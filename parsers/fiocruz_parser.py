from urllib.parse import urljoin
from parsers.dspace_jspui import DSpaceJSPUIParser

class FiocruzParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="FIOCRUZ", universidade="Fundação Oswaldo Cruz")

    def _find_program(self, soup):
        """
        Estratégia específica para FIOCRUZ (DSpace 7/8).
        Busca em blocos de metadados com classe 'simple-view-element' ou na seção de coleções.
        """
        # 1. Busca na estrutura de metadados do DSpace 7/8
        # Estrutura:
        # <div class="simple-view-element">
        #    <div class="simple-view-element-header">Programa</div>
        #    <div class="simple-view-element-body">Saúde Pública</div>
        # </div>
        elements = soup.find_all('div', class_='simple-view-element')
        for el in elements:
            header = el.find(class_='simple-view-element-header')
            if header and "Programa" in header.get_text():
                body = el.find(class_='simple-view-element-body')
                if body:
                    return body.get_text(strip=True)

        # 2. Fallback: Busca na seção de coleções (comum em layouts customizados)
        collection_divs = soup.find_all('div', class_='collections')
        for div in collection_divs:
            text = div.get_text(strip=True)
            if "Programa" in text or "Mestrado" in text or "Doutorado" in text:
                return text

        # 3. Fallback: Estratégias padrão da classe pai (Breadcrumbs, etc.)
        return super()._find_program(soup)

    def _find_pdf(self, soup, base_url):
        """
        Sobrescreve busca de PDF para suportar links de download do DSpace 7/8.
        """
        # 1. Tenta encontrar links de download explícitos do DSpace moderno
        # Ex: href=".../bitstreams/.../download"
        dl_link = soup.find('a', href=lambda h: h and '/bitstreams/' in h and '/download' in h)
        if dl_link:
            return urljoin(base_url, dl_link['href'])

        # 2. Fallback: Estratégias padrão (Meta tag citation_pdf_url, links bitstream genéricos)
        return super()._find_pdf(soup, base_url)