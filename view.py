import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from tkinter.scrolledtext import ScrolledText 
import datetime

class ScraperView:
    def __init__(self, root):
        self.root = root
        self.root.title("Coletor de Dados BDTD/Google")
        self.root.geometry("1200x750")

        # Configuração de Estilo
        style = ttk.Style()
        style.theme_use('clam')
        
        # --- Callbacks do Controller (Inicialização) ---
        self.get_row_status = None      
        self.on_action_item = None      
        self.on_action_search = None    
        self.on_reprocess = None        
        self.on_open_search_url = None
        self.on_show_sample = None
        
        # Compatibilidade com chamadas antigas
        self.search_info_command = None
        self.clear_pdf_command = None
        self.redownload_command = None
        self.clear_repo_command = None

        self.status_history = [] 
        
        # --- DADOS PARA FILTRAGEM E VISUALIZAÇÃO ---
        self.all_data = [] 
        self.filter_vars = {} 
        self.is_summarized = False
        
        # --- CRIAÇÃO DAS ABAS (NOTEBOOK) ---
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=5, pady=5)

        # Aba 1: Coletor (Interface Principal)
        self.tab_scraper = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_scraper, text="Coletor de Dados")
        
        # Aba 2: Programas (Nova Tabela)
        self.tab_programs = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_programs, text="Programas de Pós-Graduação")

        # --- CONFIGURAÇÃO DA ABA 1 (COLETOR) ---
        self._setup_layout()
        self._setup_table()
        
        # --- CONFIGURAÇÃO DA ABA 2 (PROGRAMAS) ---
        self._setup_programs_tab()

    def _setup_layout(self):
        """Monta a área de inputs e controles na primeira aba."""
        # Input Frame
        self.input_frame = tk.LabelFrame(self.tab_scraper, text="Parâmetros", padx=10, pady=5)
        self.input_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(self.input_frame, text="Motor:").pack(side="left")
        self.engine_var = tk.StringVar(value="BDTD")
        self.engine_cb = ttk.Combobox(self.input_frame, textvariable=self.engine_var, values=["BDTD", "Google"], width=8, state="readonly")
        self.engine_cb.pack(side="left", padx=5)

        tk.Label(self.input_frame, text="Termo:").pack(side="left")
        self.term_entry = tk.Entry(self.input_frame, width=30)
        self.term_entry.pack(side="left", padx=5)

        tk.Label(self.input_frame, text="Ano:").pack(side="left")
        self.year_entry = tk.Entry(self.input_frame, width=6)
        self.year_entry.pack(side="left", padx=5)
        self.year_entry.insert(0, str(datetime.datetime.now().year))

        # Action Frame
        self.action_frame = tk.Frame(self.tab_scraper)
        self.action_frame.pack(fill="x", padx=10, pady=5)

        self.btn_start = tk.Button(self.action_frame, text="Iniciar Coleta", bg="#dddddd")
        self.btn_start.pack(side="left", padx=5)

        self.btn_stop = tk.Button(self.action_frame, text="Parar", state="disabled", bg="#ffcccc")
        self.btn_stop.pack(side="left", padx=5)
        
        self.btn_refresh = tk.Button(self.action_frame, text="Atualizar Tabela")
        self.btn_refresh.pack(side="left", padx=5)

        self.btn_sample = tk.Button(self.action_frame, text="Amostra (1/Univ)", command=lambda: self._trigger_show_sample())
        self.btn_sample.pack(side="left", padx=5)

        self.lbl_link = tk.Label(self.action_frame, text="URL Alvo: -", fg="blue", cursor="hand2")
        self.lbl_link.pack(side="left", padx=15)
        self.lbl_link.bind("<Button-1>", lambda e: self._open_url(self.lbl_link.cget("text")))

        # Filter Frame
        self.filter_frame = tk.LabelFrame(self.tab_scraper, text="Filtros de Visualização", padx=10, pady=5)
        self.filter_frame.pack(fill="x", padx=10, pady=5)
        
        self._create_filter_widgets()

        # Log Frame
        self.log_frame = tk.LabelFrame(self.tab_scraper, text="Log de Status", padx=10, pady=5)
        self.log_frame.pack(fill="x", padx=10, pady=5)
        
        self.log_text = ScrolledText(self.log_frame, height=6, state='disabled', font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True)
        # Label simples para status rápido
        self.lbl_status = tk.Label(self.log_frame, text="Pronto.", anchor="w")
        self.lbl_status.pack(fill="x")

    def _setup_table(self):
        """Monta a tabela principal (Treeview) na primeira aba."""
        table_frame = tk.Frame(self.tab_scraper)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("ID", "Termo", "Ano", "Titulo", "Autor", "Sigla", "Universidade", "Programa", "PDF", "Repo", "BDTD")
        self.tree = ttk.Treeview(table_frame, columns=cols, show='headings', selectmode='extended')
        
        self.tree.heading("ID", text="ID")
        self.tree.column("ID", width=40, anchor="center")
        
        self.tree.heading("Termo", text="Termo")
        self.tree.column("Termo", width=80)

        self.tree.heading("Ano", text="Ano")
        self.tree.column("Ano", width=50, anchor="center")
        
        self.tree.heading("Titulo", text="Título")
        self.tree.column("Titulo", width=250)
        
        self.tree.heading("Autor", text="Autor")
        self.tree.column("Autor", width=120)
        
        self.tree.heading("Sigla", text="Sigla")
        self.tree.column("Sigla", width=60, anchor="center")

        self.tree.heading("Universidade", text="Universidade")
        self.tree.column("Universidade", width=150)
        
        self.tree.heading("Programa", text="Programa")
        self.tree.column("Programa", width=150)
        
        self.tree.heading("PDF", text="PDF")
        self.tree.column("PDF", width=40, anchor="center")
        
        self.tree.heading("Repo", text="Repo")
        self.tree.column("Repo", width=40, anchor="center")
        
        self.tree.heading("BDTD", text="BDTD")
        self.tree.column("BDTD", width=40, anchor="center")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        self.tree.pack(fill='both', expand=True)
        
        # Tags de cor
        self.tree.tag_configure('has_pdf', background='#d1e7dd') 
        self.tree.tag_configure('has_repo', background='#fff3cd')

        # Bindings
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Double-1>", self.on_double_click)
        
        # Menu de Contexto
        self.context_menu = tk.Menu(self.root, tearoff=0)
        
        self.menu_view = tk.Menu(self.context_menu, tearoff=0)
        self.menu_view.add_command(label="Ver HTML BDTD (Lista)", command=lambda: self._trigger_search_action('view'))
        self.menu_view.add_command(label="Ver HTML BDTD (Detalhe)", command=lambda: self._trigger_item_action('view', 'bdtd'))
        self.menu_view.add_command(label="Ver HTML Repositório", command=lambda: self._trigger_item_action('view', 'repo'))
        self.context_menu.add_cascade(label="Visualizar HTML Salvo", menu=self.menu_view)
        
        self.context_menu.add_separator()
        
        self.context_menu.add_command(label="Abrir Link da Busca (Navegador)", command=lambda: self._trigger_open_search_url())
        self.context_menu.add_command(label="Baixar HTML Repositório", command=lambda: self._trigger_item_action('download', 'repo'))
        self.context_menu.add_command(label="Baixar HTML Repositório (VISUAL)", command=lambda: self._trigger_item_action('download_visual', 'repo'))
        self.context_menu.add_command(label="Reprocessar Dados (Parser)", command=lambda: self._trigger_reprocess())
        self.context_menu.add_command(label="Definir SIGLA Manualmente", command=lambda: self._trigger_item_action('set_sigla', 'manual'))
        
        self.context_menu.add_separator()
        
        self.menu_clear = tk.Menu(self.context_menu, tearoff=0)
        self.menu_clear.add_command(label="Limpar URL PDF", command=lambda: self._safe_clear_command(self.clear_pdf_command))
        self.menu_clear.add_command(label="Limpar URL Repositório", command=lambda: self._safe_clear_command(self.clear_repo_command))
        self.menu_clear.add_command(label="Apagar Dados Extraídos", command=lambda: self._trigger_item_action('delete_extraction', 'extracted_data'))
        self.menu_clear.add_command(label="Apagar HTML Busca (Lista)", command=lambda: self._trigger_search_action('delete'))
        self.menu_clear.add_command(label="Apagar HTML BDTD (Detalhe)", command=lambda: self._trigger_item_action('delete', 'bdtd'))
        self.menu_clear.add_command(label="Apagar HTML Repositório", command=lambda: self._trigger_item_action('delete', 'repo'))
        self.context_menu.add_cascade(label="Limpar / Apagar", menu=self.menu_clear)

    def _create_filter_widgets(self):
        """Cria os checkboxes para filtros."""
        frame_cb = ttk.Frame(self.filter_frame)
        frame_cb.pack(fill='x', pady=2)
        
        filtros = [
            ("Faltando Sigla", 5),
            ("Faltando Universidade", 6),
            ("Faltando Programa", 7),
            ("Sem Link PDF", 8),
            ("Sem Link Repositório", 9)
        ]
        
        for texto, col_idx in filtros:
            var = tk.BooleanVar()
            self.filter_vars[col_idx] = var 
            cb = ttk.Checkbutton(frame_cb, text=texto, variable=var, command=self._apply_filters)
            cb.pack(side='left', padx=10)

    def _apply_filters(self):
        """Aplica filtros na tabela principal."""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for values in self.all_data:
            mostrar = True
            for col_idx, var in self.filter_vars.items():
                if var.get(): 
                    valor_celula = str(values[col_idx]).strip()
                    if valor_celula not in ['-', '', 'None']:
                        if col_idx in [8, 9] and len(valor_celula) > 5:
                             mostrar = False
                        elif col_idx not in [8, 9]:
                             mostrar = False
            if mostrar:
                self._insert_row_visual(values)

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def on_double_click(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            vals = self.tree.item(item)['values']
            # Tenta abrir o PDF (8) ou o Repo (9)
            if vals[8] and len(vals[8]) > 5:
                self._open_url(vals[8])
            elif vals[9] and len(vals[9]) > 5:
                self._open_url(vals[9])

    def _sort_treeview(self, tree, col, descending):
        data = [(tree.set(child, col), child) for child in tree.get_children('')]
        try:
            data.sort(key=lambda t: float(t[0]), reverse=descending)
        except ValueError:
            data.sort(key=lambda t: t[0].lower(), reverse=descending)
        for index, (val, k) in enumerate(data):
            tree.move(k, '', index)
        tree.heading(col, command=lambda: self._sort_treeview(tree, col, not descending))

    def load_programs_data(self, data_rows):
        for item in self.prog_tree.get_children():
            self.prog_tree.delete(item)
        if not data_rows:
            self.lbl_total_progs.config(text="0")
            return
        for row in data_rows:
            self.prog_tree.insert('', 'end', values=row)
        self.lbl_total_progs.config(text=str(len(data_rows)))

    def _insert_row_visual(self, values):
        item_id = self.tree.insert('', 'end', values=values)
        link_pdf = values[8]
        link_repo = values[9]
        tags = []
        if link_pdf and len(link_pdf) > 5 and link_pdf != '-':
            tags.append('has_pdf')
        elif link_repo and len(link_repo) > 5 and link_repo != '-':
            tags.append('has_repo')
        self.tree.item(item_id, tags=tags)

    def add_row(self, *values):
        self.all_data.append(values)
        self._insert_row_visual(values)

    def update_row_by_id(self, db_id, sigla, univ, prog, link_pdf):
        for item in self.tree.get_children():
            vals = list(self.tree.item(item, 'values'))
            if str(vals[0]) == str(db_id):
                vals[5] = sigla
                vals[6] = univ
                vals[7] = prog
                vals[8] = link_pdf
                self.tree.item(item, values=tuple(vals))
                tags = []
                if link_pdf and len(link_pdf) > 5 and link_pdf != '-':
                    tags.append('has_pdf')
                elif vals[9] and len(vals[9]) > 5 and vals[9] != '-':
                    tags.append('has_repo')
                self.tree.item(item, tags=tags)
                break
        
        for i, row in enumerate(self.all_data):
            if str(row[0]) == str(db_id):
                new_row = list(row)
                new_row[5] = sigla
                new_row[6] = univ
                new_row[7] = prog
                new_row[8] = link_pdf
                self.all_data[i] = tuple(new_row)
                break

    # --- Helpers de Interação ---

    def _get_selected_id(self):
        selected = self.tree.selection()
        if selected:
            return self.tree.item(selected[0])['values'][0]
        return None

    def _get_selected_meta(self):
        selected = self.tree.selection()
        if selected:
            vals = self.tree.item(selected[0])['values']
            # Tenta extrair a página da URL BDTD (coluna 10)
            url_bdtd = str(vals[10])
            pagina = 1
            if 'page=' in url_bdtd:
                try:
                    pagina = url_bdtd.split('page=')[1].split('&')[0]
                except: pass
                
            return {
                'id': vals[0],
                'termo': vals[1],
                'ano': vals[2],
                'pagina': pagina
            }
        return None

    def _trigger_item_action(self, action, target, extra_arg=None):
        item_id = self._get_selected_id()
        if item_id and self.on_action_item:
            vals = self.tree.item(self.tree.selection()[0])['values']
            # Coluna 9 = Repo, 10 = BDTD
            url = vals[9] if target == 'repo' else vals[10] 
            self.on_action_item(action, item_id, target, url)

    def _trigger_search_action(self, action):
        meta = self._get_selected_meta()
        if meta and self.on_action_search:
            self.on_action_search(action, meta)

    def _trigger_reprocess(self):
        item_id = self._get_selected_id()
        if item_id and self.on_reprocess:
            vals = self.tree.item(self.tree.selection()[0])['values']
            link_repo = vals[9]
            self.on_reprocess(item_id, link_repo)

    def _trigger_open_search_url(self):
        meta = self._get_selected_meta()
        if meta and self.on_open_search_url:
            self.on_open_search_url(meta)

    def _trigger_show_sample(self):
        if self.on_show_sample:
            self.on_show_sample()

    def _safe_clear_command(self, cmd):
        if cmd: cmd(self._get_selected_id())

    # --- Setters e Utilitários Padrão ---

    def get_inputs(self):
        return {
            'term': self.term_entry.get(),
            'year': self.year_entry.get(),
            'engine': self.engine_var.get()
        }

    def set_start_command(self, command):
        self.btn_start.config(command=command)

    def set_stop_command(self, command):
        self.btn_stop.config(command=command)
    
    def set_refresh_command(self, command):
        self.btn_refresh.config(command=command)

    def set_year_changed_command(self, command):
        self.year_entry.bind('<KeyRelease>', lambda e: command())
        self.term_entry.bind('<KeyRelease>', lambda e: command())
        self.engine_var.trace("w", lambda *args: command())
        
    def set_search_info_command(self, command):
        self.search_info_command = command

    def toggle_buttons(self, is_running):
        state_start = 'disabled' if is_running else 'normal'
        state_stop = 'normal' if is_running else 'disabled'
        self.btn_start.config(state=state_start)
        self.btn_stop.config(state=state_stop)

    def update_status(self, msg):
        self.lbl_status.config(text=msg)
        self.log_text.config(state='normal')
        self.log_text.insert('end', f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.log_text.see('end')
        self.log_text.config(state='disabled')
        self.root.update_idletasks()

    def update_link_display(self, url):
        self.lbl_link.config(text=url)

    def _open_url(self, url):
        if url and url.startswith("http"):
            webbrowser.open(url)

    def clear_table(self):
        self.all_data = [] 
        for item in self.tree.get_children():
            self.tree.delete(item)
            
            
#################

    def _setup_programs_tab(self):
        """Monta a tabela de programas na segunda aba com a nova coluna de contagem."""
        filter_frame = ttk.Frame(self.tab_programs)
        filter_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(filter_frame, text="Total de Registros:").pack(side='left')
        self.lbl_total_progs = ttk.Label(filter_frame, text="0")
        self.lbl_total_progs.pack(side='left', padx=5)

        tree_frame = ttk.Frame(self.tab_programs)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # Definição das Colunas (Adicionado "Qtd. Trabalhos" ao final)
        cols = (
            "Código", "Programa", "Sigla IES", "Grau", 
            "Modalidade", "Nota", "Situação", "Associativa", 
            "Área Aval.", "Área Conec.", "Grande Área", "Qtd. Trabalhos"
        )

        self.prog_tree = ttk.Treeview(tree_frame, columns=cols, show='headings', selectmode='browse')
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.prog_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.prog_tree.xview)
        self.prog_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        self.prog_tree.pack(fill='both', expand=True)

        # Configuração das Colunas (Larguras e Ordenação)
        # Ajustei as larguras para acomodar a nova coluna
        col_widths = [80, 250, 70, 90, 90, 40, 90, 40, 120, 120, 120, 80]
        
        for i, col in enumerate(cols):
            self.prog_tree.heading(
                col, 
                text=col, 
                command=lambda c=col: self._sort_treeview(self.prog_tree, c, False)
            )
            # Define largura mínima e padrão
            self.prog_tree.column(col, width=col_widths[i], minwidth=40, anchor="center" if i in [0,2,5,7,11] else "w")