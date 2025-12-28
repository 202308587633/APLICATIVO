from parsers.dspace_jspui import DSpaceJSPUIParser

class UfjfParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UFJF", universidade="Universidade Federal de Juiz de Fora")

    def _find_program(self, soup):
        """
        Estratégia específica para UFJF (DSpace 6.x JSPUI).
        O repositório expõe o programa numa classe CSS específica derivada do metadado Dublin Core.
        """
        # 1. Tenta a classe CSS específica (Estratégia mais precisa para UFJF)
        # Ex: <td class="metadataFieldValue dc_publisher_program">...</td>
        prog_td = soup.find('td', class_='dc_publisher_program')
        if prog_td:
            return prog_td.get_text(strip=True)

        # 2. Fallback: Estratégias padrão da classe pai
        # (Busca por labels "Programa:", "Aparece nas coleções", etc.)
        return super()._find_program(soup)

    # Nota: A extração de PDF e a limpeza de nomes (_clean_program_name) 
    # já são tratadas eficientemente pela classe pai (DSpaceJSPUIParser).