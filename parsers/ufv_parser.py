import re
from urllib.parse import urljoin
from parsers.dspace_jspui import DSpaceJSPUIParser

class UfvParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UFV", universidade="Universidade Federal de Viçosa")

    def _find_program(self, soup):
        """
        Estratégia específica para UFV (Locus - DSpace 8).
        Busca em blocos 'simple-view-element', com foco em extrair do campo 'Citação'.
        """
        # 1. Iterar sobre os elementos de visualização do DSpace 8
        elements = soup.find_all('div', class_='simple-view-element')
        
        for el in elements:
            header = el.find(['h2', 'h3', 'h4', 'h5'], class_='simple-view-element-header')
            if not header:
                continue
            
            header_text = header.get_text(strip=True).lower()
            body = el.find('div', class_='simple-view-element-body')
            
            if not body:
                continue
            
            content_text = body.get_text(strip=True)

            # Estratégia A: Campo "Citação" (Muito comum na UFV)
            # Ex: "... Tese (Doutorado em Economia Doméstica) ..."
            if 'citação' in header_text:
                # Regex para capturar o programa dentro da citação
                # Procura por "Mestrado/Doutorado em XXXXX" até encontrar ')' ou '-'
                match = re.search(
                    r'(?:Mestrado|Doutorado|Mestre|Doutor)(?:\s+Profissional|\s+Acadêmico)?\s+em\s+([^)\-]+)', 
                    content_text, 
                    re.IGNORECASE
                )
                if match:
                    return match.group(1).strip()
            
            # Estratégia B: Campo Explícito "Programa" ou "Titulação"
            elif 'programa' in header_text or 'titulação' in header_text:
                return content_text

        # 2. Fallback: Estratégias padrão da classe pai (Meta tags, etc.)
        return super()._find_program(soup)

    def _find_pdf(self, soup, base_url):
        """
        Sobrescreve busca de PDF para suportar links de download do DSpace 8.
        Ex: .../bitstreams/.../download
        """
        # 1. Tenta encontrar links com padrão '/bitstreams/' e '/download'
        dl_link = soup.find('a', href=lambda h: h and '/bitstreams/' in h and '/download' in h)
        if dl_link:
            return urljoin(base_url, dl_link['href'])

        # 2. Fallback: Estratégias padrão (Meta tag citation_pdf_url, links bitstream genéricos)
        return super()._find_pdf(soup, base_url)