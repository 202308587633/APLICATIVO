import re
from parsers.dspace_jspui import DSpaceJSPUIParser

class PucrsParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="PUCRS", universidade="Pontifícia Universidade Católica do Rio Grande do Sul")

    def _find_program(self, soup):
        """
        Estratégia específica para PUCRS.
        O repositório organiza muito bem os programas nas coleções e breadcrumbs.
        """
        # 1. Busca nos Breadcrumbs (Caminho de navegação)
        # A PUCRS geralmente estrutura como: Home > Escolas > Escola de... > Programa de Pós-Graduação em...
        crumbs = soup.select('ol.breadcrumb li a')
        for crumb in crumbs:
            text = crumb.get_text(strip=True)
            
            # Verifica se é explicitamente um Programa de Pós
            if "Programa de Pós-Graduação" in text:
                return text
            
            # Às vezes aparece como "Mestrado em..." ou "Doutorado em..."
            if text.startswith("Mestrado em") or text.startswith("Doutorado em"):
                return text

        # 2. Busca na tabela de metadados por afiliação ou departamento
        # Ex: dc.publisher.program (se existir) ou dc.contributor.author
        # (Fallback para a lógica padrão)
        return super()._find_program(soup)

    def _clean_program_name(self, raw):
        """
        Limpeza específica para remover nomes de Escolas antes do programa.
        """
        # A PUCRS frequentemente coloca a Escola antes do programa em títulos de coleção
        # Ex: "Escola de Humanidades - Programa de Pós-Graduação em Filosofia"
        
        # Remove o prefixo "Escola de ... -"
        clean = re.sub(r'^Escola de .*?-\s*', '', raw, flags=re.IGNORECASE)
        
        # Remove "Programa de Pós-Graduação em..." (Lógica padrão da classe pai)
        return super()._clean_program_name(clean)