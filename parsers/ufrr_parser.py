import re
from bs4 import BeautifulSoup
from parsers.dspace_jspui import DSpaceJSPUIParser

class UFRRParser(DSpaceJSPUIParser):
    def __init__(self):
        # Inicializa a classe pai com os dados da UFRR
        super().__init__(sigla="UFRR", universidade="Universidade Federal de Roraima")

    def _find_program(self, soup):
        """
        Sobrescreve a busca de programa padrão da classe pai.
        Para a UFRR, as Meta Tags são mais precisas que a tabela visual.
        """
        found_program = None

        # ESTRATÉGIA 1: Meta Tag 'DC.publisher.program' (Específica da UFRR)
        # Ex: "PPGSOF - Programa de Pós-Graduação em Sociedade e Fronteiras"
        meta_pub = soup.find('meta', attrs={'name': 'DC.publisher.program'})
        if meta_pub:
            found_program = meta_pub.get('content')

        # ESTRATÉGIA 2: Citação Bibliográfica (Fallback)
        # Ex: "... (Mestrado em Sociedade e Fronteiras) ..."
        if not found_program:
            meta_cit = soup.find('meta', attrs={'name': 'DCTERMS.bibliographicCitation'})
            if meta_cit:
                match = re.search(r'Programa de Pós-Graduação\s+(?:em\s+)?([^,]+)', meta_cit.get('content', ''), re.IGNORECASE)
                if match:
                    found_program = match.group(1)

        # Se as estratégias específicas falharem, tenta as genéricas da classe pai (Tabela, Breadcrumbs)
        if not found_program:
            found_program = super()._find_program(soup)

        return found_program

    # Nota: Não é necessário reimplementar extract_pure_soup ou _find_pdf,
    # pois a DSpaceJSPUIParser já faz isso perfeitamente para este caso.