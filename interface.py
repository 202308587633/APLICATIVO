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
        """Orquestra a criação dos componentes."""
        self._criar_cabecalho()
        self._criar_secao_fonte_e_ano() 
        self._criar_secao_filtros()
        self._criar_secao_acoes()
        self._criar_tabela_resultados()
        self._criar_painel_detalhes()

    def _criar_cabecalho(self):
        tk.Label(self.root, text="Buscador BDTD - Doutorado", 
                 font=("Arial", 14, "bold")).pack(pady=10)

    def _criar_secao_ano(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=5)
        
        tk.Label(frame, text="Ano de Referência (2020-2025):", 
                 font=("Arial", 10, "bold")).pack(side="left", padx=5)

        self.anos = ["2020", "2021", "2022", "2023", "2024", "2025"]
        self.ano_selecionado_var = tk.StringVar(value="Selecione")
        
        self.combo_ano = ttk.Combobox(frame, values=self.anos, state="readonly", 
                                     textvariable=self.ano_selecionado_var, width=15)
        self.combo_ano.pack(side="left", padx=5)
        self.ano_selecionado_var.trace_add("write", lambda *args: self.controller.validar_estado_botoes())

    def _criar_secao_fonte_e_ano(self):
        """Cria seletores para a Base de Dados e o Ano de Referência."""
        frame_mestre = tk.Frame(self.root)
        frame_mestre.pack(pady=10)

        # --- SELETOR DE FONTE ---
        tk.Label(frame_mestre, text="Fonte de Dados:", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        
        self.fontes_disponiveis = {
            "BDTD (IBICT)": "https://bdtd.ibict.br/",
            "SciELO Brasil": "https://www.scielo.br/",
            "Google Scholar": "https://scholar.google.com.br/",
            "Periódicos CAPES": "https://www.periodicos.capes.gov.br/",
            "Lens.org": "https://www.lens.org/"
        }
        
        self.fonte_selecionada_var = tk.StringVar(value="Selecione a Fonte")
        self.combo_fonte = ttk.Combobox(frame_mestre, values=list(self.fontes_disponiveis.keys()), 
                                       state="readonly", textvariable=self.fonte_selecionada_var, width=25)
        self.combo_fonte.pack(side="left", padx=15)

        # --- SELETOR DE ANO ---
        tk.Label(frame_mestre, text="Ano:", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        self.anos = ["2020", "2021", "2022", "2023", "2024", "2025"]
        self.ano_selecionado_var = tk.StringVar(value="Selecione")
        self.combo_ano = ttk.Combobox(frame_mestre, values=self.anos, state="readonly", 
                                     textvariable=self.ano_selecionado_var, width=10)
        self.combo_ano.pack(side="left", padx=5)

        # Rastreia mudanças para validar o botão de busca
        self.fonte_selecionada_var.trace_add("write", lambda *args: self.controller.validar_estado_botoes())
        self.ano_selecionado_var.trace_add("write", lambda *args: self.controller.validar_estado_botoes())

    def _criar_secao_filtros(self):
        """Orquestra a criação da área de filtros dividindo em colunas."""
        self.termos = [
            "Jurimetria", "Inteligência Artificial", "Análise de discurso", 
            "Algoritmo", "Direito Digital", "Tecnologia da Informação",
            "Hermenêutica Jurídica", "Filosofia do Direito", "Teoria do Direito", 
            "Violação de Direitos Humanos", "Jurisdição Constitucional", "Responsabilidade Civil"
        ]
        
        # Container horizontal mestre
        frame_pai = tk.Frame(self.root)
        frame_pai.pack(pady=5, padx=10, fill="x")

        # Delega a criação de cada coluna para funções especialistas
        self._configurar_coluna_inclusao(frame_pai)
        self._configurar_coluna_exclusao(frame_pai)

    def _configurar_coluna_inclusao(self, parent):
        """Cria o grupo de rádio botões para escolha do termo principal."""
        self.frame_inc = tk.LabelFrame(parent, text="1. INCLUIR (Termo Principal)", 
                                       fg="green", font=("Arial", 9, "bold"))
        self.frame_inc.pack(side="left", expand=True, fill="both", padx=5)
        
        self.var_inc_unica = tk.StringVar(value="vazio") 
        self.var_inc_unica.trace_add("write", self._logica_filtros_automatica)

        # Monta a grade interna
        grid = tk.Frame(self.frame_inc)
        grid.pack(pady=5, padx=5)
        
        for i, termo in enumerate(self.termos):
            rb = tk.Radiobutton(grid, text=termo, variable=self.var_inc_unica, 
                                value=termo, font=("Arial", 8))
            self._posicionar_na_grade(rb, i)

    def _configurar_coluna_exclusao(self, parent):
        """Cria o grupo de checkbuttons automáticos (desabilitados)."""
        self.frame_exc = tk.LabelFrame(parent, text="2. EXCLUSÕES (Automáticas)", 
                                       fg="red", font=("Arial", 9, "bold"))
        self.frame_exc.pack(side="left", expand=True, fill="both", padx=5)

        self.vars_exc = {}
        grid = tk.Frame(self.frame_exc)
        grid.pack(pady=5, padx=5)

        for i, termo in enumerate(self.termos):
            var = tk.BooleanVar(value=False)
            self.vars_exc[termo] = var
            cb = tk.Checkbutton(grid, text=termo, variable=var, state="disabled", 
                                disabledforeground="#A0A0A0", font=("Arial", 8))
            self._posicionar_na_grade(cb, i)

    def _posicionar_na_grade(self, widget, index, colunas=3):
        """Função utilitária para posicionar widgets em grades de N colunas."""
        row = index // colunas
        col = index % colunas
        widget.grid(row=row, column=col, sticky="w", padx=5, pady=2)
    
    def _criar_secao_acoes(self):
        frame = tk.Frame(self.root)
        frame.pack(pady=10)

        self.btn_buscar = tk.Button(frame, text="Iniciar Pesquisa", 
                                   command=self.controller.disparar_busca, 
                                   bg="#2ecc71", fg="white", font=("Arial", 10, "bold"), 
                                   padx=20, state="disabled")
        self.btn_buscar.pack(side="left", padx=5)

        self.btn_carregar = tk.Button(frame, text="Carregar Dados Salvos", 
                                     command=self.controller.carregar_do_banco,
                                     bg="#3498db", fg="white", font=("Arial", 10, "bold"), padx=20)
        self.btn_carregar.pack(side="left", padx=5)

        self.lbl_status = tk.Label(self.root, text="Obrigatório selecionar Ano e Termo.", 
                                   font=("Arial", 9, "italic"), fg="red")
        self.lbl_status.pack()

    def _criar_tabela_resultados(self):
        frame = tk.Frame(self.root)
        frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.colunas = ("ID", "Título", "Autor", "IES", "Programa", "Classe", "Ação", "Link")
        self.tree = ttk.Treeview(frame, columns=self.colunas, show='headings')
        
        larguras = {"ID": 40, "Título": 300, "Autor": 150, "IES": 100, "Programa": 150, "Classe": 100, "Ação": 120, "Link": 0}
        for col in self.colunas:
            self.tree.heading(col, text=col, command=lambda c=col: self.controller.ordenar_coluna(c, False))
            self.tree.column(col, width=larguras.get(col, 100), anchor="w" if col=="Título" else "center")
        
        self.tree.column("Link", width=0, stretch=tk.NO)

        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.tree.bind("<ButtonRelease-1>", self.controller.clique_na_tabela)
        self.tree.bind("<Double-1>", self.controller.abrir_link)

    def _criar_painel_detalhes(self):
        self.frame_detalhes = tk.LabelFrame(self.root, text="Detalhes e Resumo", font=("Arial", 10, "bold"))
        self.txt_resumo = tk.Text(self.frame_detalhes, wrap="word", height=8, font=("Arial", 10), state="disabled")
        self.txt_resumo.pack(fill="both", expand=True, padx=5, pady=5)
        tk.Button(self.frame_detalhes, text="Fechar Painel", command=self.ocultar_detalhes).pack(anchor="e")
    
    def _logica_filtros_automatica(self, *args):
        """Regra: Selecionar termo teórico (6 últimos) exclui os tecnológicos (6 primeiros)."""
        termo = self.var_inc_unica.get()
        if not termo: return
        
        idx = self.termos.index(termo)

        # Limpa exclusões anteriores
        for var in self.vars_exc.values():
            var.set(False)

        # Se for do segundo bloco (índice 6 em diante), marca exclusão dos primeiros 6
        if idx >= 6:
            for i in range(6):
                self.vars_exc[self.termos[i]].set(True)
        
        # Avisa o controller para validar se o botão de busca pode ser ativado
        self.controller.validar_estado_botoes()

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