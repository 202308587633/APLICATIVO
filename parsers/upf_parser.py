import re
from urllib.parse import urljoin
from parsers.dspace_jspui import DSpaceJSPUIParser

class UpfParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UPF", universidade="Universidade de Passo Fundo")

    def _find_program(self, soup):
        """
        Estratégia específica para UPF (DSpace 7+).
        Busca em blocos de metadados com classe 'simple-view-element'.
        """
        # 1. Busca na estrutura de metadados do DSpace 7
        # <div class="simple-view-element">
        #    <h5 class="simple-view-element-header">Programa de Pós-graduação...</h5>
        #    <div class="simple-view-element-body">...</div>
        # </div>
        elements = soup.find_all('div', class_='simple-view-element')
        for el in elements:
            header = el.find(['h2', 'h3', 'h4', 'h5'], class_='simple-view-element-header')
            if header:
                header_text = header.get_text(strip=True)
                
                # Verifica se o cabeçalho indica o programa
                if "Programa" in header_text or "Pós-graduação" in header_text:
                    body = el.find('div', class_='simple-view-element-body')
                    if body:
                        return body.get_text(strip=True)

        # 2. Fallback: Estratégias padrão da classe pai (Breadcrumbs, etc.)
        return super()._find_program(soup)

    def _find_pdf(self, soup, base_url):
        """
        Sobrescreve busca de PDF para suportar links de download do DSpace 7.
        """
        # 1. Tenta encontrar links com padrão '/bitstreams/' e '/download' (Típico DSpace 7)
        dl_link = soup.find('a', href=lambda h: h and '/bitstreams/' in h and '/download' in h)
        if dl_link:
            return urljoin(base_url, dl_link['href'])

        # 2. Fallback: Estratégias padrão (Meta tag citation_pdf_url, etc.)
        return super()._find_pdf(soup, base_url)