import tkinter as tk
from tkinter import ttk

class InterfaceGrafica:
    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        self.anos = ["2020", "2021", "2022", "2023", "2024", "2025"]
        
        self._configurar_janela()
        self._criar_widgets()
        self._configurar_tags()
        self.tree.bind("<Motion>", self._mudar_cursor_link)

    def mostrar_menu_contexto(self, event):
        """Identifica a linha sob o clique direito e abre o menu do Controller."""
        # Identifica o ID da linha (row) onde o mouse clicou
        item = self.tree.identify_row(event.y)
        
        if item:
            # Seleciona a linha visualmente para o usuário
            self.tree.selection_set(item)
            self.tree.focus(item)
            
            # Pede ao menu definido no Controller para aparecer na posição do mouse
            self.controller.menu_contexto.post(event.x_root, event.y_root)

    def _configurar_janela(self):
        self.root.title("Buscador Acadêmico")
        self.root.geometry("1100x750")

    def _criar_widgets(self):
        """Constrói a interface com filtros de ano, temas de pesquisa e travas de segurança."""
        
        # --- TÍTULO ---
        tk.Label(self.root, text="Buscador Acadêmico - Jurimetria e Tecnologia", 
                 font=("Arial", 14, "bold")).pack(pady=10)

        # --- CONTAINER 1: FILTRO DE ANO ---
        frame_filtros = tk.Frame(self.root)
        frame_filtros.pack(pady=5)

        tk.Label(frame_filtros, text="Ano de Referência:", font=("Arial", 10, "bold")).pack(side="left", padx=5)

        self.ano_selecionado_var = tk.StringVar(value="Selecione")
        self.combo_ano = ttk.Combobox(
            frame_filtros, 
            values=self.anos, 
            state="readonly", 
            width=12,
            textvariable=self.ano_selecionado_var
        )
        self.combo_ano.pack(side="left", padx=5)
        
        # Monitora a mudança do ano para habilitar botões
        self.ano_selecionado_var.trace_add("write", lambda *args: self.controller.validar_estado_botoes())

        # --- CONTAINER 2: TEMAS DE PESQUISA (Palavras-Chave) ---
        frame_keywords = tk.LabelFrame(self.root, text="Palavras-Chave (Selecione os temas)", font=("Arial", 10, "bold"))
        frame_keywords.pack(pady=10, padx=20, fill="x")

        termos = [
            "Jurimetria", "Inteligência Artificial", "Análise de discurso", 
            "Algoritmo", "Direito Digital", "Tecnologia da Informação"
        ]
        
        self.vars_keywords = {}
        grid_inner = tk.Frame(frame_keywords)
        grid_inner.pack(pady=5)

        # Organiza as palavras-chave em uma grade de 3 colunas
        for i, termo in enumerate(termos):
            var = tk.BooleanVar(value=False)
            self.vars_keywords[termo] = var
            cb = tk.Checkbutton(grid_inner, text=termo, variable=var, font=("Arial", 9))
            cb.grid(row=i//3, column=i%3, sticky="w", padx=15, pady=2)

        # --- CONTAINER 3: BOTÕES DE OPERAÇÃO ---
        frame_botoes = tk.Frame(self.root)
        frame_botoes.pack(pady=10)

        self.btn_buscar = tk.Button(
            frame_botoes, text="Iniciar Pesquisa Múltipla", 
            command=self.controller.disparar_busca, 
            bg="#2ecc71", fg="white", font=("Arial", 10, "bold"), 
            padx=15, state="disabled"
        )
        self.btn_buscar.pack(side="left", padx=5)

        self.btn_carregar = tk.Button(
            frame_botoes, text="Carregar Dados Salvos", 
            command=self.controller.carregar_do_banco,
            bg="#3498db", fg="white", font=("Arial", 10, "bold"), padx=15
        )
        self.btn_carregar.pack(side="left", padx=5)

        self.btn_sucupira = tk.Button(
            frame_botoes, text="Vincular Sucupira", 
            command=self.controller.solicitar_busca_sucupira,
            bg="#f39c12", fg="white", font=("Arial", 10, "bold"), 
            padx=15, state="disabled"
        )
        self.btn_sucupira.pack(side="left", padx=5)

        # --- STATUS E TABELA ---
        self.lbl_status = tk.Label(self.root, text="Aguardando seleção do ano...", font=("Arial", 9, "italic"), fg="gray")
        self.lbl_status.pack(pady=5)

        self._criar_tabela()

        # --- CONTAINER 4: PAINEL DE RESUMO ---
        self.frame_detalhes = tk.LabelFrame(self.root, text="Detalhes e Resumo do Trabalho", font=("Arial", 10, "bold"))
        
        self.txt_resumo = tk.Text(
            self.frame_detalhes, wrap="word", height=7, 
            font=("Arial", 10), state="disabled", bg="#f9f9f9"
        )
        self.txt_resumo.pack(fill="both", expand=True, padx=5, pady=5)
        
        tk.Button(self.frame_detalhes, text="Fechar Painel", command=self.ocultar_detalhes).pack(anchor="e", padx=5, pady=2)

    def _criar_tabela(self):
        """Configura a tabela com larguras automáticas e visibilidade total."""
        # Criamos o container da tabela e a barra de rolagem
        frame_tree = tk.Frame(self.root)
        frame_tree.pack(pady=5, padx=10, fill="both", expand=True)

        # Definição das colunas (certifique-se de que os IDs batem com seu banco)
        self.colunas = ("ID", "Título", "Programa", "IES", "Classificação", "Link Detalhes")
        
        self.tree = ttk.Treeview(frame_tree, columns=self.colunas, show='headings', height=12)
        
        # --- CONFIGURAÇÃO DE LARGURA E CABEÇALHOS ---
        # Definimos pesos e larguras iniciais para evitar o "esmagamento" das colunas
        config_colunas = {
            "ID": {"width": 40, "anchor": "center", "stretch": False},
            "Título": {"width": 300, "anchor": "w", "stretch": True},
            "Programa": {"width": 180, "anchor": "w", "stretch": True},
            "IES": {"width": 100, "anchor": "center", "stretch": False},
            "Classificação": {"width": 100, "anchor": "center", "stretch": False},
            "Link Detalhes": {"width": 150, "anchor": "w", "stretch": True} 
        }
        
        for col in self.colunas:
            conf = config_colunas[col]
            self.tree.heading(col, text=col, command=lambda c=col: self.controller.ordenar_coluna(c, False))
            self.tree.column(col, width=conf["width"], anchor=conf["anchor"], stretch=conf["stretch"])

        # Barras de rolagem
        scroll_y = ttk.Scrollbar(frame_tree, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(frame_tree, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        # Layout final
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        
        frame_tree.grid_columnconfigure(0, weight=1)
        frame_tree.grid_rowconfigure(0, weight=1)

        # Tags de cores (Permanecem iguais)
        self.tree.tag_configure('juridico', background='#d4edda')
        self.tree.tag_configure('nao_juridico', background='#f8d7da')
        self.tree.tag_configure('pendente', background='white')
        
        # Bind do clique para mostrar detalhes
        self.tree.bind("<<TreeviewSelect>>", self.controller.clique_na_tabela)
        self.tree.bind("<Button-3>", self.mostrar_menu_contexto)
    
    def _configurar_tags(self):
        self.tree.tag_configure('juridico', background='#d1e7dd')
        self.tree.tag_configure('nao_juridico', background='#f8d7da')
        self.tree.tag_configure('pendente', background='white')

    def ocultar_detalhes(self):
        self.frame_detalhes.pack_forget()

    def _mudar_cursor_link(self, event):
        """Muda o cursor para 'hand2' apenas sobre a coluna de ação."""
        item_id = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        
        # Como agora temos 6 colunas, a coluna 'Ação' é a #6
        if column == "#6" and item_id:
            self.tree.configure(cursor="hand2")
        else:
            self.tree.configure(cursor="")

    def exibir_resumo(self, texto):
        self.frame_detalhes.pack(fill="x", side="bottom", padx=10, pady=5)
        self.txt_resumo.config(state="normal")
        self.txt_resumo.delete("1.0", tk.END)
        self.txt_resumo.insert(tk.END, texto)
        self.txt_resumo.config(state="disabled")