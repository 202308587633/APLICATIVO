import time
import os
import requests
import urllib3
from bs4 import BeautifulSoup
from bdtd_adapter import BDTDAdapter
import urllib.parse
import threading

# Importação APENAS da Factory
from services.parser_factory import ParserFactory 

# Suprime avisos de segurança SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class BDTDStrategy:
    def __init__(self):
        # Inicializa a factory que gerencia a escolha dos parsers
        self.factory = ParserFactory()

    def get_url(self, term, year, page_num):
        adapter = BDTDAdapter(term)
        # Opcional: restrições de assunto
        adapter.add_subject_restriction("direito")
        return adapter.get_url(page=page_num, year=year)

    def parse_from_stored_html(self, html_content, link_repo, on_progress=None):
        """
        Processa HTML já salvo no banco de dados.
        """
        if not html_content:
            return {'sigla': 'Erro', 'universidade': 'HTML vazio'}

        # A Factory decide qual parser usar baseada no link
        parser = self.factory.get_parser(link_repo)
        
        if on_progress: on_progress(f"Parser selecionado: {parser.__class__.__name__}")
        
        # Executa a extração usando o parser retornado pela factory
        return parser.extract_pure_soup(html_content, link_repo, on_progress)

    # --- Métodos Auxiliares de Parsing da Lista BDTD ---
    def _get_title(self, res):
        t = res.select_one('.title')
        return t.get_text(" ", strip=True) if t else "Sem Título"
    
    def _get_link(self, res):
        t = res.select_one('.title')
        href = t.get('href') if t else ""
        if href and not href.startswith('http'): return "https://bdtd.ibict.br" + href
        return href
    
    def _get_author(self, res):
        a = res.select_one('a[href*="/vufind/Author/"]')
        return a.get_text(strip=True) if a else "N/A"

    # --- Métodos de Rede (Requests & Selenium) ---
    def download_page(self, url, on_progress=None):
        """
        Baixa a página usando requests puro (rápido).
        """
        if on_progress: on_progress(f"Tentando conexão HTTP em: {url[:60]}...")
        try:
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            
            session = requests.Session()
            retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
            adapter = HTTPAdapter(max_retries=retry)
            session.mount('http://', adapter)
            session.mount('https://', adapter)
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            
            resp = session.get(url, headers=headers, timeout=30, verify=False)
            resp.raise_for_status()
            
            if on_progress: on_progress(f"Sucesso HTTP ({resp.status_code}).")
            return resp.url, resp.text
            
        except Exception as e:
            if on_progress: on_progress(f"Erro HTTP: {str(e)}")
            raise Exception(f"Erro HTTP: {str(e)}")

    def download_page_visual(self, url, on_progress=None):
        """
        Baixa a página usando navegador real (lento, para sites com JS/bloqueios).
        """
        if on_progress: on_progress(f"Inicializando driver visual...")
        driver = None
        try:
            from selenium import webdriver
            from selenium.webdriver.edge.options import Options as EdgeOptions
            from selenium.webdriver.edge.service import Service as EdgeService
            from webdriver_manager.microsoft import EdgeChromiumDriverManager
            
            edge_options = EdgeOptions()
            edge_options.add_argument("--start-maximized")
            edge_options.add_argument("--disable-blink-features=AutomationControlled")
            edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            # edge_options.add_argument("--headless") # Descomente para rodar oculto
            
            # O código abaixo estava falhando ao iniciar o browser
            ### service = EdgeService(EdgeChromiumDriverManager().install())
            
            # Verifica se existe o driver local na pasta atual
            driver_path = "msedgedriver.exe"
            if os.path.exists(driver_path):
                # Usa o driver local fornecido
                service = EdgeService(executable_path=os.path.abspath(driver_path))
            else:
                # Fallback: Tenta baixar se não encontrar o local
                service = EdgeService(EdgeChromiumDriverManager().install())
            
            driver = webdriver.Edge(service=service, options=edge_options)
                        
            driver.get(url)
            if on_progress: on_progress("Aguardando carregamento (10s)...")
            time.sleep(10)
            
            final_url = driver.current_url
            html = driver.page_source
            return final_url, html
            
        except Exception as e:
            raise Exception(f"Erro Visual: {str(e)}")
        finally:
            if driver: driver.quit()

    def parse(self, soup, on_progress=None):
        """
        Processa a lista de resultados da busca na BDTD.
        """
        items = []
        if not soup: return items
        
        results = soup.select('.result')
        if on_progress: on_progress(f"Encontrados {len(results)} itens.")
        
        for i, res in enumerate(results):
            try:
                titulo = self._get_title(res)
                link_bdtd = self._get_link(res)
                
                html_bdtd = ""
                html_repo = ""
                link_univ = "N/A"

                # Se houver link BDTD, tenta baixar e descobrir o repositório original
                if link_bdtd:
                    try:
                        url_final, html_content = self.download_page(link_bdtd, on_progress)
                        html_bdtd = html_content
                        
                        # Mock simples para reaproveitar a função _fetch_university_data
                        class Mock:
                            def __init__(self, u, c): self.url=u; self.content=c.encode('utf-8'); self.text=c
                        
                        link_univ, html_repo = self._fetch_university_data(Mock(url_final, html_bdtd), on_progress)
                    except: pass

                # --- PONTO CRUCIAL DA REFATORAÇÃO ---
                # Usa a Factory para obter a instância correta do parser
                parser = self.factory.get_parser(link_univ)
                
                # Executa a extração
                details = parser.extract_pure_soup(html_repo, link_univ, on_progress)
                # ------------------------------------

                items.append({
                    'titulo': titulo,
                    'autor': self._get_author(res),
                    'sigla': details.get('sigla', '-'),
                    'universidade': details.get('universidade', '-'),
                    'programa': details.get('programa', '-'),
                    'link_pdf': details.get('link_pdf', link_univ),
                    'link_repo': link_univ,
                    'link_bdtd': link_bdtd,
                    'html_bdtd': html_bdtd, 
                    'html_repo': html_repo  
                })
            except: continue
        return items

    def _fetch_university_data(self, resp_bdtd, on_progress=None):
        """
        Tenta encontrar o link do repositório original na página da BDTD.
        Ignora links que contenham 'lattes' ou 'buscatextual'.
        """
        url_bdtd = resp_bdtd.url
        
        # Validação atualizada: Ignora Lattes E Buscatextual
        def is_valid(url):
            if not url: return False
            url_lower = url.lower()
            return "lattes" not in url_lower and "buscatextual" not in url_lower

        # Caso 1: Redirecionamento direto (URL já não é BDTD)
        if "bdtd.ibict.br" not in url_bdtd:
            if is_valid(url_bdtd):
                if on_progress: on_progress("Redirecionamento externo detectado.")
                try: return self.download_page(url_bdtd, on_progress)
                except: return url_bdtd, ""
            else:
                # Se redirecionou para Lattes ou Buscatextual, ignoramos e tentamos analisar o conteúdo
                if on_progress: on_progress("Redirecionamento para link inválido (Lattes/Buscatextual) ignorado.")

        # Caso 2: Analisar HTML para achar o link
        if on_progress: on_progress("Buscando link original na BDTD...")
        try:
            soup = BeautifulSoup(resp_bdtd.content, 'html.parser')
            found_link = None
            
            # Estratégia A: Tabela de metadados
            for th in soup.find_all('th'):
                if any(x in th.get_text() for x in ["Link de acesso", "Texto completo", "URI", "Online"]):
                    td = th.find_next_sibling('td')
                    if td:
                        # Itera sobre TODOS os links da célula
                        for link in td.find_all('a', href=True):
                            href = link['href']
                            if is_valid(href):
                                found_link = href
                                break 
                    if found_link: break
            
            # Estratégia B: Botão Online (comum na interface nova)
            if not found_link:
                access = soup.select_one('.onlineUrl')
                if access:
                    for link in access.find_all('a', href=True):
                        href = link['href']
                        if is_valid(href):
                            found_link = href
                            break

            # Estratégia C: Varredura genérica em qualquer tabela
            if not found_link:
                main_table = soup.find('table', class_='table')
                if main_table:
                    for link in main_table.find_all('a', href=True):
                        href = link['href']
                        # Filtros de domínio + validação atualizada
                        if "bdtd.ibict.br" not in href and \
                           any(x in href for x in ['handle', 'bitstream', 'repositorio', '.br/']) and \
                           is_valid(href):
                            found_link = href
                            break

            if found_link:
                if on_progress: on_progress(f"Baixando repositório: {found_link[:40]}...")
                try: return self.download_page(found_link, on_progress)
                except: return found_link, ""
            
            return url_bdtd, ""
        except: return url_bdtd, ""

class GoogleStrategy:
    def get_url(self, term, year, page_num):
        start = (page_num - 1) * 10
        base = "https://www.google.com/search"
        params = {'q': f"{term} Direito", 'tbs': f'cdr:1,cd_min:{year},cd_max:{year}', 'start': start}
        return f"{base}?{urllib.parse.urlencode(params)}"

    def parse(self, soup, on_progress=None):
        results = soup.select('div.g')
        items = []
        for res in results:
            try:
                h3 = res.select_one('h3')
                if not h3: continue
                link = res.select_one('a')['href'] if res.select_one('a') else ""
                cite = res.select_one('cite')
                autor = cite.get_text(strip=True) if cite else "Google"
                
                items.append({
                    'titulo': h3.get_text(strip=True),
                    'autor': autor,
                    'sigla': 'Google',
                    'universidade': '-', 'programa': '-',
                    'link_pdf': link, 'link_bdtd': link, 'link_repo': link,
                    'html_bdtd': '', 'html_repo': ''
                })
            except: pass
        return items
    
    
