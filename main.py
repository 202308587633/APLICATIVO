from database import *
from interface import InterfaceGrafica
import leitor_de_paginas
import leitor_sucupira
import tkinter as tk
from tkinter import messagebox, simpledialog
import threading
import urllib.parse 
import webbrowser

class AppController:
    def __init__(self):
        self.root = tk.Tk()
        # Inicializa a View passando este Controller para os comandos
        self.view = InterfaceGrafica(self.root, self)
        
        # Menu de contexto
        self.menu_contexto = tk.Menu(self.root, tearoff=0)
        self.menu_contexto.add_command(label="📄 Abrir PDF", command=self.abrir_pdf_selecionado)
        self.menu_contexto.add_command(label="🌐 Abrir no Navegador", command=self.abrir_link_navegador)
        self.menu_contexto.add_separator()
        self.menu_contexto.add_command(label="🗑 Apagar Detalhes (Reset)", command=self.limpar_detalhes)

        # Binds de eventos
        self.view.tree.bind("<ButtonRelease-1>", self.clique_na_tabela)
        self.view.tree.bind("<Button-3>", self.mostrar_menu_contexto)
        
        # Carregamento inicial de dados
        self.carregar_do_banco()

    def validar_estado_botoes(self):
        """Ativa os botões apenas quando um ano válido é selecionado."""
        ano = self.view.ano_selecionado_var.get()
        if ano in self.view.anos:
            self.view.btn_buscar.config(state="normal")
            self.view.btn_sucupira.config(state="normal")
            self.view.lbl_status.config(text=f"Pronto para pesquisar o ano {ano}.", fg="green")
        else:
            self.view.btn_buscar.config(state="disabled")
            self.view.btn_sucupira.config(state="disabled")

    def carregar_do_banco(self):
        """Atualiza os dados na Treeview preservando a ordem atual."""
        dados_salvos = recuperar_todos()
        
        # Se a tabela estiver vazia, faz o carregamento inicial completo
        if not self.view.tree.get_children():
            self._recarregar_completo(dados_salvos)
            return

        # Se já houver dados, atualiza as linhas existentes para manter a ordem
        mapa_dados = {d['link']: d for d in dados_salvos}
        for item_id in self.view.tree.get_children():
            valores_atuais = self.view.tree.item(item_id, "values")
            link_item = valores_atuais[7]
            
            if link_item in mapa_dados:
                d = mapa_dados[link_item]
                classe = str(d['classificacao']).lower() if d['classificacao'] else ""
                tag = 'juridico' if "jurídico" in classe else 'nao_juridico' if "não" in classe else 'pendente'
                
                self.view.tree.item(item_id, values=(
                    d['id'], d['titulo'], d['autor'], d['universidade'], 
                    d['programa'], d['classificacao'], "🔍 Ler Resumo", d['link']
                ), tags=(tag,))

    def _recarregar_completo(self, dados):
        """Método auxiliar para preencher a tabela do zero."""
        for d in dados:
            classe = str(d['classificacao']).lower() if d['classificacao'] else ""
            tag = 'juridico' if "jurídico" in classe else 'nao_juridico' if "não" in classe else 'pendente'
            self.view.tree.insert("", "end", values=(
                d['id'], d['titulo'], d['autor'], d['universidade'], 
                d['programa'], d['classificacao'], "🔍 Ler Resumo", d['link']
            ), tags=(tag,))

    def disparar_busca(self):
        """
        Orquestra a pesquisa múltipla baseada no ano selecionado 
        e nas palavras-chave marcadas na interface.
        """
        # 1. Validação do Ano de Referência
        ano = self.view.ano_selecionado_var.get()
        if ano not in self.view.anos:
            messagebox.showwarning("Aviso", "Selecione um ano de referência obrigatório antes de buscar.")
            return

        # 2. Coleta dos temas marcados na interface (View)
        termos_selecionados = [
            termo for termo, var in self.view.vars_keywords.items() 
            if var.get()
        ]
        
        if not termos_selecionados:
            messagebox.showwarning("Aviso", "Selecione ao menos um tema (palavra-chave) para realizar a pesquisa.")
            return

        # 3. Preparação da Interface (Bloqueio de botões e limpeza)
        self.view.btn_buscar.config(state="disabled")
        self.view.btn_sucupira.config(state="disabled")
        self.view.lbl_status.config(text=f"Iniciando busca múltipla para {ano}...", fg="blue")
        
        # Limpa a tabela para receber os novos resultados desta rodada
        self.view.tree.delete(*self.view.tree.get_children())

        # 4. Montagem Dinâmica das URLs
        # O loop percorre cada termo selecionado e cria uma URL específica para o BDTD
        urls_para_processar = []
        for termo in termos_selecionados:
            # Aspas duplas ao redor do termo para busca exata e quote para caracteres especiais
            termo_formatado = urllib.parse.quote(f'"{termo}"')
            
            url = (
                f"https://bdtd.ibict.br/vufind/Search/Results?"
                f"lookfor={termo_formatado}&type=AllFields&"
                f"filter%5B%5D=publishDate%3A%22%5B{ano}+TO+{ano}%5D%22"
            )
            urls_para_processar.append(url)

        # 5. Disparo da Thread de Processamento
        # Passamos a lista de URLs e o ano para a tarefa de segundo plano
        threading.Thread(
            target=self._task_busca, 
            args=(urls_para_processar,), 
            daemon=True
        ).start()
    
    def _task_busca(self, urls):
        """Thread que executa a raspagem recursiva do BDTD enviando o callback de status."""
        todos_os_resultados = []
        try:
            total_urls = len(urls)
            for i, url in enumerate(urls):
                # Criamos a função de callback que o leitor_de_paginas vai chamar
                def atualizar_status_view(msg):
                    # O status agora mostra o progresso das URLs e a mensagem do scraper
                    texto = f"[Busca {i+1}/{total_urls}] {msg}"
                    self.root.after(0, lambda t=texto: self.view.lbl_status.config(text=t, fg="blue"))
                
                # ENVIANDO O ARGUMENTO QUE ESTAVA FALTANDO: callback_status
                resultados = leitor_de_paginas.realizar_busca_recursiva(url, callback_status=atualizar_status_view)
                todos_os_resultados.extend(resultados)

            # Salva resultados básicos no SQLite
            novos = salvar_resultados(todos_os_resultados)
            
            # Atualiza interface
            self.root.after(0, self.carregar_do_banco)
            self.root.after(0, lambda: messagebox.showinfo("Busca Concluída", f"Foram encontrados {len(todos_os_resultados)} itens ({novos} novos)."))
        
        except Exception as e:
            self.root.after(0, lambda err=str(e): messagebox.showerror("Erro na Busca", f"Falha: {err}"))
        finally:
            self.root.after(0, lambda: self.view.btn_buscar.config(state="normal"))
    
    def clique_na_tabela(self, event):
        region = self.view.tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.view.tree.identify_column(event.x)
            item_id = self.view.tree.identify_row(event.y)
            
            if column == "#7":
                valores = self.view.tree.item(item_id, "values")
                link = valores[7]
                dados = buscar_trabalho_por_link(link)
                
                if dados and dados.get("resumo"):
                    info = f"IES: {dados['universidade']}\nPROG: {dados['programa']}\n{'-'*30}\n{dados['resumo']}"
                    self.view.exibir_resumo(info)
                else:
                    self.view.lbl_status.config(text="Extraindo detalhes via Selenium...", fg="orange")
                    threading.Thread(target=self._task_scrap_detalhado, args=(link,), daemon=True).start()

    def _task_scrap_detalhado(self, url):
        try:
            res = leitor_de_paginas.ler_detalhes_trabalho(url)
            salvar_detalhes_completos(url, res["resumo"], res["programa"], res["universidade"], res["classificacao"], res["link_pdf"])
            info = f"IES: {res['universidade']}\nPDF: {res['link_pdf']}\n{'-'*30}\n{res['resumo']}"
            self.root.after(0, lambda: self.view.exibir_resumo(info))
            self.root.after(0, self.carregar_do_banco)
        except Exception as e:
            self.root.after(0, lambda err=str(e): messagebox.showerror("Erro", err))

    def ordenar_coluna(self, col, reverse):
        l = [(self.view.tree.set(k, col), k) for k in self.view.tree.get_children('')]
        try:
            if col == "ID": l.sort(key=lambda t: int(t[0]), reverse=reverse)
            else: l.sort(key=lambda t: t[0].lower(), reverse=reverse)
        except: l.sort(reverse=reverse)

        for index, (val, k) in enumerate(l):
            self.view.tree.move(k, '', index)
        self.view.tree.heading(col, command=lambda: self.ordenar_coluna(col, not reverse))

    def abrir_pdf_selecionado(self):
        sel = self.view.tree.selection()
        if sel:
            link = self.view.tree.item(sel[0], "values")[7]
            dados = buscar_trabalho_por_link(link)
            if dados and dados.get("link_pdf") and "http" in dados["link_pdf"]:
                webbrowser.open(dados["link_pdf"])

    def abrir_link_navegador(self, event=None):
        sel = self.view.tree.selection()
        if sel:
            link = self.view.tree.item(sel[0], "values")[7]
            webbrowser.open(link)

    def mostrar_menu_contexto(self, event):
        item = self.view.tree.identify_row(event.y)
        if item:
            self.view.tree.selection_set(item)
            self.menu_contexto.post(event.x_root, event.y_root)

    def solicitar_busca_sucupira(self):
        ano = self.view.combo_ano.get()
        sigla = simpledialog.askstring("Sucupira", "Sigla da Universidade:")
        if sigla:
            threading.Thread(target=self._task_sucupira, args=(sigla, ano), daemon=True).start()

    def _task_sucupira(self, sigla, ano):
        id_s = leitor_sucupira.buscar_id_instituicao(sigla)
        if id_s:
            salvar_id_sucupira(sigla, id_s, ano)
            self.root.after(0, lambda: messagebox.showinfo("Sucesso", f"ID {id_s} salvo para {sigla}."))

    def limpar_detalhes(self):
        """Ação disparada pelo menu de contexto para resetar os dados de um trabalho."""
        item_selecionado = self.view.tree.selection()
        if not item_selecionado:
            return
        
        # Pega os valores da linha (ID está no índice 0)
        valores = self.view.tree.item(item_selecionado[0], "values")
        id_trabalho = valores[0]
        titulo = valores[1]
        
        pergunta = f"Deseja apagar os detalhes extraídos de:\n'{titulo[:50]}...'?"
        if messagebox.askyesno("Confirmar Reset", pergunta):
            try:
                # 1. Chama a função do arquivo database.py
                limpar_detalhes_trabalho(id_trabalho)
                
                # 2. Notifica o status
                self.view.lbl_status.config(text=f"Dados do ID {id_trabalho} resetados.", fg="blue")
                
                # 3. Fecha o painel de resumo se estiver aberto
                self.view.ocultar_detalhes()
                
                # 4. Atualiza a tabela para voltar a cor para Branco (pendente)
                self.carregar_do_banco()
                
            except Exception as e:
                messagebox.showerror("Erro ao apagar", f"Falha no banco de dados: {e}")

    def iniciar(self):
        self.root.mainloop()

if __name__ == "__main__":
    inicializar_banco()
    AppController().iniciar()