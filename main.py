from config_agregadores import CONFIG_AGREGADORES
import database
from interface import InterfaceGrafica
import leitor_de_paginas
import threading
import webbrowser
from tkinter import messagebox
import tkinter as tk
import urllib.parse
from url_factory import gerar_url_por_fonte 
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

        url = gerar_url_por_fonte(fonte, ano, termo_inc, termos_exc, self.view.fontes_disponiveis)

        self.view.btn_buscar.config(state="disabled")
        self.view.lbl_status.config(text=f"Pesquisando em {fonte}...", fg="blue")
        threading.Thread(target=self._executar_tarefa_busca, args=(url,), daemon=True).start()
    
    def _executar_tarefa_busca(self, url):
        """Tarefa executada em Thread para não travar a interface."""
        try:
            # 1. Recolha de metadados da interface
            fonte = self.view.fonte_selecionada_var.get()
            ano = self.view.ano_selecionado_var.get()
            termo = self.view.var_inc_unica.get()
            
            meta_dados = {
                'ano': ano,
                'termo': termo,
                'agregador': fonte
            }

            config_site = CONFIG_AGREGADORES.get(fonte)

            def atualizar_gui(msg):
                self.root.after(0, lambda: self.view.lbl_status.config(text=msg))

            # 2. Passagem dos metadados para a função agnóstica
            resultados = leitor_de_paginas.realizar_busca_recursiva(
                url, config_site, meta_dados, atualizar_gui
            )
            
            # 3. Salva no banco (garante que a função salvar_resultados trate os novos campos)
            novos = database.salvar_resultados(resultados)
            
            self.root.after(0, self.carregar_do_banco)
            self.root.after(0, lambda: messagebox.showinfo("Sucesso", f"Coletados {len(resultados)} itens."))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Erro", str(e)))
    
    def carregar_do_banco(self):
        """Lê os dados do SQLite e popula a Treeview."""
        dados = database.recuperar_todos()
        self.view.tree.delete(*self.view.tree.get_children())
        
        for d in dados:
            # Lógica de cores baseada na classificação
            classif = str(d.get('classificacao', '') or '')
            tag = 'juridico' if "Jurídico" in classif else 'nao_juridico'
            
            self.view.tree.insert("", "end", values=(
                d['id'], 
                d['titulo'], 
                d['autor'], 
                d.get('ano', '-'),       
                d.get('termo', '-'),     
                d.get('agregador', '-'), 
                "🔍 Detalhes", 
                d['link']
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
        """Executa Selenium em segundo plano para capturar o resumo e metadados."""
        try:
            res = leitor_de_paginas.ler_detalhes_trabalho(link)
            
            # Persistência no banco
            database.salvar_detalhes_completos(
                link,
                res['resumo'],
                res['programa'],
                res['universidade'],
                res['classificacao'],
                res['link_pdf']
            )
            
            # Montagem da string formatada para a UI
            info_painel = (
                f"UNIVERSIDADE: {res['universidade']}\n"
                f"PROGRAMA: {res['programa']}\n"
                f"PDF: {res['link_pdf']}\n"
                f"{'-'*40}\n"
                f"RESUMO: {res['resumo']}"
            )

            # Atualizações da Interface (Thread Safe)
            self.root.after(0, self.carregar_do_banco)
            # Mantemos apenas a chamada com a informação completa:
            self.root.after(0, lambda: self.view.exibir_resumo(info_painel))
            self.root.after(0, lambda: self.view.lbl_status.config(
                text="Detalhes extraídos com sucesso!", fg="green"
            ))

        except Exception as e:
            self.root.after(0, lambda: self.view.lbl_status.config(
                text="Erro ao extrair detalhes.", fg="red"
            ))
            self.root.after(0, lambda: messagebox.showerror(
                "Erro no Scrap Detalhado", f"Falha ao processar {link}:\n{str(e)}"
            ))    
    
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

    def abrir_link(self, event=None): # Adicionado event=None para ser opcional
        """Abre o link da linha selecionada. Funciona para duplo clique ou menu."""
        selecao = self.view.tree.selection()
        if selecao:
            link = self.view.tree.item(selecao[0], "values")[7]
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

    def abrir_link_contexto(self):
        self.abrir_link()

    def extrair_detalhes_contexto(self):
        selecao = self.view.tree.selection()
        if selecao:
            link = self.view.tree.item(selecao[0], "values")[7]
            self._gerenciar_detalhes(link)

    def limpar_detalhes_contexto(self):
        """Apaga os metadados (Uni, Programa, Resumo, PDF) da linha selecionada."""
        selecao = self.view.tree.selection()
        if not selecao:
            return

        # Obtém os valores da linha (o ID está no índice 0)
        valores = self.view.tree.item(selecao[0], "values")
        id_trabalho = valores[0]
        titulo = valores[1]

        # Confirmação com o usuário
        pergunta = messagebox.askyesno("Confirmar Reset", 
            f"Deseja apagar os detalhes extraídos de:\n'{titulo}'?")
        
        if pergunta:
            try:
                # Chama a função existente no seu database.py
                database.limpar_detalhes_trabalho(id_trabalho)
                
                # Atualiza a tabela para refletir as mudanças
                self.carregar_do_banco()
                
                # Se o painel de resumo estiver aberto, limpa o texto
                self.view.exibir_resumo("") 
                self.view.ocultar_detalhes()
                
                self.view.lbl_status.config(text="Detalhes removidos com sucesso.", fg="blue")
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível limpar os dados: {e}")

    def iniciar(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = AppController()
    app.iniciar()