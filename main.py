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
        self.view.tree.bind("<ButtonRelease-1>", self.clique_na_tabela)

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
        try:
            fonte = self.view.fonte_selecionada_var.get()
            ano = self.view.ano_selecionado_var.get()
            termo = self.view.var_inc_unica.get()
        
            meta_dados = {'ano': ano, 'termo': termo, 'agregador': fonte}

            def atualizar_gui(msg):
                self.root.after(0, lambda: self.view.lbl_status.config(text=msg, fg="blue"))

            # O leitor agora já retorna a lista com link_universidade preenchido
            resultados = leitor_de_paginas.coletar_dados_por_agregador(
                url, fonte, meta_dados, atualizar_gui
            )

            if resultados:
                novos = database.salvar_resultados(resultados)
                self.root.after(0, self.carregar_do_banco)
                atualizar_gui(f"Busca finalizada! {novos} novos itens salvos.")
            else:
                atualizar_gui("Nenhum resultado encontrado.")

            self.root.after(0, lambda: self.view.btn_buscar.config(state="normal"))

        except Exception as e:
            # Capturamos a mensagem como string imediatamente
            msg_erro = str(e) 
            self.root.after(0, lambda m=msg_erro: self.view.lbl_status.config(text=f"Erro: {m}", fg="red"))
            self.root.after(0, lambda m=msg_erro: messagebox.showerror("Erro na busca", m))    
            
    def carregar_do_banco(self):
        dados = database.recuperar_todos()
        self.view.tree.delete(*self.view.tree.get_children())
        
        for d in dados:
            classif = str(d.get('classificacao', '') or '')
            tag = 'juridico' if "Jurídico" in classif else 'nao_juridico'
            
            self.view.tree.insert("", "end", values=(
                d['id'], 
                d['titulo'], 
                d['autor'], 
                d.get('universidade', '-'), 
                d.get('programa', '-'), 
                d.get('classificacao', '-'),
                d['ano'], 
                d['termo'], 
                d['agregador'],
                d.get('link_universidade', 'N/A'), # Coluna 10 (índice 9)
                "🔍 Detalhes",                   # Coluna 11 (índice 10)
                d['link']                        # Coluna 12 (índice 11)
            ))

    def clique_na_tabela(self, event):
        region = self.view.tree.identify_region(event.x, event.y)
        if region == "cell":
            col = self.view.tree.identify_column(event.x)
            item_id = self.view.tree.identify_row(event.y)
            if col == "#11":  # Coluna Detalhes
                valores = self.view.tree.item(item_id, "values")
                id_db = valores[0]    # ID no SQLite
                link_uni = valores[9] # Link da Universidade
                
                if link_uni and link_uni != "N/A":
                    # Inicia o scrap passando o ID para gravação posterior
                    self.view.lbl_status.config(text="⏳ A preparar navegação...", fg="orange")
                    threading.Thread(target=self._task_scrap_detalhado, args=(link_uni, id_db), daemon=True).start()
                
                
    def _gerenciar_detalhes(self, link, id_db):
        dados = database.buscar_trabalho_por_link(link) # Ou por ID
        
        if dados and dados.get('resumo'):
            info = f"UNIVERSIDADE: {dados['universidade']}\nRESUMO: {dados['resumo']}"
            self.view.exibir_resumo(info)
        else:
            self.view.lbl_status.config(text=f"⏳ Iniciando scrap em: {link[:40]}...", fg="orange")
            threading.Thread(target=self._task_scrap_detalhado, args=(link, id_db), daemon=True).start()
          
    def _task_scrap_detalhado(self, link, id_db):
        try:
            # Função interna para atualizar a UI a partir da Thread
            def reportar_progresso(msg):
                self.root.after(0, lambda: self.view.lbl_status.config(text=msg, fg="orange"))

            # 1. Realiza o scrap (leitor_de_paginas precisa aceitar o callback)
            res = leitor_de_paginas.ler_detalhes_trabalho(link, reportar_progresso)
            
            # 2. Grava no banco de dados usando o ID
            database.salvar_detalhes_por_id(id_db, res['resumo'], res['programa'], 
                                            res['universidade'], res['classificacao'], res['link_pdf'])
            
            # 3. Atualiza a Interface
            self.root.after(0, self.carregar_do_banco)
            self.root.after(0, lambda: self.view.exibir_resumo(f"UNI: {res['universidade']}\n{res['resumo']}"))
            self.root.after(0, lambda: self.view.lbl_status.config(text="✅ Detalhes atualizados!", fg="green"))
        except Exception as e:
            self.root.after(0, lambda: self.view.lbl_status.config(text=f"❌ Erro: {str(e)}", fg="red"))
                
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
            link = self.view.tree.item(selecao[0], "values")[11]
            if link and link != "N/A":
                webbrowser.open(link)

# No AppController:

    def abrir_link_agregador(self, event):
        """Ação do Duplo Clique: Abre a página do agregador (ex: BDTD)."""
        selecao = self.view.tree.selection()
        if selecao:
            item_id = selecao[0]
            valores = self.view.tree.item(item_id, "values")
            
            # Busca o índice dinamicamente (coluna oculta 'Link')
            idx_link_agregador = self.view.colunas.index("Link")
            url = valores[idx_link_agregador]
            
            if url and url != "N/A":
                webbrowser.open(url)

    def abrir_link_universidade(self):
        """Ação do Menu de Contexto: Abre a URL direta da universidade."""
        selecao = self.view.tree.selection()
        if selecao:
            item_id = selecao[0]
            valores = self.view.tree.item(item_id, "values")
            
            # Busca o índice dinamicamente (coluna 'Link Uni')
            idx_link_uni = self.view.colunas.index("Link Uni")
            url_uni = valores[idx_link_uni]
            
            if url_uni and url_uni != "N/A":
                webbrowser.open(url_uni)
            else:
                messagebox.showinfo("Informação", "Link da universidade não disponível para este item.")

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
            # Índice 9 é o 'Link Uni' na sua configuração da treeview
            link_universidade = self.view.tree.item(selecao[0], "values")[9]
            
            if link_universidade and link_universidade != "N/A":
                # O ID é necessário para atualizar o banco corretamente depois
                id_trabalho = self.view.tree.item(selecao[0], "values")[0]
                self._gerenciar_detalhes(link_universidade, id_trabalho)
            else:
                messagebox.showwarning("Aviso", "Este item não possui link de universidade para scrap.")

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