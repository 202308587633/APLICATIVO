import re
from parsers.dspace_jspui import DSpaceJSPUIParser

class UfpeParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UFPE", universidade="Universidade Federal de Pernambuco")

    def _find_program(self, soup):
        """
        Estratégia específica para UFPE (Attena).
        Prioriza Breadcrumbs e Meta Tags com tratamento de acentuação flexível.
        """
        # Regex flexível para "Pós-Graduação" (com ou sem acentos)
        regex_ppg = r'Programa de P(?:ó|o)s-Gradua(?:ç|c)(?:ã|a)o'

        # 1. Busca nos Breadcrumbs (ol.breadcrumb)
        crumbs = soup.select('ol.breadcrumb li')
        for crumb in crumbs:
            text = crumb.get_text(strip=True)
            if re.search(regex_ppg, text, re.IGNORECASE):
                return text

        # 2. Busca na Meta Tag DC.publisher (Comum na UFPE)
        publishers = soup.find_all('meta', attrs={'name': 'DC.publisher'})
        for meta in publishers:
            content = meta.get('content', '')
            if re.search(regex_ppg, content, re.IGNORECASE):
                return content

        # 3. Fallback: Estratégias padrão da classe pai
        return super()._find_program(soup)

    def _clean_program_name(self, raw):
        """
        Limpeza específica para remover variações de "Programa de Pós-Graduação"
        (com e sem acento) antes da limpeza padrão.
        """
        # Remove prefixo "Programa de Pós-Graduação em..." (flexible regex)
        clean = re.sub(
            r'Programa de P(?:ó|o)s-Gradua(?:ç|c)(?:ã|a)o (?:em|no|na)?\s*', 
            '', 
            raw, 
            flags=re.IGNORECASE
        )
        
        # Envia para a limpeza padrão (remove parênteses finais, espaços extras, etc.)
        return super()._clean_program_name(clean)