from parsers.dspace_jspui import DSpaceJSPUIParser

class UNISANTOSParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UNISANTOS", universidade="Universidade Católica de Santos")

    def _find_program(self, soup):
        # Estratégia Específica: Busca pela classe CSS exata do DSpace da UNISANTOS
        # Ex: <td class="metadataFieldValue dc_publisher_program">Mestrado em Direito</td>
        program_td = soup.find('td', class_='metadataFieldValue dc_publisher_program')
        if program_td:
            return program_td.get_text(strip=True)
            
        # Fallback: Tenta a lógica padrão da classe pai (Labels genéricos, Breadcrumbs, etc)
        return super()._find_program(soup)