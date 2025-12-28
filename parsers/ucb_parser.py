import re
from urllib.parse import urljoin
from parsers.dspace_jspui import DSpaceJSPUIParser

class UcbParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UCB", universidade="Universidade Católica de Brasília")

    def _find_program(self, soup):
        """
        Estratégia específica para UCB.
        Foca em Breadcrumbs com termos específicos ("Stricto Sensu") e Meta Tags.
        """
        # 1. Busca nos Breadcrumbs (ol.breadcrumb)
        # A UCB usa termos como "Programa Stricto Sensu em..." que o parser padrão pode não pegar com precisão
        crumbs = soup.select('ol.breadcrumb li a')
        for crumb in crumbs:
            text = crumb.get_text(strip=True)
            # Verifica se contém "Programa" E ("Pós-Graduação" OU "Stricto Sensu")
            if "Programa" in text and ("Pós-Graduação" in text or "Stricto Sensu" in text):
                return text

        # 2. Fallback: Meta Tag DC.publisher
        meta_pub = soup.find('meta', attrs={'name': 'DC.publisher'})
        if meta_pub:
            content = meta_pub.get('content', '')
            if "Programa" in content:
                return content

        # 3. Fallback: Estratégias padrão da classe pai
        return super()._find_program(soup)

    def _clean_program_name(self, raw):
        """
        Limpeza específica para remover "Programa Stricto Sensu" antes da limpeza padrão.
        """
        # Remove "Programa Stricto Sensu" (termo específico da UCB)
        clean = re.sub(r'Programa Stricto Sensu\s*(?:em|no|na)?\s*', '', raw, flags=re.IGNORECASE)
        
        # Chama a limpeza padrão (que remove "Programa de Pós-Graduação", parênteses, etc.)
        return super()._clean_program_name(clean)

    def _find_pdf(self, soup, base_url):
        """
        Sobrescreve busca de PDF para priorizar botões específicos da interface UCB.
        """
        # 1. Busca por link com texto "Baixar/Abrir" (Padrão visual da UCB)
        link_text = soup.find('a', string=re.compile(r'Baixar/Abrir', re.I))
        if link_text and link_text.get('href'):
            return urljoin(base_url, link_text['href'])

        # 2. Busca por botão verde (classe btn-success) que aponte para PDF/Bitstream
        btn_link = soup.find('a', class_='btn-success', href=True)
        if btn_link:
            href = btn_link['href']
            if 'bitstream' in href or href.lower().endswith('.pdf'):
                return urljoin(base_url, href)

        # 3. Fallback padrão (Meta tags citation_pdf_url, links bitstream genéricos)
        return super()._find_pdf(soup, base_url)