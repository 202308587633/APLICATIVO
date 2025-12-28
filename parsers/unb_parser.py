import re
from parsers.dspace_jspui import DSpaceJSPUIParser

class UnbParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UNB", universidade="Universidade de Brasília")

    def _find_program(self, soup):
        """
        Estratégia específica para UNB.
        Prioriza Meta Tags (DC.publisher) e Links explícitos na interface.
        """
        # 1. Estratégia de Meta Tags (Forte na UnB)
        # O repositório da UnB costuma preencher 'DC.publisher' com o nome do programa
        metas = soup.find_all('meta', attrs={'name': ['DC.publisher', 'citation_publisher']})
        for meta in metas:
            content = meta.get('content', '')
            # Filtra para não pegar apenas "Universidade de Brasília"
            if "Programa" in content or "Pós-Graduação" in content:
                # Evita falsos positivos muito curtos
                if len(content) > 10: 
                    return content

        # 2. Estratégia de Link explícito
        # Procura links que contenham "Programa de Pós-Graduação" no texto
        prog_link = soup.find('a', string=re.compile(r'Programa de Pós-[Gg]raduação', re.I))
        if prog_link:
            return prog_link.get_text(strip=True)

        # 3. Fallback: Estratégias padrão da classe pai (Tabela de metadados, Breadcrumbs)
        return super()._find_program(soup)

    def _clean_program_name(self, raw):
        """
        Limpeza específica para UnB antes da limpeza padrão.
        """
        # Remove prefixos institucionais se aparecerem junto com o programa
        # Ex: "Universidade de Brasília, Programa de Pós-Graduação em História"
        clean = re.sub(r'^Universidade de Brasília[.,-]?\s*', '', raw, flags=re.IGNORECASE)
        
        # Chama a limpeza padrão (que remove "Programa de Pós-Graduação em", etc.)
        return super()._clean_program_name(clean)