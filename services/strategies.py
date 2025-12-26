import time
import os
import time
import os
import requests
import urllib3
from bs4 import BeautifulSoup
from bdtd_adapter import BDTDAdapter
import urllib.parse

# Suprime avisos de segurança SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Importação dos Parsers
from parsers.ufop_parser import UFOPParser
from parsers.ufmt_parser import UFMTParser
from parsers.unisinos_parser import UnisinosParser
from parsers.generic_parser import GenericParser
from parsers.unifor_parser import UniforParser
from parsers.unicap_parser import UNICAPParser
from parsers.usp_parser import USPParser
from parsers.pucsp_parser import PUCSPParser
from parsers.ufg_parser import UFGParser
from parsers.uninove_parser import UninoveParser
from parsers.unb_parser import UnbParser
from parsers.ucb_parser import UCBParser
from parsers.ufpr_parser import UFPRParser
from parsers.ufsm_parser import UFSMParser
from parsers.fgv_parser import FGVParser
from parsers.unesp_parser import UNESPParser
from parsers.ufc_parser import UFCParser
from parsers.ufsc_parser import UFSCParser
from parsers.ufpa_parser import UFPAParser
from parsers.ufma_parser import UFMAParser
from parsers.uepg_parser import UEPGParser
from parsers.ufrn_parser import UFRNParser
from parsers.ufmg_parser import UFMGParser
from parsers.puccampinas import PUCCampinasParser
from parsers.fdv_parser import FDVParser
from parsers.univates_parser import UNIVATESParser
from parsers.pucrio_parser import PUCRioParser
from parsers.pucrs_parser import PUCRSParser
from parsers.uniceub_parser import UniCEUBParser
from parsers.ufjf_parser import UFJFParser
from parsers.ufpel_parser import UFPELParser
from parsers.mackenzie_parser import MackenzieParser

