import re
from parsers.dspace_jspui import DSpaceJSPUIParser

class UfpelParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UFPEL", universidade="Universidade Federal de Pelotas")

    def _find_program(self, soup):
        """
        Estratégia específica para UFPEL (Guaiaca).
        Prioriza Meta Tags e labels específicos na tabela de metadados.
        """
        # 1. Busca por Meta Tags (DC.publisher)
        # O Guaiaca costuma preencher este campo com o nome do programa.
        publishers = soup.find_all('meta', attrs={'name': 'DC.publisher'})
        for meta in publishers:
            content = meta.get('content', '')
            # Filtra para garantir que é um programa e não apenas o nome da universidade
            if "Programa" in content or "Pós-Graduação" in content:
                return content

        # 2. Busca por label explícito na tabela de metadados
        # Ex: "Programa de Pós-Graduação:"
        prog = self._try_metadata_table_label(soup, label_pattern=r'^Programa')
        if prog:
            return prog

        # 3. Fallback: Estratégias padrão da classe pai (Coleções, Breadcrumbs)
        return super()._find_program(soup)

    def _clean_program_name(self, raw):
        """
        Limpeza específica para UFPEL.
        """
        # Remove prefixo institucional que às vezes aparece concatenado
        # Ex: "Universidade Federal de Pelotas. Programa de Pós-Graduação em..."
        clean = re.sub(r'^Universidade Federal de Pelotas[.,-]?\s*', '', raw, flags=re.IGNORECASE)
        
        # Chama a limpeza padrão (que remove "Programa de Pós-Graduação em", etc.)
        return super()._clean_program_name(clean)