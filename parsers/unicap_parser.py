from parsers.dspace_jspui import DSpaceJSPUIParser

class UnicapParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UNICAP", universidade="Universidade Católica de Pernambuco")

    def _find_program(self, soup):
        """
        Estratégia específica para UNICAP.
        Prioriza links com a classe 'program', que é um padrão específico deste repositório.
        """
        # 1. Estratégia específica: Link com classe "program"
        # Ex: <a class="program" href="...">Doutorado em Direito</a>
        prog_link = soup.find('a', class_='program')
        if prog_link:
            return prog_link.get_text(strip=True)

        # 2. Fallback: Estratégias padrão da classe pai (Labels na tabela, Breadcrumbs, etc.)
        return super()._find_program(soup)

    # Nota: A limpeza padrão (_clean_program_name) da classe pai já trata 
    # a remoção de "Programa de Pós-Graduação" e afins.
    # A extração de PDF também é idêntica à da classe pai.