class BDTDStrategy:
    def __init__(self):
        # Mapeamento: Quem sabe ler cada domínio
        self._parsers = {
            "ufop.br": UFOPParser(),
            "ufmt.br": UFMTParser(),
            "unisinos.br": UnisinosParser(),
            "jesuita.org.br": UnisinosParser(), 
            "unifor.br": UniforParser(),
            "sophia.com.br": UniforParser(),
            "unicap.br": UNICAPParser(),
            "usp.br": USPParser(),
            "pucsp.br": PUCSPParser(),
            "ufg.br": UFGParser(),
            "uninove.br": UninoveParser(),
            "unb.br": UnbParser(),
            "ucb.br": UCBParser(),
            "bdtd.ucb.br": UCBParser(),
            "ufpr.br": UFPRParser(),
            "ufsm.br": UFSMParser(),
            "fgv.br": FGVParser(),
            "unesp.br": UNESPParser(),
            "ufc.br": UFCParser(),
            "ufsc.br": UFSCParser(),
            "ufpa.br": UFPAParser(),
            "ufma.br": UFMAParser(),
            "uepg.br": UEPGParser(),
            "ufrn.br": UFRNParser(),
            "ufmg.br": UFMGParser(),
            "puc-campinas.edu.br": PUCCampinasParser(),
            "/fdv/": FDVParser(),
            "univates.br": UNIVATESParser(),
            "hdl.handle.net/10737": UNIVATESParser(), # Opcional, para capturar pelo handle
            "puc-rio.br": PUCRioParser(),
            "maxwell.vrac.puc-rio.br": PUCRioParser(),
            "pucrs.br": PUCRSParser(),
            "tede2.pucrs.br": PUCRSParser(),
            "repositorio.uniceub.br": UniCEUBParser(),
            "uniceub.br": UniCEUBParser(),
            "repositorio.ufjf.br": UFJFParser(),
            "ufjf.br": UFJFParser(),
            "guaiaca.ufpel.edu.br": UFPELParser(),
            "ufpel.edu.br": UFPELParser(),
            "dspace.mackenzie.br": MackenzieParser(),
            "mackenzie.br": MackenzieParser(),
        }
        
        self._default_parser = GenericParser()

    def get_url(self, term, year, page_num):
        adapter = BDTDAdapter(term)
        adapter.add_subject_restriction("direito")
        return adapter.get_url(page=page_num, year=year)




    def parse_from_stored_html(self, html_content, link_repo, on_progress=None):
        if not html_content:
            return {'sigla': 'Erro', 'universidade': 'HTML vazio'}

        parser = self._get_specialist_parser(link_repo)
        if isinstance(parser, type): parser = parser()
        
        if on_progress: on_progress(f"Parser selecionado: {parser.__class__.__name__}")
        return parser.extract_pure_soup(html_content, link_repo, on_progress)

    def _get_title(self, res):
        t = res.select_one('.title')
        return t.get_text(" ", strip=True) if t else "Sem Título"
    
    def _get_link(self, res):
        t = res.select_one('.title')
        href = t.get('href') if t else ""
        if href and not href.startswith('http'):
            return "https://bdtd.ibict.br" + href
        return href
    
    def _get_author(self, res):
        a = res.select_one('a[href*="/vufind/Author/"]')
        return a.get_text(strip=True) if a else "N/A"

    def _get_specialist_parser(self, url):
        if not url or not isinstance(url, str): return self._default_parser
        url_lower = url.lower()
        for domain, parser in self._parsers.items():
            if domain in url_lower:
                return parser if not isinstance(parser, type) else parser()
        return self._default_parser

    def download_page(self, url, on_progress=None):
        """
        Baixa a página usando requests puro com Retry automático.
        Relata o progresso se on_progress for fornecido.
        """
        if on_progress: on_progress(f"Tentando conexão HTTP (Requests) em: {url[:60]}...")
        
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
            
            start_time = time.time()
            resp = session.get(url, headers=headers, timeout=30, verify=False)
            resp.raise_for_status()
            elapsed = time.time() - start_time
            
            if on_progress: on_progress(f"Sucesso HTTP ({resp.status_code}) em {elapsed:.2f}s. Tamanho: {len(resp.text)} bytes.")
            
            return resp.url, resp.text

        except Exception as e:
            msg = str(e)
            if on_progress: on_progress(f"Erro HTTP ao baixar {url[:30]}...: {msg}")
            raise Exception(f"Erro HTTP: {msg}")

    def download_page_visual(self, url, on_progress=None):
        """
        Abre um navegador REAL.
        Relata passos da automação visual.
        """
        if on_progress: on_progress(f"Inicializando driver visual para: {url[:50]}...")
        
        driver = None
        try:
            from selenium import webdriver
            from selenium.webdriver.edge.options import Options as EdgeOptions
            from selenium.webdriver.edge.service import Service as EdgeService
            from webdriver_manager.microsoft import EdgeChromiumDriverManager
            import os

            edge_options = EdgeOptions()
            edge_options.add_argument("--start-maximized")
            edge_options.add_argument("--no-sandbox")
            edge_options.add_argument("--disable-dev-shm-usage")
            edge_options.add_argument("--disable-gpu")
            edge_options.add_argument("--remote-allow-origins=*")
            edge_options.add_argument("--disable-blink-features=AutomationControlled")
            edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            edge_options.add_experimental_option("useAutomationExtension", False)

            # Verifica driver local
            current_folder = os.getcwd()
            local_driver = os.path.join(current_folder, "msedgedriver.exe")

            if os.path.exists(local_driver):
                if on_progress: on_progress("Usando driver local encontrado na pasta.")
                service = EdgeService(executable_path=local_driver)
            else:
                if on_progress: on_progress("Driver local não encontrado. Verificando gerenciador...")
                service = EdgeService(EdgeChromiumDriverManager().install())

            driver = webdriver.Edge(service=service, options=edge_options)

            if on_progress: on_progress("Navegador aberto. Carregando página...")
            driver.get(url)
            
            if on_progress: on_progress("Aguardando 10s para carregamento e validação de segurança...")
            time.sleep(10)
            
            final_url = driver.current_url
            html_content = driver.page_source
            
            if on_progress: on_progress(f"Conteúdo capturado. URL final: {final_url[:50]}...")
            return final_url, html_content

        except Exception as e:
            if on_progress: on_progress(f"Erro no processo visual: {str(e)}")
            msg = str(e)
            if "Could not reach host" in msg:
                msg = "Não foi possível conectar ao navegador. Feche outras janelas do Edge e tente novamente."
            elif "executable needs to be in PATH" in msg:
                 msg = "Driver não encontrado. Verifique se 'msedgedriver.exe' está na pasta do script."
            
            raise Exception(f"Erro no Navegador: {msg}")
        finally:
            if driver:
                try: 
                    driver.quit()
                    if on_progress: on_progress("Navegador fechado.")
                except: pass

    def _fetch_university_data(self, resp_bdtd, on_progress=None):
        """Tenta encontrar o link do repositório original com logs detalhados."""
    def download_page(self, url, on_progress=None):
        """
        Baixa a página usando requests puro com Retry automático.
        Relata o progresso se on_progress for fornecido.
        """
        if on_progress: on_progress(f"Tentando conexão HTTP (Requests) em: {url[:60]}...")
        
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
            
            start_time = time.time()
            resp = session.get(url, headers=headers, timeout=30, verify=False)
            resp.raise_for_status()
            elapsed = time.time() - start_time
            
            if on_progress: on_progress(f"Sucesso HTTP ({resp.status_code}) em {elapsed:.2f}s. Tamanho: {len(resp.text)} bytes.")
            
            return resp.url, resp.text

        except Exception as e:
            msg = str(e)
            if on_progress: on_progress(f"Erro HTTP ao baixar {url[:30]}...: {msg}")
            raise Exception(f"Erro HTTP: {msg}")

    def download_page_visual(self, url, on_progress=None):
        """
        Abre um navegador REAL.
        Relata passos da automação visual.
        """
        if on_progress: on_progress(f"Inicializando driver visual para: {url[:50]}...")
        
        driver = None
        try:
            from selenium import webdriver
            from selenium.webdriver.edge.options import Options as EdgeOptions
            from selenium.webdriver.edge.service import Service as EdgeService
            from webdriver_manager.microsoft import EdgeChromiumDriverManager
            import os

            edge_options = EdgeOptions()
            edge_options.add_argument("--start-maximized")
            edge_options.add_argument("--no-sandbox")
            edge_options.add_argument("--disable-dev-shm-usage")
            edge_options.add_argument("--disable-gpu")
            edge_options.add_argument("--remote-allow-origins=*")
            edge_options.add_argument("--disable-blink-features=AutomationControlled")
            edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            edge_options.add_experimental_option("useAutomationExtension", False)

            # Verifica driver local
            current_folder = os.getcwd()
            local_driver = os.path.join(current_folder, "msedgedriver.exe")

            if os.path.exists(local_driver):
                if on_progress: on_progress("Usando driver local encontrado na pasta.")
                service = EdgeService(executable_path=local_driver)
            else:
                if on_progress: on_progress("Driver local não encontrado. Verificando gerenciador...")
                service = EdgeService(EdgeChromiumDriverManager().install())

            driver = webdriver.Edge(service=service, options=edge_options)

            if on_progress: on_progress("Navegador aberto. Carregando página...")
            driver.get(url)
            
            if on_progress: on_progress("Aguardando 10s para carregamento e validação de segurança...")
            time.sleep(10)
            
            final_url = driver.current_url
            html_content = driver.page_source
            
            if on_progress: on_progress(f"Conteúdo capturado. URL final: {final_url[:50]}...")
            return final_url, html_content

        except Exception as e:
            if on_progress: on_progress(f"Erro no processo visual: {str(e)}")
            msg = str(e)
            if "Could not reach host" in msg:
                msg = "Não foi possível conectar ao navegador. Feche outras janelas do Edge e tente novamente."
            elif "executable needs to be in PATH" in msg:
                 msg = "Driver não encontrado. Verifique se 'msedgedriver.exe' está na pasta do script."
            
            raise Exception(f"Erro no Navegador: {msg}")
        finally:
            if driver:
                try: 
                    driver.quit()
                    if on_progress: on_progress("Navegador fechado.")
                except: pass

    def _fetch_university_data(self, resp_bdtd, on_progress=None):
        """Tenta encontrar o link do repositório original com logs detalhados."""
        url_bdtd = resp_bdtd.url
        
        if "bdtd.ibict.br" not in url_bdtd:
            if on_progress: on_progress("Redirecionamento externo detectado. Baixando destino...")
            try: return self.download_page(url_bdtd, on_progress)
            except: return url_bdtd, ""
            if on_progress: on_progress("Redirecionamento externo detectado. Baixando destino...")
            try: return self.download_page(url_bdtd, on_progress)
            except: return url_bdtd, ""

        if on_progress: on_progress("Analisando HTML da BDTD para encontrar link original...")
        if on_progress: on_progress("Analisando HTML da BDTD para encontrar link original...")
        try:
            inner_soup = BeautifulSoup(resp_bdtd.content, 'html.parser')
            found_link = None

            # Estratégia 1
            # Estratégia 1
            for th in inner_soup.find_all('th'):
                if any(x in th.get_text() for x in ["Link de acesso", "Texto completo", "URI", "Online"]):
                    td = th.find_next_sibling('td')
                    if td and td.find('a', href=True): 
                        found_link = td.find('a')['href']
                        if on_progress: on_progress("Link encontrado na tabela de metadados.")
                        if on_progress: on_progress("Link encontrado na tabela de metadados.")
                        break
            
            # Estratégia 2
            # Estratégia 2
            if not found_link:
                access_div = inner_soup.select_one('.onlineUrl')
                if access_div and access_div.find('a', href=True): 
                    found_link = access_div.find('a')['href']
                    if on_progress: on_progress("Link encontrado no botão de acesso.")
                    if on_progress: on_progress("Link encontrado no botão de acesso.")

            # Estratégia 3
            # Estratégia 3
            if not found_link:
                main_table = inner_soup.find('table', class_='table')
                if main_table:
                    for link in main_table.find_all('a', href=True):
                        href = link['href']
                        if "bdtd.ibict.br" not in href and any(x in href for x in ['handle', 'bitstream', 'repositorio', '.br/']):
                            found_link = href
                            if on_progress: on_progress("Link encontrado por varredura genérica.")
                            if on_progress: on_progress("Link encontrado por varredura genérica.")
                            break

            if found_link:
                if on_progress: on_progress(f"Baixando repositório original: {found_link[:60]}...")
                try: return self.download_page(found_link, on_progress)
                except: return found_link, ""
            
            if on_progress: on_progress("Nenhum link externo encontrado na BDTD.")
            return url_bdtd, ""
        except Exception as e:
            if on_progress: on_progress(f"Erro ao analisar BDTD: {str(e)}")
                if on_progress: on_progress(f"Baixando repositório original: {found_link[:60]}...")
                try: return self.download_page(found_link, on_progress)
                except: return found_link, ""
            
            if on_progress: on_progress("Nenhum link externo encontrado na BDTD.")
            return url_bdtd, ""
        except Exception as e:
            if on_progress: on_progress(f"Erro ao analisar BDTD: {str(e)}")
            return url_bdtd, ""

    def parse(self, soup, on_progress=None):
        items = []
        if not soup: return items
        
        results = soup.select('.result')
        if on_progress: on_progress(f"Encontrados {len(results)} itens na página de busca.")
        
        for i, res in enumerate(results):
            try:
                # if on_progress: on_progress(f"Processando item {i+1}/{len(results)}...") # Opcional: pode poluir muito
                titulo = self._get_title(res)
                link_bdtd = self._get_link(res)
                
                html_bdtd = ""
                html_repo = ""
                link_univ = "N/A"

                if link_bdtd:
                    try:
                        # Passa on_progress para download_page
                        url_final, html_content = self.download_page(link_bdtd, on_progress)
                        html_bdtd = html_content
                        
                        class MockResponse:
                            def __init__(self, u, c): self.url = u; self.content = c.encode('utf-8'); self.text = c
                        
                        # Passa on_progress para fetch_university_data
                        link_univ, html_repo = self._fetch_university_data(MockResponse(url_final, html_bdtd), on_progress)
                    except Exception as e:
                        if on_progress: on_progress(f"Falha ao baixar detalhes do item {i+1}: {e}")

                parser = self._get_specialist_parser(link_univ)
                if isinstance(parser, type): parser = parser()
                
                # O parser já recebe on_progress internamente em extract_pure_soup
                details = parser.extract_pure_soup(html_repo, link_univ, on_progress)

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
            except Exception as e:
                if on_progress: on_progress(f"Erro fatal no item {i+1}: {e}")
                continue
                
        return items


    def parse(self, soup, on_progress=None):
        items = []
        if not soup: return items
        
        results = soup.select('.result')
        if on_progress: on_progress(f"Encontrados {len(results)} itens na página de busca.")
        
        for i, res in enumerate(results):
            try:
                # if on_progress: on_progress(f"Processando item {i+1}/{len(results)}...") # Opcional: pode poluir muito
                titulo = self._get_title(res)
                link_bdtd = self._get_link(res)
                
                html_bdtd = ""
                html_repo = ""
                link_univ = "N/A"

                if link_bdtd:
                    try:
                        # Passa on_progress para download_page
                        url_final, html_content = self.download_page(link_bdtd, on_progress)
                        html_bdtd = html_content
                        
                        class MockResponse:
                            def __init__(self, u, c): self.url = u; self.content = c.encode('utf-8'); self.text = c
                        
                        # Passa on_progress para fetch_university_data
                        link_univ, html_repo = self._fetch_university_data(MockResponse(url_final, html_bdtd), on_progress)
                    except Exception as e:
                        if on_progress: on_progress(f"Falha ao baixar detalhes do item {i+1}: {e}")

                parser = self._get_specialist_parser(link_univ)
                if isinstance(parser, type): parser = parser()
                
                # O parser já recebe on_progress internamente em extract_pure_soup
                details = parser.extract_pure_soup(html_repo, link_univ, on_progress)

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
            except Exception as e:
                if on_progress: on_progress(f"Erro fatal no item {i+1}: {e}")
                continue
                
        return items


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
    
    
    
    