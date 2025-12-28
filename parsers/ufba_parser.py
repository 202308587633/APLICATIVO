from parsers.dspace_jspui import DSpaceJSPUIParser

class UfbaParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UFBA", universidade="Universidade Federal da Bahia")

    def _find_program(self, soup):
        """
        Estratégia específica para UFBA (DSpace JSPUI).
        Prioriza a classe CSS específica 'dc_publisher_program' e Meta Tags Dublin Core.
        """
        # 1. Busca pela classe específica do DSpace da UFBA
        # Ex: <td class="metadataFieldValue dc_publisher_program">Programa de Pós-graduação em Direito</td>
        prog_td = soup.find('td', class_='dc_publisher_program')
        if prog_td:
            return prog_td.get_text(strip=True)

        # 2. Busca por meta tags (DC.publisher)
        # Muitas vezes contém o nome do programa.
        publishers = soup.find_all('meta', attrs={'name': 'DC.publisher'})
        for meta in publishers:
            content = meta.get('content', '')
            # Verifica se parece um programa para não pegar o nome da universidade apenas
            if 'Programa' in content or 'Pós-graduação' in content:
                return content

        # 3. Fallback: Estratégias padrão da classe pai (Labels na tabela, Breadcrumbs)
        return super()._find_program(soup)

    # Nota: A limpeza padrão (_clean_program_name) da classe pai já remove 
    # "Programa de Pós-Graduação em..." e siglas entre parênteses "(PPGD)" corretamente.