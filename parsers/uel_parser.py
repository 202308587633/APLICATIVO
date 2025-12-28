import re
from urllib.parse import urljoin
from parsers.dspace_jspui import DSpaceJSPUIParser

class UelParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UEL", universidade="Universidade Estadual de Londrina")

    def _find_program(self, soup):
        """
        Estratégia específica para UEL (DSpace 7/Angular).
        O programa geralmente está no Breadcrumb da coleção, formatado como:
        "02 - Mestrado - Direito Negocial" ou "02 - - Direito Negocial".
        """
        # 1. Estratégia Breadcrumbs (Mais confiável no layout UEL)
        # Procura por itens que começam com dígitos seguidos de hífen (Ex: "02 - ...")
        crumbs = soup.select('ol.breadcrumb li')
        for crumb in crumbs:
            text = crumb.get_text(strip=True)
            
            # Padrão da UEL: Começa com número e hífen (Ex: "02 - ")
            if re.match(r'^\d+\s*-', text):
                return text

        # 2. Fallback: Meta Tags
        # A UEL tem 'dc.relation.ppgname' no JSON de estado, mas nem sempre exposto no HTML puro.
        # Tentamos o padrão
        return super()._find_program(soup)

    def _clean_program_name(self, raw):
        """
        Limpeza específica para UEL.
        Resolve casos como "02 - - Direito Negocial" ou "02 - Mestrado - Direito".
        """
        # 1. Remove números iniciais seguidos de hífen (Ex: "02 - ")
        clean = re.sub(r'^\d+\s*-\s*', '', raw)
        
        # 2. Remove níveis acadêmicos seguidos de hífen (Ex: "Mestrado - ")
        clean = re.sub(r'^(?:Mestrado|Doutorado)(?:\s+Profissional|\s+Acadêmico)?\s*-\s*', '', clean, flags=re.IGNORECASE)

        # 3. Remove hífens residuais no início (Ex: "- Direito Negocial" -> "Direito Negocial")
        # Isso corrige o caso "02 - - Direito Negocial"
        clean = re.sub(r'^[\s-]*', '', clean)

        # Chama a limpeza padrão (remove "Programa de Pós-Graduação", etc.)
        return super()._clean_program_name(clean)

    def _find_pdf(self, soup, base_url):
        """
        Adaptação para DSpace 7 Angular.
        """
        # 1. Tenta citation_pdf_url (Geralmente presente e correto no header)
        pdf = super()._find_pdf(soup, base_url)
        if pdf:
            return pdf

        # 2. Busca links de download explícitos do Angular
        dl_link = soup.find('a', href=lambda h: h and '/bitstreams/' in h and '/download' in h)
        if dl_link:
            return urljoin(base_url, dl_link['href'])

        return None