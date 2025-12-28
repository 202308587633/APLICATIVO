import threading
import queue
import requests
import urllib3
import os
import tempfile
import webbrowser
from services.strategies import BDTDStrategy, GoogleStrategy

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ScraperController:
    def __init__(self, root):
        self.root = root
        
        # Importações locais
        from view import ScraperView
        from model import ScraperModel
        from database import ScraperDB

        # Inicialização dos componentes
        self.view = ScraperView(root)
        self.model = ScraperModel()
        self.db = ScraperDB() # Conecta automaticamente ao instance/trabalhos.db
        
        self.msg_queue = queue.Queue()
        self.is_running = False 
        
        # Configurações iniciais
        self._setup_commands()
        self.update_url_preview()
        
        # Carrega dados da aba 1 (Coletor)
        self.load_initial_data()
        
        # --- CARREGAMENTO DOS DADOS DA ABA 2 (PROGRAMAS) ---
        # Inicia uma thread para buscar os dados do banco sem travar a tela
        threading.Thread(target=self.load_programs_from_db, daemon=True).start()
        
        self.check_queue()

    def load_programs_from_db(self):
        """
        Busca os dados da tabela 'programas_pos' no banco e envia para a View.
        """
        try:
            # 1. Busca no banco de dados
            programs = self.db.get_all_programs()
            
            if programs:
                qtd = len(programs)
                # 2. Atualiza a View na thread principal (seguro para UI)
                self.root.after(0, lambda: self.view.load_programs_data(programs))
                self.msg_queue.put(('status', f"Programas carregados do banco: {qtd} registros."))
            else:
                self.msg_queue.put(('status', "Tabela de programas está vazia."))
                
        except Exception as e:
            self.msg_queue.put(('status', f"Erro ao ler tabela de programas: {e}"))

    # --- MÉTODOS EXISTENTES DO COLETOR (MANTIDOS) ---

    def handle_search_page_action(self, action, meta):
        termo, ano, pagina = meta['termo'], meta['ano'], meta['pagina']
        if action == 'view':
            html = self.db.get_search_page(termo, ano, pagina)
            if html: self._open_html_text(html, f"busca_{termo}_{pagina}")
            else: self.view.update_status("HTML da busca não encontrado.")
        elif action == 'delete':
            self.db.delete_search_page(termo, ano, pagina)
            self.view.update_status(f"HTML da busca (Pág {pagina}) apagado.")
        elif action == 'download':
            self._redownload_search_page(termo, ano, pagina)

    def _open_html_text(self, content, prefix):
        try:
            fd, path = tempfile.mkstemp(suffix='.html', prefix=prefix)
            with os.fdopen(fd, 'w', encoding='utf-8') as tmp:
                tmp.write(content)
            webbrowser.open('file://' + path)
            self.view.update_status("Visualização aberta no navegador.")
        except Exception as e:
            self.view.update_status(f"Erro ao abrir visualização: {e}")

    def start_scraping(self):
        self.view.clear_table()
        self.is_running = True
        self.view.toggle_buttons(True)
        inputs = self.view.get_inputs()
        threading.Thread(target=self.run_loop, args=(inputs,), daemon=True).start()

    def stop_scraping(self):
        self.is_running = False
        self.view.toggle_buttons(False)

    def run_loop(self, data):
        strategy = BDTDStrategy() if data['engine'] == "BDTD" else GoogleStrategy()
        page = 1
        total = 0
        def log(msg): self.msg_queue.put(('status', msg))

        try:
            while self.is_running:
                log(f"--- Processando Página {page} ---")
                items, msg, search_html = self.model.fetch(strategy, data['term'], data['year'], page, on_progress=log)

                if search_html:
                    self.db.save_search_page(data['engine'], data['term'], data['year'], page, search_html)

                if not items: 
                    self.msg_queue.put(('done', f"Fim. {msg} Total coletado: {total}"))
                    break

                for item in items:
                    if not self.is_running: break
                    item['termo'] = data['term']
                    item['ano'] = data['year']
                    item['pagina'] = page
                    item['id'] = self.db.save(item)
                    self.msg_queue.put(('row', item))
                    total += 1
                page += 1
        except Exception as e:
            self.msg_queue.put(('done', f"Erro Crítico: {e}"))

    def load_initial_data(self):
        try:
            registros = self.db.fetch_all()
            for row in registros: self.view.add_row(*row)
            if registros: self.view.update_status(f"Histórico: {len(registros)} registros carregados.")
        except Exception as e: self.view.update_status(f"Erro DB: {e}")

    def refresh_table_data(self):
        self.view.clear_table()
        self.load_initial_data()
        self.view.update_status("Tabela atualizada.")

    def update_url_preview(self, event=None):
        inputs = self.view.get_inputs()
        strategy = BDTDStrategy() if inputs['engine'] == "BDTD" else GoogleStrategy()
        try:
            url = strategy.get_url(inputs['term'], inputs['year'], 1)
            self.view.update_link_display(url)
        except: pass

    def open_stored_html(self, db_id, target_type):
        html = self.db.get_specific_html(db_id, target_type)
        if html: self._open_html_text(html, f"{target_type}_{db_id}")
        else: self.view.update_status(f"HTML {target_type} vazio.")

    def open_generated_search_url(self, meta):
        try:
            termo, ano, pagina = meta['termo'], meta['ano'], meta['pagina']
            strategy = BDTDStrategy() 
            url = strategy.get_url(termo, ano, pagina)
            webbrowser.open(url)
            self.view.update_status(f"Abrindo lista no navegador: Pág {pagina}")
        except Exception as e:
            self.view.update_status(f"Erro ao gerar URL: {e}")
            
    def _redownload_search_page(self, termo, ano, pagina):
        def _task():
            try:
                from services.strategies import BDTDStrategy
                strategy = BDTDStrategy()
                url = strategy.get_url(termo, ano, pagina)
                self.root.after(0, lambda: self.view.update_status(f"Baixando lista: {url[:40]}..."))
                headers = {'User-Agent': 'Mozilla/5.0'}
                resp = requests.get(url, headers=headers, timeout=20, verify=False)
                if resp.status_code == 200:
                    self.db.save_search_page("BDTD", termo, ano, pagina, resp.text)
                    self.root.after(0, lambda: self.view.update_status(f"Lista (Pág {pagina}) atualizada!"))
                else:
                    self.root.after(0, lambda: self.view.update_status(f"Erro HTTP {resp.status_code}"))
            except Exception as e:
                self.root.after(0, lambda: self.view.update_status(f"Erro download busca: {e}"))
        threading.Thread(target=_task, daemon=True).start()
 
    def _ask_visual_download(self, db_id, url, target_type, reason=None):
        from tkinter import messagebox
        msg_base = reason if reason else "O download padrão falhou ou retornou vazio."
        msg_final = f"{msg_base}\n\nDeseja abrir o navegador para capturar este item manualmente?"
        if messagebox.askyesno("Captura Visual Necessária", msg_final):
            self.force_redownload_visual(db_id, url, target_type)
        else:
            self.view.update_status(f"[ID {db_id}] Captura visual cancelada.")
            
    def force_redownload(self, db_id, url_alvo, target_type):
        def _task():
            def log(msg): self.root.after(0, lambda: self.view.update_status(f"[ID {db_id}] {msg}"))
            try:
                log(f"Iniciando download rápido ({target_type})...")
                from services.strategies import BDTDStrategy
                strategy = BDTDStrategy()
                final_url, html_content = strategy.download_page(url_alvo, on_progress=log)
                
                if html_content and len(html_content) > 500:
                    self.db.update_specific_html(db_id, target_type, html_content, final_url if target_type == 'repo' else None)
                    log("Download concluído com sucesso!")
                    if target_type == 'repo':
                        log("Iniciando extração de dados...")
                        self.retry_info_fetch(db_id, final_url or url_alvo)
                else:
                    log("AVISO: Conteúdo vazio/bloqueado.")
                    self.root.after(0, lambda: self._ask_visual_download(db_id, url_alvo, target_type, "Conteúdo vazio."))
            except Exception as e:
                log(f"Falha: {str(e)}")
                self.root.after(0, lambda: self._ask_visual_download(db_id, url_alvo, target_type, str(e)))
        threading.Thread(target=_task, daemon=True).start()

    def force_redownload_visual(self, db_id, url_alvo, target_type):
        def _task():
            def log(msg): self.root.after(0, lambda: self.view.update_status(f"[ID {db_id}] [Visual] {msg}"))
            try:
                log("Preparando navegador...")
                from services.strategies import BDTDStrategy
                strategy = BDTDStrategy()
                final_url, html_content = strategy.download_page_visual(url_alvo, on_progress=log)
                
                if html_content and len(html_content) > 500:
                    self.db.update_specific_html(db_id, target_type, html_content, final_url if target_type == 'repo' else None)
                    log("Sucesso! HTML atualizado.")
                    if target_type == 'repo':
                        self.retry_info_fetch(db_id, final_url or url_alvo)
                else:
                    log("Erro: Navegador retornou vazio.")
            except Exception as e:
                log(f"Falha Crítica: {str(e)}")
        threading.Thread(target=_task, daemon=True).start()

    def retry_info_fetch(self, db_id, link_repo):
        def _task():
            def log(m): self.root.after(0, lambda: self.view.update_status(f"[ID {db_id}] {m}"))
            log("Analisando HTML salvo...")
            html = self.db.get_specific_html(db_id, 'repo')
            if not html: 
                log("HTML não encontrado. Baixando...")
                self.force_redownload(db_id, link_repo, 'repo')
                return

            from services.strategies import BDTDStrategy
            strat = BDTDStrategy()
            data = strat.parse_from_stored_html(html, link_repo, on_progress=log)
            
            univ = data.get('universidade')
            if not univ or univ in ['-', 'None', 'N/A']:
                log("Falha na extração.")
                self.root.after(0, lambda: self._ask_visual_download(db_id, link_repo, 'repo', "Extração falhou."))
            else:
                log(f"Dados extraídos: {data.get('sigla')} - {data.get('programa')}")

            if (not data.get('sigla') or data.get('sigla') == '-') and link_repo and '.ufpr.' in link_repo.lower():
                data['sigla'] = 'UFPR'; data['universidade'] = 'Universidade Federal do Paraná'
            
            self.db.update_record_details(db_id, data)
            self.root.after(0, lambda: self.view.update_row_by_id(db_id, data.get('sigla'), data.get('universidade'), data.get('programa'), data.get('link_pdf')))
        threading.Thread(target=_task, daemon=True).start()
            
    def handle_item_action(self, action, db_id, target_type, url=None):
        if action == 'view': self.open_stored_html(db_id, target_type)
        elif action == 'delete': self.manage_field(db_id, f'html_{target_type}')
        elif action == 'download': 
            if url and url != "-": self.force_redownload(db_id, url, target_type)
            else: self.view.update_status("URL inválida.")
        elif action == 'download_visual':
            if url and url != "-": self.force_redownload_visual(db_id, url, target_type)
            else: self.view.update_status("URL inválida.")
        elif action == 'delete_extraction': self.manage_field(db_id, 'extracted_data')
        elif action == 'set_sigla': self.set_manual_sigla(db_id)

    def set_manual_sigla(self, db_id):
        from tkinter import simpledialog
        nova_sigla = simpledialog.askstring("Sigla Manual", "Digite a sigla:", parent=self.root)
        if nova_sigla is not None:
            nova_sigla = nova_sigla.strip().upper()
            if not nova_sigla: return
            try:
                self.db.update_record_details(db_id, {'sigla': nova_sigla})
                self.root.after(0, lambda: self._update_treeview_sigla(db_id, nova_sigla))
            except Exception as e: self.view.update_status(f"Erro: {e}")
           
    def _setup_commands(self):
        self.view.set_start_command(self.start_scraping)
        self.view.set_stop_command(self.stop_scraping)
        self.view.set_year_changed_command(self.update_url_preview)
        self.view.set_refresh_command(self.refresh_table_data)
        self.view.get_row_status = self.db.check_html_exists
        self.view.on_action_item = self.handle_item_action
        self.view.on_action_search = self.handle_search_page_action
        self.view.on_reprocess = self.retry_info_fetch
        self.view.on_open_search_url = self.open_generated_search_url
        self.view.on_show_sample = self.show_university_sample
        self.view.set_search_info_command(self.retry_info_fetch)
        self.view.clear_pdf_command = lambda db_id: self.manage_field(db_id, 'link_pdf')
        self.view.redownload_command = lambda db_id, url: self.force_redownload(db_id, url, 'repo' if 'bdtd.ibict' not in url else 'bdtd')
        self.view.clear_repo_command = lambda db_id: self.manage_field(db_id, 'link_repo')

    def show_university_sample(self):
        try:
            rows = self.db.fetch_one_per_university()
            self.view.clear_table()
            for row in rows: self.view.add_row(*row)
            self.view.update_status(f"Exibindo amostra: {len(rows)} universidades.")
        except Exception as e: self.view.update_status(f"Erro: {e}")
            
    def check_queue(self):
        try:
            while True:
                msg_type, content = self.msg_queue.get_nowait()
                if msg_type == 'row':
                    self.view.add_row(content.get('id', 0), content.get('termo', ''), content.get('ano', ''), 
                                      content.get('titulo', ''), content.get('autor', ''), content.get('sigla', '-'), 
                                      content.get('universidade', '-'), content.get('programa', '-'), 
                                      content.get('link_pdf', ''), content.get('link_repo', ''), content.get('link_bdtd', ''))
                elif msg_type == 'status': self.view.update_status(content)
                elif msg_type == 'done': 
                    self.stop_scraping()
                    self.view.update_status(content)
        except queue.Empty: pass
        finally: self.root.after(100, self.check_queue)
        
    def _update_treeview_sigla(self, db_id, nova_sigla):
        try:
            items = self.view.tree.get_children()
            for item in items:
                row_values = self.view.tree.item(item, 'values')
                if str(row_values[0]) == str(db_id):
                    vals = list(row_values)
                    vals[5] = nova_sigla
                    self.view.tree.item(item, values=tuple(vals))
                    break
        except Exception as e: pass
    
    def manage_field(self, db_id, field_type):
        try:
            if field_type == 'extracted_data':
                self.db.clear_field(db_id, 'extracted_data')
                self.db.clear_field(db_id, 'link_repo')
            else:
                self.db.clear_field(db_id, field_type)
            
            items = self.view.tree.get_children()
            for item in items:
                if str(self.view.tree.item(item, 'values')[0]) == str(db_id):
                    vals = list(self.view.tree.item(item, 'values'))
                    if field_type == 'extracted_data':
                        vals[5] = '-'; vals[6] = '-'; vals[7] = '-'; vals[9] = '-'
                    elif field_type == 'link_pdf': vals[8] = '-'
                    elif field_type == 'link_repo': vals[9] = '-'
                    self.view.tree.item(item, values=tuple(vals))
                    self.view.update_row_by_id(db_id, vals[5], vals[6], vals[7], vals[8])
                    break
            self.view.update_status(f"Limpo: {field_type}")
        except Exception as e: self.view.update_status(f"Erro ao limpar: {e}")