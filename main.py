import webbrowser
import database 
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import leitor_de_paginas
import importlib 

class AppPesquisa:
    def __init__(self, root):
        importlib.reload(leitor_de_paginas)
        self.root = root
        self.root.title("Buscador Acadêmico RAG")
        self.root.geometry("1000x600")

        # --- Lista de URLs (Mantenha as suas aqui) ---
        self.lista_de_urls = [
            "https://bdtd.ibict.br/vufind/Search/Results?join=AND&bool0%5B%5D=AND&lookfor0%5B%5D=%22an%C3%A1lise+de+discurso%22&type0%5B%5D=AllFields&lookfor0%5B%5D=direito&type0%5B%5D=AllFields&illustration=-1&daterange%5B%5D=publishDate&publishDatefrom=2021&publishDateto=2021",
            "https://bdtd.ibict.br/vufind/Search/Results?join=AND&bool0%5B%5D=AND&lookfor0%5B%5D=%22algoritmo%22&type0%5B%5D=AllFields&lookfor0%5B%5D=direito&type0%5B%5D=AllFields&illustration=-1&daterange%5B%5D=publishDate&publishDatefrom=2021&publishDateto=2021"
        ]

        # --- Título ---
        tk.Label(root, text="Buscador BDTD - Doutorado", font=("Arial", 14, "bold")).pack(pady=10)

        # --- Container para Botões ---
        frame_botoes = tk.Frame(root)
        frame_botoes.pack(pady=5)

        self.btn_buscar = tk.Button(frame_botoes, text="Iniciar Pesquisa Múltipla", command=self.disparar_busca, 
                                   bg="#2ecc71", fg="white", font=("Arial", 10, "bold"), padx=20)
        self.btn_buscar.pack(side="left", padx=5)

        self.btn_carregar = tk.Button(frame_botoes, text="Carregar Dados Salvos", command=self.carregar_do_banco,
                                     bg="#3498db", fg="white", font=("Arial", 10, "bold"), padx=20)
        self.btn_carregar.pack(side="left", padx=5)

        # --- Status ---
        self.lbl_status = tk.Label(root, text="Pronto para iniciar.", font=("Arial", 9, "italic"), fg="gray")
        self.lbl_status.pack(pady=5)

        # --- Frame da Tabela ---
        frame_tabela = tk.Frame(root)
        frame_tabela.pack(fill="both", expand=True, padx=10, pady=10)

        # Configuração da Treeview (4 COLUNAS DEFINIDAS)
        self.tree = ttk.Treeview(frame_tabela, columns=("Título", "Autor", "Ação", "Link"), show='headings')
        
        self.tree.heading("Título", text="Título")
        self.tree.heading("Autor", text="Autor")
        self.tree.heading("Ação", text="Extrair Detalhes")
        self.tree.heading("Link", text="Link") # Heading necessário para evitar erros internos
        
        self.tree.column("Título", width=400, anchor="w")
        self.tree.column("Autor", width=200, anchor="w")
        self.tree.column("Ação", width=120, anchor="center")
        self.tree.column("Link", width=0, stretch=tk.NO) # TOTALMENTE OCULTA

        scrollbar = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set, cursor="hand2")

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- Vínculo de Eventos ---
        self.tree.bind("<ButtonRelease-1>", self.clique_na_tabela)
        self.tree.bind("<Double-1>", self.abrir_link)
        
        # No __init__ do AppPesquisa, abaixo da Treeview:
        self.frame_detalhes = tk.LabelFrame(root, text="Detalhes e Resumo", font=("Arial", 10, "bold"))
        # Não daremos pack() nele ainda para ele ficar "escondido"

        self.txt_resumo = tk.Text(self.frame_detalhes, wrap="word", height=8, font=("Arial", 10))
        self.txt_resumo.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Botão para fechar o painel (tornar retrátil)
        tk.Button(self.frame_detalhes, text="Fechar Painel", command=self.ocultar_detalhes).pack(anchor="e")

        database.conectar()

    def ocultar_detalhes(self):
        self.frame_detalhes.pack_forget()

    def exibir_detalhes(self, texto):
        self.frame_detalhes.pack(fill="x", side="bottom", padx=10, pady=5)
        self.txt_resumo.delete("1.0", tk.END)
        self.txt_resumo.insert(tk.END, texto)

    def disparar_busca(self):
        self.btn_buscar.config(state="disabled")
        for item in self.tree.get_children(): self.tree.delete(item)
        threading.Thread(target=self.processar_em_segundo_plano, daemon=True).start()

    def processar_em_segundo_plano(self):
        todos_os_resultados_finais = []
        try:
            total_urls = len(self.lista_de_urls)
            for i, url in enumerate(self.lista_de_urls):
                def atualizar_status_view(msg):
                    self.root.after(0, lambda: self.lbl_status.config(
                        text=f"[Busca {i+1}/{total_urls}] {msg}", fg="blue"))

                resultados_da_url = leitor_de_paginas.realizar_busca_recursiva(url, atualizar_status_view)
                todos_os_resultados_finais.extend(resultados_da_url)

            # Salvar no SQLite
            novos = database.salvar_resultados(todos_os_resultados_finais)
            
            # Atualizar interface (Passando os dados e a contagem de novos)
            self.root.after(0, self.atualizar_tabela, todos_os_resultados_finais, novos)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Erro Crítico", f"Erro: {e}"))
            self.root.after(0, lambda: self.btn_buscar.config(state="normal"))

    def atualizar_tabela(self, dados, novos_count=0):
        """Limpa e preenche a tabela com 4 valores por linha."""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for d in dados:
            # INSERÇÃO CORRETA: Título[0], Autor[1], Texto Ação[2], Link[3]
            self.tree.insert("", "end", values=(d["Título"], d["Autor"], "🔍 Ler Resumo", d["Link"]))

        self.lbl_status.config(
            text=f"Concluído! {len(dados)} exibidos. {novos_count} novos salvos.", 
            fg="green"
        )
        self.btn_buscar.config(state="normal")

    def carregar_do_banco(self):
        """Carrega do banco e reconstrói as 4 colunas necessárias."""
        dados_salvos = database.recuperar_todos()
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for d in dados_salvos:
            # d[0]=Título, d[1]=Autor, d[2]=Link (conforme database.py)
            # Adicionamos "🔍 Ler Resumo" no índice [2] para manter a estrutura
            self.tree.insert("", "end", values=(d[0], d[1], "🔍 Ler Resumo", d[2]))
            
        self.lbl_status.config(text=f"Exibindo {len(dados_salvos)} trabalhos salvos.", fg="purple")

    def abrir_link(self, event):
        item_selecionado = self.tree.selection()
        if item_selecionado:
            valores = self.tree.item(item_selecionado, "values")
            # Link agora está no índice [3]
            if len(valores) >= 4:
                link = valores[3]
                if link and link != "N/A":
                    webbrowser.open(link)

    def clique_na_tabela(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            item_id = self.tree.identify_row(event.y)
            
            if column == "#3": # Coluna "Extrair Detalhes"
                valores = self.tree.item(item_id, "values")
                link = valores[3]
                titulo = valores[0]
                
                # --- LÓGICA DE RECUPERAÇÃO INTELIGENTE ---
                dados_existentes = database.buscar_trabalho_por_link(link)
                
                # Verificamos se o resumo (coluna de índice 8 no SELECT *) não é nulo/vazio
                if dados_existentes and dados_existentes["resumo"]: 
                    info_banco = (
                        f"INSTITUIÇÃO: {dados_existentes['universidade']}\n"
                        f"PROGRAMA: {dados_existentes['programa']}\n"
                        f"CLASSIFICAÇÃO: {dados_existentes['classificacao']}\n"
                        f"{'-'*50}\n"
                        f"RESUMO (RECUPERADO DO BANCO):\n{dados_existentes['resumo']}"
                    )
                    self.exibir_resumo(info_banco)
                    self.lbl_status.config(text="Dados recuperados do banco local.", fg="purple")
                
                else:
                    # Se não existe no banco, aí sim usamos o Selenium
                    self.lbl_status.config(text=f"Fazendo scrap: {titulo[:30]}...", fg="orange")
                    threading.Thread(target=self.scrap_detalhado, args=(link,), daemon=True).start()

    def scrap_detalhado(self, url):
        try:
            # 1. Faz o scrap (Motor que você já tem)
            res = leitor_de_paginas.ler_detalhes_trabalho(url)
            
            # 2. Armazena no Banco de Dados
            database.salvar_detalhes_completos(
                url, res["resumo"], res["programa"], res["universidade"], res["classificacao"]
            )

            # 3. Formata o texto para a célula retrátil
            texto_exibicao = (
                f"UNIVERSIDADE: {res['universidade']}\n"
                f"PROGRAMA: {res['programa']}\n"
                f"CLASSIFICAÇÃO: {res['classificacao']}\n"
                f"{'-'*50}\n"
                f"RESUMO: {res['resumo']}"
            )

            # 4. Atualiza a interface (Painel Retrátil)
            self.root.after(0, lambda: self.exibir_detalhes(texto_exibicao))
            self.root.after(0, lambda: self.lbl_status.config(text="Resumo carregado e salvo.", fg="green"))

        except Exception as e:
            erro_msg = str(e)
            self.root.after(0, lambda err=erro_msg: messagebox.showerror("Erro", f"Falha: {err}"))

    def exibir_resumo(self, texto):
        self.frame_detalhes.pack(fill="x", padx=10, pady=5)
        self.txt_resumo.config(state="normal") # Habilita para escrita
        self.txt_resumo.delete("1.0", tk.END)
        self.txt_resumo.insert(tk.END, texto)
        self.txt_resumo.see("1.0") # Volta para o início do texto
        self.txt_resumo.config(state="disabled") # Bloqueia edição

if __name__ == "__main__":
    root = tk.Tk()
    app = AppPesquisa(root)
    root.mainloop()