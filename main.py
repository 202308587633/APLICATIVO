from config_agregadores import CONFIG_AGREGADORES
import database
from interface import InterfaceGrafica
import leitor_de_paginas
import threading
import webbrowser
from tkinter import messagebox
import tkinter as tk
import urllib.parse

class AppController:
    def __init__(self):
        self.root = tk.Tk()
        # Inicializa a View passando o controlador
        self.view = InterfaceGrafica(self.root, self)
        
        # Inicialização de dados e banco
        database.inicializar_banco()
        self.carregar_do_banco()

    def disparar_busca(self):
        """Orquestra o início da busca em segundo plano."""
        fonte = self.view.fonte_selecionada_var.get()
        ano = self.view.ano_selecionado_var.get()
        termo_inc = self.view.var_inc_unica.get()
        termos_exc = [t for t, v in self.view.vars_exc.items() if v.get()]

        # Validação extra de segurança
        if termo_inc == "vazio" or ano == "Selecione":
            messagebox.showwarning("Aviso", "Preencha todos os filtros antes de buscar.")
            return

        url = self._gerar_url_por_fonte(fonte, ano, termo_inc, termos_exc)

        # Atualiza UI para estado de carregamento
        self.view.btn_buscar.config(state="disabled")
        self.view.lbl_status.config(text=f"Pesquisando em {fonte}...", fg="blue")
        
        # Inicia a thread de busca
        threading.Thread(target=self._executar_tarefa_busca, args=(url,), daemon=True).start()

    def _gerar_url_por_fonte(self, fonte, ano, inc, exc):
        """Fábrica de URLs para diferentes bases acadêmicas (Sintaxe específica)."""
        # Montagem da query: "Inclusao" -"Exclusao1" -"Exclusao2"
        query = f'"{inc}"'
        if exc:
            query += " " + " ".join([f'-"{t}"' for t in exc])
        
        query_encoded = urllib.parse.quote(query)

        # Seleção da URL baseada na fonte
        if "BDTD" in fonte:
            return (f"https://bdtd.ibict.br/vufind/Search/Results?"
                    f"lookfor={query_encoded}&type=AllFields&"
                    f"filter%5B%5D=publishDate%3A%22%5B{ano}+TO+{ano}%5D%22")
        
        elif "SciELO" in fonte:
            return f"https://search.scielo.org/?q={query_encoded}&filter[year][]={ano}"
        
        elif "Scholar" in fonte:
            return f"https://scholar.google.com.br/scholar?q={query_encoded}+as_ylo={ano}&as_yhi={ano}"
        
        # Fallback genérico para as outras fontes cadastradas na View
        base_url = self.view.fontes_disponiveis.get(fonte, "")
        return f"{base_url}search?q={query_encoded}"

    def _executar_tarefa_busca(self, url):
        """Tarefa executada em Thread para não travar a interface."""
        try:
            # O robô de busca retorna uma lista de dicionários
            fonte = self.view.fonte_selecionada_var.get()
            config_site = CONFIG_AGREGADORES.get(fonte)

            def atualizar_gui(msg):
                self.root.after(0, lambda: self.view.lbl_status.config(text=msg))

            # A função agora é chamada com o parâmetro de configuração
            resultados = leitor_de_paginas.realizar_busca_recursiva(url, config_site, atualizar_gui)
            
            # Salva no SQLite (o método retorna quantos itens novos foram inseridos)
            novos_itens = database.salvar_resultados(resultados)
            
            # Atualiza a interface de volta na Main Thread
            self.root.after(0, self.carregar_do_banco)
            self.root.after(0, lambda: messagebox.showinfo(
                "Busca Concluída", 
                f"Encontrados: {len(resultados)}\nNovos no banco: {novos_itens}"
            ))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Erro na Busca", f"Detalhes: {str(e)}"))
        finally:
            self.root.after(0, self.validar_estado_botoes)
    
    def carregar_do_banco(self):
        """Lê os dados do SQLite e popula a Treeview."""
        dados = database.recuperar_todos()
        self.view.tree.delete(*self.view.tree.get_children())
        
        for d in dados:
            # Lógica de cores baseada na classificação
            classif = str(d.get('classificacao', '') or '')
            tag = 'juridico' if "Jurídico" in classif else 'nao_juridico'
            
            self.view.tree.insert("", "end", values=(
                d['id'], d['titulo'], d['autor'], d['universidade'], 
                d['programa'], classif, "🔍 Ler Resumo", d['link']
            ), tags=(tag,))

    def clique_na_tabela(self, event):
        """Detecta cliques na coluna de ação (Extrair Detalhes)."""
        region = self.view.tree.identify_region(event.x, event.y)
        if region == "cell":
            col = self.view.tree.identify_column(event.x)
            item_id = self.view.tree.identify_row(event.y)
            
            if col == "#7": # Coluna 'Ação'
                valores = self.view.tree.item(item_id, "values")
                link = valores[7]
                self._gerenciar_detalhes(link)

    def _gerenciar_detalhes(self, link):
        """Verifica se o resumo já existe ou se precisa de scrap via Selenium."""
        dados = database.buscar_trabalho_por_link(link)
        
        if dados and dados.get('resumo'):
            info = f"UNIVERSIDADE: {dados['universidade']}\nRESUMO: {dados['resumo']}"
            self.view.exibir_resumo(info)
        else:
            self.view.lbl_status.config(text="Fazendo scrap de detalhes...", fg="orange")
            threading.Thread(target=self._task_scrap_detalhado, args=(link,), daemon=True).start()

    def _task_scrap_detalhado(self, link):
        """Executa Selenium em segundo plano para capturar o resumo."""
        try:
            res = leitor_de_paginas.ler_detalhes_trabalho(link)
            database.salvar_detalhes_completos(
                link, res['resumo'], res['programa'], res['universidade'], res['classificacao']
            )
            self.root.after(0, self.carregar_do_banco)
            self.root.after(0, lambda: self.view.exibir_resumo(res['resumo']))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Erro no Scrap", str(e)))
    
    def ordenar_coluna(self, col, reverse):
        """Ordena a Treeview de forma inteligente (numérica ou alfabética)."""
        itens = [(self.view.tree.set(k, col), k) for k in self.view.tree.get_children('')]

        try:
            # Tenta ordenar como números (importante para ID)
            itens.sort(key=lambda t: float(t[0]), reverse=reverse)
        except ValueError:
            # Se falhar (texto), ordena alfabeticamente
            itens.sort(reverse=reverse)

        for index, (val, k) in enumerate(itens):
            self.view.tree.move(k, '', index)

        self.view.tree.heading(col, command=lambda: self.ordenar_coluna(col, not reverse))

    def abrir_link(self, event):
        """Abre a URL original no navegador ao dar duplo clique."""
        item = self.view.tree.selection()
        if item:
            link = self.view.tree.item(item, "values")[7]
            if link and link != "N/A":
                webbrowser.open(link)

    def validar_estado_botoes(self):
        """Habilita o botão de busca apenas se os critérios forem válidos."""
        fonte = self.view.fonte_selecionada_var.get()
        ano = self.view.ano_selecionado_var.get()
        termo = self.view.var_inc_unica.get()

        valido = (fonte != "Selecione a Fonte" and 
                  ano != "Selecione" and 
                  termo != "vazio")

        if valido:
            self.view.btn_buscar.config(state="normal", bg="#2ecc71")
            self.view.lbl_status.config(text="Pronto para pesquisar.", fg="green")
        else:
            self.view.btn_buscar.config(state="disabled", bg="#95a5a6")
            self.view.lbl_status.config(text="Selecione Fonte, Ano e Termo.", fg="red")

    def iniciar(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = AppController()
    app.iniciar()