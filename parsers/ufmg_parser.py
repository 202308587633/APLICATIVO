from urllib.parse import urljoin
from parsers.dspace_jspui import DSpaceJSPUIParser

class UfmgParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UFMG", universidade="Universidade Federal de Minas Gerais")

    def _find_program(self, soup):
        """
        Estratégia específica para UFMG (DSpace 8/Angular).
        Busca o campo "Curso" dentro da estrutura 'simple-view-element'.
        """
        # 1. Busca nos blocos de metadados do DSpace 8
        # Estrutura: <h2 class="simple-view-element-header">Curso</h2> ... <div class="simple-view-element-body">Valor</div>
        headers = soup.find_all('h2', class_='simple-view-element-header')
        
        for header in headers:
            if "Curso" in header.get_text(strip=True):
                # O valor está na div irmã (body) logo após o header
                body = header.find_next_sibling('div', class_='simple-view-element-body')
                if body:
                    return body.get_text(strip=True)

        # 2. Fallback: Estratégias padrão da classe pai (Breadcrumbs, etc)
        # Embora DSpace 8 seja diferente, às vezes breadcrumbs funcionam
        return super()._find_program(soup)

    def _find_pdf(self, soup, base_url):
        """
        Sobrescreve busca de PDF para suportar links de download do DSpace 7/8.
        """
        # 1. Tenta encontrar links com padrão '/bitstreams/' e '/download'
        # Ex: href=".../bitstreams/uuid/download"
        dl_link = soup.find('a', href=lambda h: h and '/bitstreams/' in h and '/download' in h)
        if dl_link:
            return urljoin(base_url, dl_link['href'])

        # 2. Fallback: Estratégias padrão (Meta tag citation_pdf_url, links bitstream genéricos)
        return super()._find_pdf(soup, base_url)