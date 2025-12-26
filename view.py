import tkinter as tk
from tkinter import ttk
import webbrowser
from tkinter.scrolledtext import ScrolledText 
import datetime

class ScraperView:
    def __init__(self, root):
        self.root = root
        self.root.title("Scraper Modular Juridico - BDTD/Google")
        self.root.geometry("1400x800")
        
        # --- Callbacks do Controller ---
        self.get_row_status = None      
        self.on_action_item = None      
        self.on_action_search = None    
        self.on_reprocess = None        
        self.on_open_search_url = None # <--- NOVO CALLBACK
        
        self.search_info_command = None
        self.clear_pdf_command = None
        self.redownload_command = None
        self.clear_repo_command = None

        self.status_history = [] 
        
        # --- DADOS PARA FILTRAGEM ---
        self.all_data = [] 
        self.filter_vars = {} 
        
        self._setup_layout()
        self._setup_table()

    def _setup_layout(self):
        self.input_frame = tk.LabelFrame(self.root, text="Parametros", padx=10, pady=10)
        self.input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Widgets de Input
        tk.Label(self.input_frame, text="Motor:").pack(side=tk.LEFT)
        self.combo_engine = ttk.Combobox(self.input_frame, values=["BDTD", "Google"], width=10, state="readonly")
        self.combo_engine.current(0)
        self.combo_engine.pack(side=tk.LEFT, padx=5)
        
        tk.Label(self.input_frame, text="Termo:").pack(side=tk.LEFT)
        self.combo_term = ttk.Combobox(self.input_frame, values=["jurimetria", "inteligência artificial", "análise de discurso", "algoritmo", "direito digital" , "tecnologia da informação"], width=60)
        self.combo_term.pack(side=tk.LEFT, padx=5)
        
        tk.Label(self.input_frame, text="Ano:").pack(side=tk.LEFT)
        self.combo_year = ttk.Combobox(self.input_frame, values=[str(x) for x in range(2020, 2026)], width=6)
        self.combo_year.current(0)
        self.combo_year.pack(side=tk.LEFT, padx=5)
        
        # Botões
        self.btn_run = tk.Button(self.input_frame, text="Iniciar", bg="#4CAF50", fg="white")
        self.btn_run.pack(side=tk.LEFT, padx=5)
        
        self.btn_stop = tk.Button(self.input_frame, text="Parar", bg="#F44336", fg="white", state="disabled")
        self.btn_stop.pack(side=tk.LEFT, padx=5)
        
        self.btn_refresh = tk.Button(self.input_frame, text="Recarregar", bg="#2196F3", fg="white")
        self.btn_refresh.pack(side=tk.LEFT, padx=5)
        
        # Barra de Status Clicável
        self.status_frame = tk.Frame(self.root, bd=1, relief=tk.SUNKEN)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.lbl_status = tk.Label(self.status_frame, text="Pronto.", anchor=tk.W, cursor="hand2", fg="blue")
        self.lbl_status.pack(fill=tk.X)
        self.lbl_status.bind("<Button-1>", self.show_status_history)
        
        # Preview de Link
        self.link_frame = tk.Frame(self.root, padx=5)
        self.link_frame.pack(fill=tk.X)
        self.lbl_link = tk.Label(self.link_frame, text="...", fg="gray")
        self.lbl_link.pack(side=tk.LEFT)

    def _setup_table(self):
        self.table_frame = tk.Frame(self.root)
        self.table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Definição das colunas e larguras iniciais
        self.columns_config = {
            "id": {"text": "ID", "width": 40, "anchor": "center"},
            "termo": {"text": "Termo", "width": 100},
            "titulo": {"text": "Título", "width": 300},
            "autor": {"text": "Autor", "width": 100},
            "sigla": {"text": "Sigla", "width": 60, "anchor": "center"},
            "universidade": {"text": "Universidade", "width": 120},
            "programa": {"text": "Programa", "width": 120},
            "link_pdf": {"text": "PDF", "width": 100},
            "link_repo": {"text": "Repo", "width": 100},
            "link_bdtd": {"text": "BDTD", "width": 100}
        }
        
        col_names = list(self.columns_config.keys())

        # --- FRAME DE FILTROS (Acima da Tabela) ---
        self.filter_frame = tk.Frame(self.table_frame)
        self.filter_frame.pack(fill=tk.X)

        # Cria uma entrada de texto para cada coluna
        for i, col in enumerate(col_names):
            cfg = self.columns_config[col]
            
            # Container para alinhar (Label pequena + Entry)
            f_container = tk.Frame(self.filter_frame, width=cfg["width"], bd=1, relief=tk.RAISED)
            f_container.pack_propagate(False) # Mantém tamanho fixo
            f_container.pack(side=tk.LEFT, padx=1, fill=tk.Y)
            
            # Variável de controle
            var = tk.StringVar()
            var.trace("w", lambda name, index, mode, v=var: self._apply_filters())
            self.filter_vars[col] = var
            
            # Entry do filtro
            ent = tk.Entry(f_container, textvariable=var, font=("Arial", 8))
            ent.pack(fill=tk.BOTH, expand=True)
            
            # Placeholder/Tooltip simples
            tk.Label(f_container, text=cfg["text"], font=("Arial", 7, "bold"), bg="#ddd").pack(fill=tk.X, side=tk.TOP)

        # --- TREEVIEW ---
        self.tree = ttk.Treeview(self.table_frame, columns=col_names, show="headings", selectmode="browse")

        for col in col_names:
            cfg = self.columns_config[col]
            self.tree.heading(col, text=cfg["text"], command=lambda _col=col: self.sort_column(_col, False))
            self.tree.column(col, width=cfg["width"], anchor=cfg.get("anchor", "w"))

        scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree.bind("<Button-3>", self._on_right_click)
        self.tree.bind("<Double-1>", self._on_double_click)

    # --- MÉTODO QUE FALTAVA (CORREÇÃO DO ERRO) ---
    def get_inputs(self):
        """Retorna os valores atuais dos campos de entrada."""
        return {
            "engine": self.combo_engine.get(),
            "term": self.combo_term.get(),
            "year": self.combo_year.get()
        }

    # --- Métodos de Interface ---
    def add_row(self, *args):
        """Adiciona linha na visualização e no cache de dados."""
        # Salva na lista completa para permitir filtragem posterior
        self.all_data.append(args)
        # Insere na árvore (se os filtros atuais permitirem, idealmente, mas aqui inserimos direto)
        self.tree.insert("", "end", values=args)
        # Reaplica filtros para garantir consistência se houver algo digitado
        if any(v.get() for v in self.filter_vars.values()):
            self._apply_filters()

    def clear_table(self):
        """Limpa visualização e cache."""
        self.all_data = [] # Limpa cache
        for item in self.tree.get_children():
            self.tree.delete(item)

       
    def update_status(self, text): 
        hora = datetime.datetime.now().strftime("%H:%M:%S")
        self.lbl_status.config(text=text)
        self.status_history.append(f"[{hora}] {text}")
        if len(self.status_history) > 300: self.status_history.pop(0)

    def show_status_history(self, event=None):
        top = tk.Toplevel(self.root)
        top.title("Log de Execução")
        top.geometry("600x400")
        txt = ScrolledText(top); txt.pack(fill=tk.BOTH, expand=True)
        for m in self.status_history: txt.insert(tk.END, m+"\n")
        txt.see(tk.END)

    def update_link_display(self, url): 
        self.lbl_link.config(text=url)

    def toggle_buttons(self, is_running): 
        self.btn_run.config(state="disabled" if is_running else "normal")
        self.btn_stop.config(state="normal" if is_running else "disabled")

    def update_row_by_id(self, db_id, s, u, p, pdf):
        for item in self.tree.get_children():
            if str(self.tree.item(item, 'values')[0]) == str(db_id):
                v = list(self.tree.item(item, 'values'))
                v[4], v[5], v[6], v[7] = s, u, p, pdf
                self.tree.item(item, values=tuple(v)); break

    def open_browser(self, url):
        if url and url.startswith("http"): webbrowser.open_new_tab(url)

    # --- Configuração de Comandos ---
    def set_start_command(self, cmd): self.btn_run.config(command=cmd)
    def set_stop_command(self, cmd): self.btn_stop.config(command=cmd)
    def set_refresh_command(self, cmd): self.btn_refresh.config(command=cmd)
    
    def set_year_changed_command(self, cmd):
        self.combo_year.bind("<<ComboboxSelected>>", cmd)
        self.combo_term.bind("<<ComboboxSelected>>", cmd)
        self.combo_engine.bind("<<ComboboxSelected>>", cmd)

    # Setters legados (para compatibilidade se o controller chamar)
    def set_search_info_command(self, cmd): pass 

    # --- Menu de Contexto (Lógica Granular) ---
    def _on_right_click(self, event):
        """
        Menu de contexto com opções de navegação, gestão e extração/limpeza.
        """
        item_id = self.tree.identify_row(event.y)
        if not item_id: return
        self.tree.selection_set(item_id)
        
        vals = self.tree.item(item_id, 'values')
        db_id = vals[0]
        
        status = self.get_row_status(db_id) if self.get_row_status else None
        if not status: return

        meta = status.get('meta', {})
        link_bdtd = meta.get('link_bdtd', '')
        link_repo = meta.get('link_repo', '')
        link_pdf = meta.get('link_pdf', '')
        
        # Estados dos Arquivos
        st_bdtd_file = "normal" if status.get('has_bdtd') else "disabled"
        st_repo_file = "normal" if status.get('has_repo') else "disabled"
        st_search_file = "normal" if status.get('has_search') else "disabled"

        # Estados dos Links
        st_url_bdtd = "normal" if link_bdtd and link_bdtd.startswith("http") else "disabled"
        st_url_repo = "normal" if link_repo and link_repo.startswith("http") else "disabled"
        st_url_pdf = "normal" if link_pdf and link_pdf.startswith("http") else "disabled"

        m = tk.Menu(self.root, tearoff=0)

        # --- 1. BUSCADOR (Detalhes) ---
        m.add_command(label="--- DETALHES (BUSCADOR) ---", state="disabled")
        m.add_command(label="🌐 Abrir URL do Buscador", state=st_url_bdtd, 
                      command=lambda: self.open_browser(link_bdtd))
        m.add_command(label="📄 Exibir HTML Local", state=st_bdtd_file, 
                      command=lambda: self.on_action_item('view', db_id, 'bdtd'))
        m.add_command(label="❌ Apagar HTML", state=st_bdtd_file, 
                      command=lambda: self.on_action_item('delete', db_id, 'bdtd'))
        m.add_command(label="⬇️ Baixar HTML", 
                      command=lambda: self.on_action_item('download', db_id, 'bdtd', link_bdtd))

        m.add_separator()

        # --- 2. REPOSITÓRIO (Universidade) ---
        m.add_command(label="--- REPOSITÓRIO ---", state="disabled")
        m.add_command(label="🌐 Abrir URL do Repositório", state=st_url_repo, 
                      command=lambda: self.open_browser(link_repo))
        m.add_command(label="📄 Abrir PDF Original", state=st_url_pdf, 
                      command=lambda: self.open_browser(link_pdf))

        m.add_command(label="🏛️ Exibir HTML Local", state=st_repo_file, 
                      command=lambda: self.on_action_item('view', db_id, 'repo'))
        
        m.add_command(label="⚙️ Extrair Programa e PDF (Local)", state=st_repo_file, 
                      command=lambda: self.on_reprocess(db_id, link_repo))
        
        m.add_command(label="⚙️ Obter Sigla e Universidade (Local)", state=st_repo_file, 
                      command=lambda: self.on_reprocess(db_id, link_repo))

        # --- NOVA OPÇÃO DE APAGAR ---
        m.add_command(label="❌ Apagar Dados Extraídos", 
                      command=lambda: self.on_action_item('delete_extraction', db_id, 'repo'))

        m.add_command(label="❌ Apagar HTML", state=st_repo_file, 
                      command=lambda: self.on_action_item('delete', db_id, 'repo'))
        
        m.add_command(label="⬇️ Baixar HTML", state=st_url_repo,
                      command=lambda: self.on_action_item('download', db_id, 'repo', link_repo))

        m.add_separator()

        # --- 3. PÁGINA DE PESQUISA (Lista) ---
        m.add_command(label="--- LISTA DE RESULTADOS ---", state="disabled")
        m.add_command(label="🌐 Abrir URL da Lista", 
                      command=lambda: self.on_open_search_url(meta))
        m.add_command(label="📄 Exibir Lista Local", state=st_search_file, 
                      command=lambda: self.on_action_search('view', meta))
        m.add_command(label="❌ Apagar Lista", state=st_search_file, 
                      command=lambda: self.on_action_search('delete', meta))
        m.add_command(label="⬇️ Baixar Lista", 
                      command=lambda: self.on_action_search('download', meta))

        m.add_separator()
        # Exemplo de como adicionar no view.py (dentro do menu de contexto)
        m.add_command(label="Definir Sigla Manualmente", 
                      command=lambda: self._handle_action("set_sigla", item_id, "repo", None))

        m.post(event.x_root, event.y_root)

        
    def _on_double_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id: return
        vals = self.tree.item(item_id, 'values')
        # Tenta abrir o link da BDTD (coluna 9)
        if len(vals) > 9 and vals[9].startswith("http"):
            self.open_browser(vals[9])

    def _apply_filters(self):
        """Filtra os dados locais e atualiza a Treeview."""
        # 1. Obtém termos de busca
        filters = {col: var.get().lower() for col, var in self.filter_vars.items() if var.get()}
        
        # 2. Limpa visualização atual (não apaga self.all_data)
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # 3. Mapeia índices das colunas
        col_indices = {col: i for i, col in enumerate(self.columns_config.keys())}
        
        # 4. Reinsere apenas o que combina
        for row in self.all_data:
            match = True
            for col, text in filters.items():
                idx = col_indices[col]
                cell_value = str(row[idx]).lower()
                if text not in cell_value:
                    match = False
                    break
            
            if match:
                self.tree.insert("", "end", values=row)

    def sort_column(self, col, reverse):
        """Ordena a Treeview clicando no cabeçalho."""
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        
        try:
            # Tenta ordenar como número (para ID)
            l.sort(key=lambda t: float(t[0]), reverse=reverse)
        except ValueError:
            # Ordenação padrão string
            l.sort(key=lambda t: t[0].lower(), reverse=reverse)

        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)

        # Alterna direção para o próximo clique
        self.tree.heading(col, command=lambda: self.sort_column(col, not reverse))
        
#################################

    def _handle_action(self, action, item_id, target_type, url=None):
        """
        Método auxiliar para disparar ações do menu de contexto.
        Verifica se o controller conectou uma função a 'on_action_item' antes de chamar.
        """
        if hasattr(self, 'on_action_item') and self.on_action_item:
            self.on_action_item(action, item_id, target_type, url)
        else:
            print(f"Ação '{action}' ignorada: Controller não conectado.")