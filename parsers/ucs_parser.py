from parsers.dspace_jspui import DSpaceJSPUIParser

class UcsParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UCS", universidade="Universidade de Caxias do Sul")

    def _find_program(self, soup):
        """
        Estratégia específica para UCS (DSpace).
        Prioriza Meta Tags (DC.publisher) que costumam conter o nome do programa.
        """
        # 1. Busca por meta tags (DC.publisher)
        # Ex: <meta name="DC.publisher" content="Programa de Pós-Graduação em Direito">
        publishers = soup.find_all('meta', attrs={'name': 'DC.publisher'})
        for meta in publishers:
            content = meta.get('content', '')
            # Verifica se o conteúdo realmente se parece com um nome de programa
            # para evitar pegar apenas o nome da universidade
            if 'Programa' in content or 'Pós-Graduação' in content:
                return content

        # 2. Fallback: Estratégias padrão da classe pai 
        # (Tabela de metadados, Aparece nas Coleções, Breadcrumbs)
        return super()._find_program(soup)

    # Nota: A limpeza padrão (_clean_program_name) da classe pai já remove 
    # "Programa de Pós-Graduação em", "Mestrado", "Doutorado", etc.