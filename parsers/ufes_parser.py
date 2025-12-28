import re
from urllib.parse import urljoin
from parsers.dspace_jspui import DSpaceJSPUIParser

class UfesParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UFES", universidade="Universidade Federal do Espírito Santo")

    def _find_program(self, soup):
        """
        Estratégia específica para UFES (DSpace 7 Angular).
        O programa geralmente aparece na seção "Coleções" ou nos Breadcrumbs.
        Ex: "Mestrado em Direito Processual"
        """
        # 1. Estratégia Breadcrumbs
        crumbs = soup.select('ol.breadcrumb li')
        for crumb in crumbs:
            text = crumb.get_text(strip=True)
            # DSpace 7 costuma ter "Mestrado em..." ou "Doutorado em..." nos crumbs
            if re.match(r'^(?:Mestrado|Doutorado) (?:em|no|na)\s+', text, re.IGNORECASE):
                return text

        # 2. Estratégia Metadado da Coleção (presente na UFES como link)
        # Ex: <a href="/collections/...">Mestrado em Direito Processual</a>
        # O DSpace Angular renderiza isso em listas de coleções no rodapé do item.
        collections_links = soup.select('ds-item-page-collections a')
        for link in collections_links:
            text = link.get_text(strip=True)
            if "Mestrado" in text or "Doutorado" in text:
                return text

        # 3. Fallback: Padrão da classe pai
        return super()._find_program(soup)

    def _clean_program_name(self, raw):
        """
        Limpeza específica para UFES.
        Remove "Mestrado em", "Programa de Pós-Graduação em", etc.
        """
        # Remove "Programa de Pós-Graduação em/no/na"
        clean = re.sub(r'Programa de Pós-Graduação (?:em|no|na)\s+', '', raw, flags=re.IGNORECASE)
        
        # Remove "Mestrado/Doutorado em/no/na" (Muito comum na UFES)
        clean = re.sub(r'^(?:Mestrado|Doutorado) (?:em|no|na)\s+', '', clean, flags=re.IGNORECASE)

        # Chama a limpeza padrão
        return super()._clean_program_name(clean)

    def _find_pdf(self, soup, base_url):
        """
        Adaptação para DSpace 7 Angular.
        """
        # 1. Tenta citation_pdf_url (Geralmente presente no cabeçalho)
        pdf = super()._find_pdf(soup, base_url)
        if pdf:
            return pdf

        # 2. Busca links de download explícitos do Angular
        dl_link = soup.find('a', href=lambda h: h and '/bitstreams/' in h and '/download' in h)
        if dl_link:
            return urljoin(base_url, dl_link['href'])

        return None