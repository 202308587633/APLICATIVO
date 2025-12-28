from database import ScraperDB
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
        from view import ScraperView
        from model import ScraperModel
        from database import ScraperDB

        self.view = ScraperView(root)
        self.model = ScraperModel()
        self.db = ScraperDB()
        self.msg_queue = queue.Queue()
        self.is_running = False 
        
        self._setup_commands()
        self.update_url_preview()
        self.load_initial_data()
        self.check_queue()

    def handle_search_page_action(self, action, meta):
        """Gerencia ações para a Página de Busca (Lista)."""
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
        """Helper para salvar string HTML em arquivo temp e abrir no navegador."""
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
        """Loop principal de raspagem com suporte a salvamento da página de busca."""
        strategy = BDTDStrategy() if data['engine'] == "BDTD" else GoogleStrategy()
        page = 1
        total = 0

        def log(msg): self.msg_queue.put(('status', msg))

        try:
            while self.is_running:
                log(f"--- Processando Página {page} ---")

                # Captura Itens, Mensagem e HTML da Busca
                items, msg, search_html = self.model.fetch(strategy, data['term'], data['year'], page, on_progress=log)

                # Salva a página de listagem (HTML da busca) no banco
                if search_html:
                    self.db.save_search_page(data['engine'], data['term'], data['year'], page, search_html)
                    # Opcional: log(f"HTML da busca pág {page} salvo.")

                if not items: 
                    self.msg_queue.put(('done', f"Fim. {msg} Total coletado: {total}"))
                    break

                for item in items:
                    if not self.is_running: break
                    item['termo'] = data['term']
                    item['ano'] = data['year']
                    item['pagina'] = page
                    
                    # Salva no banco
                    item['id'] = self.db.save(item)
                    
                    # Envia para a interface
                    self.msg_queue.put(('row', item))
                    total += 1

                page += 1

        except Exception as e:
            self.msg_queue.put(('done', f"Erro Crítico: {e}"))

    def load_initial_data(self):
        try:
            registros = self.db.fetch_all()
            for row in registros: self.view.add_row(*row)
            if registros: self.view.update_status(f"Histórico: {len(registros)}.")
        except Exception as e: self.view.update_status(f"Erro DB: {e}")

    def refresh_table_data(self):
        self.view.clear_table()
        self.load_initial_data()
        self.view.update_status("Atualizado.")

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

    def handle_search_page_action(self, action, meta):
        """Gerencia ações para a página de listagem (busca)."""
        termo, ano, pagina = meta['termo'], meta['ano'], meta['pagina']
        
        if action == 'view':
            html = self.db.get_search_page(termo, ano, pagina)
            if html: 
                self._open_html_text(html, f"busca_{termo}_{pagina}")
            else: 
                self.view.update_status("HTML da busca não encontrado no banco.")
            
        elif action == 'delete':
            self.db.delete_search_page(termo, ano, pagina)
            self.view.update_status(f"HTML da busca (Pág {pagina}) apagado.")
            
        elif action == 'download':
            self._redownload_search_page(termo, ano, pagina)

    def open_generated_search_url(self, meta):
        """Recontrói a URL da busca original e abre no navegador."""
        try:
            termo, ano, pagina = meta['termo'], meta['ano'], meta['pagina']
            
            # Recria a estratégia para obter a URL correta (Assume BDTD por padrão)
            # Se quiser suportar Google, precisaria passar 'engine' no meta
            strategy = BDTDStrategy() 
            url = strategy.get_url(termo, ano, pagina)
            
            webbrowser.open(url)
            self.view.update_status(f"Abrindo lista no navegador: Pág {pagina}")
        except Exception as e:
            self.view.update_status(f"Erro ao gerar URL: {e}")
            
            
            ############################################
            
    def open_generated_search_url(self, meta):
        """Recontrói a URL da busca original e abre no navegador."""
        try:
            termo, ano, pagina = meta['termo'], meta['ano'], meta['pagina']
            
            # Recria a estratégia para obter a URL correta (Assume BDTD por padrão)
            # Se quiser suportar Google, precisaria passar 'engine' no meta
            strategy = BDTDStrategy() 
            url = strategy.get_url(termo, ano, pagina)
            
            webbrowser.open(url)
            self.view.update_status(f"Abrindo lista no navegador: Pág {pagina}")
        except Exception as e:
            self.view.update_status(f"Erro ao gerar URL: {e}")
            
            
            ############################################
            
    def _redownload_search_page(self, termo, ano, pagina):
        """Baixa novamente a página de listagem da busca."""
        def _task():
            try:
                # Assume BDTD pois GoogleStrategy é mais complexa de reconstruir url fixa
                from services.strategies import BDTDStrategy
                from services.strategies import BDTDStrategy
                strategy = BDTDStrategy()
                url = strategy.get_url(termo, ano, pagina)
                
                self.root.after(0, lambda: self.view.update_status(f"Baixando lista: {url[:40]}..."))
                
                headers = {'User-Agent': 'Mozilla/5.0'}
                resp = requests.get(url, headers=headers, timeout=20, verify=False)
                
                if resp.status_code == 200:
                    self.db.save_search_page("BDTD", termo, ano, pagina, resp.text)
                    self.root.after(0, lambda: self.view.update_status(f"Lista (Pág {pagina}) atualizada com sucesso!"))
                else:
                    self.root.after(0, lambda: self.view.update_status(f"Erro HTTP {resp.status_code} ao baixar lista"))
            except Exception as e:
                # CORREÇÃO: Mesma correção de escopo aplicada aqui preventivamente
                error_msg = f"Erro download busca: {e}"
                self.root.after(0, lambda: self.view.update_status(error_msg))
        
        threading.Thread(target=_task, daemon=True).start()
 
    def _ask_visual_download(self, db_id, url, target_type, reason=None):
        """
        Pergunta ao usuário se deseja abrir o navegador para capturar o link.
        Usado quando o download falha ou quando a extração de dados retorna vazia.
        """
        from tkinter import messagebox
        
        # Mensagem padrão ou personalizada pelo motivo do erro
        msg_base = reason if reason else "O download padrão falhou ou retornou vazio."
        msg_final = f"{msg_base}\n\nDeseja abrir o navegador para capturar este item manualmente?\n(O navegador abrirá, aguardará o carregamento e fechará sozinho)"
        
        # A caixa de diálogo deve rodar na thread principal
        if messagebox.askyesno("Captura Visual Necessária", msg_final):
            self.force_redownload_visual(db_id, url, target_type)
        else:
            self.view.update_status(f"[ID {db_id}] Captura visual cancelada pelo usuário.")
            
    def force_redownload(self, db_id, url_alvo, target_type):
        """
        Baixa o HTML novamente (MÉTODO RÁPIDO/PADRÃO).
        Logs detalhados e tratamento seguro de erros.
        """
        def _task():
            # Função auxiliar para logar na thread principal de forma segura
            def log(msg):
                self.root.after(0, lambda: self.view.update_status(f"[ID {db_id}] {msg}"))

            try:
                log(f"Iniciando download rápido ({target_type})...")
                
                from services.strategies import BDTDStrategy
                strategy = BDTDStrategy()
                
                # Passa a função de log para acompanhar o progresso interno
                final_url, html_content = strategy.download_page(url_alvo, on_progress=log)
                
                if html_content and len(html_content) > 500:
                    log("Conteúdo baixado. Salvando no banco...")
                    self.db.update_specific_html(
                        db_id, 
                        target_type, 
                        html_content, 
                        final_url if target_type == 'repo' else None
                    )
                    
                    log("Download concluído com sucesso!")
                    
                    if target_type == 'repo':
                        log("Iniciando tentativa de extração de dados...")
                        self.retry_info_fetch(db_id, final_url or url_alvo)
                else:
                    log("AVISO: Conteúdo vazio ou muito curto. Possível bloqueio.")
                    self.root.after(0, lambda: self._ask_visual_download(db_id, url_alvo, target_type, "Conteúdo vazio."))

            except Exception as e:
                # CORREÇÃO DE ESCOPO: Converte o erro para string imediatamente
                erro_txt = str(e)
                log(f"Falha no download rápido: {erro_txt}")
                self.root.after(0, lambda: self._ask_visual_download(db_id, url_alvo, target_type, erro_txt))
        
        threading.Thread(target=_task, daemon=True).start()

    def force_redownload_visual(self, db_id, url_alvo, target_type):
        """
        Abre o navegador, espera, captura e fecha (MÉTODO VISUAL).
        Correção do erro 'NameError' aplicada aqui.
        """
        def _task():
            def log(msg):
                self.root.after(0, lambda: self.view.update_status(f"[ID {db_id}] [Visual] {msg}"))

            try:
                log("Preparando navegador...")
                
                from services.strategies import BDTDStrategy
                strategy = BDTDStrategy()
                
                # Passa log para ver etapas do Selenium (abertura, espera, captura)
                final_url, html_content = strategy.download_page_visual(url_alvo, on_progress=log)
                
                if html_content and len(html_content) > 500:
                    log("HTML capturado. Salvando...")
                    self.db.update_specific_html(
                        db_id, 
                        target_type, 
                        html_content, 
                        final_url if target_type == 'repo' else None
                    )
                    
                    log("Sucesso! O HTML foi atualizado no banco.")
                    
                    if target_type == 'repo':
                        self.retry_info_fetch(db_id, final_url or url_alvo)
                else:
                    log("Erro: O navegador retornou conteúdo vazio/inválido.")

            except Exception as e:
                # CORREÇÃO DE ESCOPO: Salva a mensagem de erro em variável local
                # Isso impede o erro 'cannot access free variable e'
                erro_msg = str(e)
                log(f"Falha Crítica: {erro_msg}")

        threading.Thread(target=_task, daemon=True).start()

    def retry_info_fetch(self, db_id, link_repo):
        """
        Tenta extrair dados do HTML salvo.
        """
        def _task():
            def log(m): self.root.after(0, lambda: self.view.update_status(f"[ID {db_id}] {m}"))
            
            log("Analisando HTML salvo...")
            
            html = self.db.get_specific_html(db_id, 'repo')
            if not html: 
                log("HTML não encontrado. Iniciando download...")
                self.force_redownload(db_id, link_repo, 'repo')
                return

            from services.strategies import BDTDStrategy
            strat = BDTDStrategy()
            
            # Extrai dados (passando log para ver qual parser está sendo usado)
            data = strat.parse_from_stored_html(html, link_repo, on_progress=log)
            
            univ = data.get('universidade')
            # Verifica se a extração falhou (indicando bloqueio ou HTML ruim)
            if not univ or univ in ['-', 'None', 'N/A']:
                log("Falha na extração (Universidade não detectada).")
                self.root.after(0, lambda: self._ask_visual_download(
                    db_id, 
                    link_repo, 
                    'repo', 
                    reason="A extração falhou. O HTML pode estar bloqueado."
                ))
            else:
                log(f"Dados extraídos: {data.get('sigla')} - {data.get('programa')}")

            # Fallback UFPR
            if (not data.get('sigla') or data.get('sigla') == '-') and link_repo and '.ufpr.' in link_repo.lower():
                data['sigla'] = 'UFPR'
                data['universidade'] = 'Universidade Federal do Paraná'
            
            self.db.update_record_details(db_id, data)
            
            self.root.after(0, lambda: self.view.update_row_by_id(
                db_id, data.get('sigla'), data.get('universidade'), data.get('programa'), data.get('link_pdf')
            ))
            
        threading.Thread(target=_task, daemon=True).start()
            
    def handle_item_action(self, action, db_id, target_type, url=None):
        """
        Gerencia ações para itens individuais (BDTD ou Repositório).
        """
        if action == 'view':
            self.open_stored_html(db_id, target_type)
        elif action == 'delete':
            self.manage_field(db_id, f'html_{target_type}')
        elif action == 'download':
            if url and url != "-":
                self.force_redownload(db_id, url, target_type)
            else:
                self.view.update_status(f"URL inválida para baixar {target_type}")
        elif action == 'download_visual':
            if url and url != "-":
                self.force_redownload_visual(db_id, url, target_type)
            else:
                self.view.update_status(f"URL inválida.")
        elif action == 'delete_extraction':
            self.manage_field(db_id, 'extracted_data')
        
        # --- COMANDO PARA DEFINIR SIGLA MANUALMENTE ---
        elif action == 'set_sigla':
            self.set_manual_sigla(db_id)

    def set_manual_sigla(self, db_id):
        """
        Abre um diálogo para o usuário digitar a sigla manualmente
        e atualiza o registro no banco de dados e na interface visual.
        """
        from tkinter import simpledialog
        
        # Abre a caixa de entrada
        nova_sigla = simpledialog.askstring(
            "Definir Sigla Manualmente", 
            "Digite a sigla da universidade (ex: USP, UFRJ):",
            parent=self.root
        )
        
        if nova_sigla is not None:  # Verifica se não foi cancelado (pode ser string vazia)
            nova_sigla = nova_sigla.strip().upper() 
            if not nova_sigla: return # Se digitou vazio, ignora
            
            try:
                # 1. Atualiza no Banco de Dados
                self.db.update_record_details(db_id, {'sigla': nova_sigla})
                
                # 2. Atualiza a Interface (Treeview)
                # Garante que roda na thread principal da interface
                self.root.after(0, lambda: self._update_treeview_sigla(db_id, nova_sigla))
                
            except Exception as e:
                self.view.update_status(f"Erro ao atualizar sigla: {e}")
           
    def _setup_commands(self):
        """Conecta os botões e eventos da View às funções do Controller."""
        self.view.set_start_command(self.start_scraping)
        self.view.set_stop_command(self.stop_scraping)
        self.view.set_year_changed_command(self.update_url_preview)
        self.view.set_refresh_command(self.refresh_table_data)
        
        # --- CONEXÕES DO MENU DE CONTEXTO ---
        self.view.get_row_status = self.db.check_html_exists
        self.view.on_action_item = self.handle_item_action
        self.view.on_action_search = self.handle_search_page_action
        self.view.on_reprocess = self.retry_info_fetch
        
        # Conecta a ação de abrir a URL da lista (recálculo de URL)
        self.view.on_open_search_url = self.open_generated_search_url
        
        # --- NOVO: Conecta o botão de amostra ---
        self.view.on_show_sample = self.show_university_sample
        
        # Callbacks de compatibilidade/legado
        self.view.set_search_info_command(self.retry_info_fetch)
        self.view.clear_pdf_command = lambda db_id: self.manage_field(db_id, 'link_pdf')
        self.view.redownload_command = lambda db_id, url: self.force_redownload(db_id, url, 'repo' if 'bdtd.ibict' not in url else 'bdtd')
        self.view.clear_repo_command = lambda db_id: self.manage_field(db_id, 'link_repo')

    def show_university_sample(self):
        """
        Carrega na tabela apenas um registro de cada universidade.
        """
        try:
            # Busca os dados agrupados do banco (Requer método no database.py)
            rows = self.db.fetch_one_per_university()
            
            # Limpa a tabela e o cache de dados da view
            self.view.clear_table()
            
            # Reinsere os dados filtrados usando o método da view
            # Isso garante que a lista interna 'all_data' da view seja atualizada,
            # permitindo que os filtros de texto funcionem sobre essa amostra
            for row in rows:
                self.view.add_row(*row)
            
            self.view.update_status(f"Exibindo amostra: {len(rows)} universidades únicas.")
            
        except Exception as e:
            self.view.update_status(f"Erro ao filtrar amostra: {e}")
            
    def check_queue(self):
        try:
            while True:
                msg_type, content = self.msg_queue.get_nowait()
                if msg_type == 'row':
                    # ATUALIZAÇÃO: Incluído 'ano' na 3ª posição (índice 2)
                    self.view.add_row(
                        content.get('id', 0), 
                        content.get('termo', ''), 
                        content.get('ano', ''),       # <--- CAMPO NOVO
                        content.get('titulo', ''), 
                        content.get('autor', ''), 
                        content.get('sigla', '-'), 
                        content.get('universidade', '-'),
                        content.get('programa', '-'), 
                        content.get('link_pdf', ''), 
                        content.get('link_repo', ''), 
                        content.get('link_bdtd', '')
                    )
                elif msg_type == 'status': self.view.update_status(content)
                elif msg_type == 'done': 
                    self.stop_scraping()
                    self.view.update_status(content)
        except queue.Empty: pass
        finally: self.root.after(100, self.check_queue)
        
    def _update_treeview_sigla(self, db_id, nova_sigla):
        """
        Função auxiliar interna para atualizar a linha específica da tabela.
        """
        try:
            items = self.view.tree.get_children()
            target_item = None
            
            # Procura a linha correspondente ao ID do banco
            for item in items:
                row_values = self.view.tree.item(item, 'values')
                if str(row_values[0]) == str(db_id):
                    target_item = item
                    break
            
            if target_item:
                vals = list(self.view.tree.item(target_item, 'values'))
                
                # ATUALIZAÇÃO: O índice da coluna 'Sigla' agora é 5 (era 4)
                if len(vals) > 5:
                    vals[5] = nova_sigla
                    
                    self.view.tree.item(target_item, values=tuple(vals))
                    self.view.update_status(f"Sigla do ID {db_id} atualizada para '{nova_sigla}'.")
                else:
                    self.view.update_status("Erro: Estrutura da tabela inesperada.")
            else:
                self.view.update_status("Erro: Item não encontrado na tabela para atualização visual.")
                
        except Exception as e:
            self.view.update_status(f"Erro visual ao atualizar sigla: {e}")
    
    def manage_field(self, db_id, field_type):
        """Limpa campos no banco e atualiza imediatamente a interface."""
        try:
            self.db.clear_field(db_id, field_type)
            
            # Busca o item na Treeview para atualizar visualmente
            items = self.view.tree.get_children()
            target_item = None
            for item in items:
                if str(self.view.tree.item(item, 'values')[0]) == str(db_id):
                    target_item = item
                    break
            
            if target_item:
                vals = list(self.view.tree.item(target_item, 'values'))
                
                # ATUALIZAÇÃO DOS ÍNDICES (Confirmando):
                # 0:id, 1:termo, 2:ano, 3:titulo, 4:autor
                # 5:sigla, 6:univ, 7:prog, 8:pdf, 9:repo, 10:bdtd
                
                if field_type == 'extracted_data':
                    vals[5] = '-' # Sigla (Índice 5)
                    vals[6] = '-' # Universidade (Índice 6)
                    vals[7] = '-' # Programa (Índice 7)
                elif field_type == 'link_pdf':
                    vals[8] = '-' # Coluna PDF (Índice 8)
                elif field_type == 'link_repo':
                    vals[9] = '-' # Coluna Repo (Índice 9)
                
                # Aplica os novos valores na linha
                self.view.tree.item(target_item, values=tuple(vals))
                
                # Atualiza também o cache da view para persistência visual
                self.view.update_row_by_id(db_id, vals[5], vals[6], vals[7], vals[8])
            
            self.view.update_status(f"Limpo com sucesso: {field_type}")
        except Exception as e:
            self.view.update_status(f"Erro ao limpar {field_type}: {e}")