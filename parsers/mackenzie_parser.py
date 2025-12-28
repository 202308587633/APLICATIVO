from urllib.parse import urljoin
from parsers.dspace_jspui import DSpaceJSPUIParser

class MackenzieParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="MACKENZIE", universidade="Universidade Presbiteriana Mackenzie")

    def _find_program(self, soup):
        """
        Estratégia específica para MACKENZIE (DSpace 7/Angular).
        Prioriza Breadcrumbs com formatação específica e blocos de metadados.
        """
        # 1. Estratégia Breadcrumbs (Específica do Mackenzie)
        # Ex: "Direito Político e Econômico - Dissertações - Direito Higienópolis"
        crumbs = soup.select('ol.breadcrumb li')
        for crumb in crumbs:
            text = crumb.get_text(strip=True)
            
            # Ignora itens genéricos
            if text in ["Início", "Faculdade de Direito", "Dissertações", "Teses"]:
                continue
            
            # Tenta identificar o nome do programa. Geralmente contém "Direito" ou "Programa"
            if "Direito" in text or "Programa" in text:
                # Limpeza específica: Pega apenas a parte antes do primeiro hífen " - "
                prog_candidate = text.split(' - ')[0].strip()
                
                # Validação para evitar falsos positivos
                if len(prog_candidate) > 5 and prog_candidate != "Faculdade de Direito":
                    return prog_candidate

        # 2. Estratégia Metadata Element (DSpace 7)
        # Estrutura: <h2 ...>Programa</h2> ... <div ...>Direito Político e Econômico</div>
        elements = soup.find_all('div', class_='simple-view-element')
        for el in elements:
            header = el.find(['h2', 'h3', 'h4', 'h5'], class_='simple-view-element-header')
            if header and "Programa" in header.get_text(strip=True):
                body = el.find('div', class_='simple-view-element-body')
                if body:
                    return body.get_text(strip=True)

        # 3. Fallback: Estratégias padrão da classe pai
        return super()._find_program(soup)

    def _find_pdf(self, soup, base_url):
        """
        Sobrescreve busca de PDF para suportar links de download do DSpace 7 (Angular).
        Links terminam em '/download' em vez de '.pdf'.
        """
        # 1. Tenta encontrar links com padrão '/bitstreams/' e '/download'
        dl_link = soup.find('a', href=lambda h: h and '/bitstreams/' in h and '/download' in h)
        if dl_link:
            return urljoin(base_url, dl_link['href'])

        # 2. Fallback: Estratégias padrão (Meta tag citation_pdf_url, links bitstream genéricos)
        return super()._find_pdf(soup, base_url)