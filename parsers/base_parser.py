import requests
from bs4 import BeautifulSoup

class BaseParser:
    """
    Classe base que define o comportamento padrão para todos os parsers de universidades.
    Implementa a filosofia 'Small is Beautiful' centralizando o download e 
    padronizando a extração.
    """
    
    def __init__(self, sigla="-", universidade="Desconhecida"):
        self.sigla = sigla
        self.universidade = universidade

    def fetch_and_extract(self, url, on_progress=None):
        data = self._get_default_data(url)
        if not url or not url.startswith("http"): return data

        try:
            if on_progress: on_progress(f"Iniciando download em {self.sigla}...")
            
            # Usa o serviço de rede (opcional: instanciar ou passar por parâmetro)
            from services.networking import NetworkingService
            resp = NetworkingService().get(url, on_progress=on_progress)
            
            if resp.status_code == 200:
                if on_progress: on_progress(f"Extraindo metadados de {self.sigla}...")
                data['html_source'] = resp.text
                extracted = self.extract_pure_soup(resp.text, url, on_progress)
                data.update(extracted)
            else:
                if on_progress: on_progress(f"Falha: Status {resp.status_code}")
        except Exception as e:
            if on_progress: on_progress(f"Erro em {self.sigla}: {str(e)[:20]}")
            
        return data

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Este método deve ser sobrescrito pelos parsers filhos.
        Realiza apenas o parsing do HTML (Modo Offline/Banco).
        """
        raise NotImplementedError("Os parsers filhos devem implementar o método extract_pure_soup")

    def _get_default_data(self, url):
        """Subfunção utilitária para manter o dicionário padronizado."""
        return {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': url,
            'html_source': ''
        }

    # --- Subfunções utilitárias comuns a todos os parsers ---
    
    def _find_pdf_meta(self, soup):
        """Tenta encontrar o PDF pela meta tag padrão citation_pdf_url."""
        pdf_tag = soup.find('meta', attrs={'name': 'citation_pdf_url'})
        return pdf_tag.get('content') if pdf_tag else None

    def _find_pdf_by_link(self, soup, url_base):
        """Busca exaustiva por links que terminam em .pdf no corpo do HTML."""
        for a in soup.find_all('a', href=True):
            href = a['href'].lower()
            if href.endswith('.pdf') or 'bitstream' in href:
                if not href.startswith('http'):
                    # Constrói URL absoluta se for relativa
                    return requests.compat.urljoin(url_base, a['href'])
                return a['href']
        return None