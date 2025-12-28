from urllib.parse import urljoin
from parsers.dspace_jspui import DSpaceJSPUIParser

class UenpParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UENP", universidade="Universidade Estadual do Norte do Paraná")

    def _find_program(self, soup):
        """
        Estratégia específica para UENP (DSpace 7/Angular).
        Prioriza Breadcrumbs e blocos de metadados 'simple-view-element'.
        """
        # 1. Estratégia Breadcrumbs (DSpace 7)
        # Ex: Início > ... > Programa de Pós-Graduação em Ciência Jurídica > Dissertações
        crumbs = soup.select('ol.breadcrumb li')
        for crumb in crumbs:
            text = crumb.get_text(strip=True)
            
            # Ignora itens genéricos
            if text in ["Início", "Comunidades e Coleções"]:
                continue
            
            # Busca explícita por "Programa de Pós-Graduação"
            if "Programa de Pós-Graduação" in text:
                return text

        # 2. Estratégia Metadata Element (DSpace 7)
        # Estrutura: <div class="simple-view-element"><h5>Programa</h5><div>Valor</div></div>
        elements = soup.find_all('div', class_='simple-view-element')
        for el in elements:
            # O cabeçalho pode ser h2, h5, etc.
            header = el.find(['h2', 'h3', 'h4', 'h5'], class_='simple-view-element-header')
            if header and "Programa" in header.get_text(strip=True):
                body = el.find('div', class_='simple-view-element-body')
                if body:
                    return body.get_text(strip=True)

        # 3. Fallback: Estratégias padrão da classe pai
        return super()._find_program(soup)

    def _find_pdf(self, soup, base_url):
        """
        Sobrescreve busca de PDF para suportar links de download do DSpace 7.
        Ex: .../bitstreams/.../download
        """
        # 1. Tenta encontrar links com padrão '/bitstreams/' e '/download'
        dl_link = soup.find('a', href=lambda h: h and '/bitstreams/' in h and '/download' in h)
        if dl_link:
            return urljoin(base_url, dl_link['href'])

        # 2. Fallback: Estratégias padrão (Meta tag citation_pdf_url, links bitstream genéricos)
        return super()._find_pdf(soup, base_url)