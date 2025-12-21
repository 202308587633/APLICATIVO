import tkinter as tk
from tkinter import ttk

class InterfaceGrafica:
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        
        # Configurações da Janela
        self.root.title("Buscador Acadêmico RAG")
        self.root.geometry("1100x750")

        self._criar_widgets()
        self._configurar_tags()

    def _criar_widgets(self):
        # Título
        tk.Label(self.root, text="Buscador BDTD - Doutorado", font=("Arial", 14, "bold")).pack(pady=10)

        # Container para Botões
        frame_botoes = tk.Frame(self.root)
        frame_botoes.pack(pady=5)

        self.btn_buscar = tk.Button(frame_botoes, text="Iniciar Pesquisa Múltipla", 
                                   command=self.controller.disparar_busca, 
                                   bg="#2ecc71", fg="white", font=("Arial", 10, "bold"), padx=20)
        self.btn_buscar.pack(side="left", padx=5)

        self.btn_carregar = tk.Button(frame_botoes, text="Carregar Dados Salvos", 
                                     command=self.controller.carregar_do_banco,
                                     bg="#3498db", fg="white", font=("Arial", 10, "bold"), padx=20)
        self.btn_carregar.pack(side="left", padx=5)

        # Status
        self.lbl_status = tk.Label(self.root, text="Pronto para iniciar.", font=("Arial", 9, "italic"), fg="gray")
        self.lbl_status.pack(pady=5)

        # Tabela (Treeview)
        frame_tree = tk.Frame(self.root)
        frame_tree.pack(fill="both", expand=True, padx=10, pady=5)

        self.colunas = ("ID", "Título", "Autor", "IES", "Programa", "Classe", "Ação", "Link")
        self.tree = ttk.Treeview(frame_tree, columns=self.colunas, show='headings')
        
        # Configuração das colunas
        larguras = {"ID": 40, "Título": 300, "Autor": 150, "IES": 100, "Programa": 150, "Classe": 100, "Ação": 120, "Link": 0}
        for col in self.colunas:
            self.tree.heading(col, text=col, command=lambda c=col: self.controller.ordenar_coluna(c, False))
            self.tree.column(col, width=larguras.get(col, 100), anchor="w" if col=="Título" else "center")
        
        self.tree.column("Link", width=0, stretch=tk.NO) # Oculto

        # Scrollbar
        scroll = ttk.Scrollbar(frame_tree, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # Eventos
        self.tree.bind("<ButtonRelease-1>", self.controller.clique_na_tabela)
        self.tree.bind("<Double-1>", self.controller.abrir_link)

        # Painel de Detalhes (Retrátil)
        self.frame_detalhes = tk.LabelFrame(self.root, text="Detalhes e Resumo", font=("Arial", 10, "bold"))
        self.txt_resumo = tk.Text(self.frame_detalhes, wrap="word", height=8, font=("Arial", 10), state="disabled")
        self.txt_resumo.pack(fill="both", expand=True, padx=5, pady=5)
        tk.Button(self.frame_detalhes, text="Fechar Painel", command=self.ocultar_detalhes).pack(anchor="e")

    def _configurar_tags(self):
        self.tree.tag_configure('juridico', background='#d1e7dd')
        self.tree.tag_configure('nao_juridico', background='#f8d7da')

    def exibir_resumo(self, texto):
        self.frame_detalhes.pack(fill="x", side="bottom", padx=10, pady=5)
        self.txt_resumo.config(state="normal")
        self.txt_resumo.delete("1.0", tk.END)
        self.txt_resumo.insert(tk.END, texto)
        self.txt_resumo.config(state="disabled")

    def ocultar_detalhes(self):
        self.frame_detalhes.pack_forget()