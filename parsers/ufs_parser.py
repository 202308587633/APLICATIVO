from parsers.dspace_jspui import DSpaceJSPUIParser

class UfsParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UFS", universidade="Universidade Federal de Sergipe")

    def _find_program(self, soup):
        """
        Estratégia específica para UFS (DSpace JSPUI).
        Prioriza a classe CSS específica 'dc_publisher_program'.
        """
        # 1. Estratégia específica: Classe CSS na tabela de metadados
        # Ex: <td class="metadataFieldValue dc_publisher_program">Pós-Graduação em Direito</td>
        prog_td = soup.find('td', class_='dc_publisher_program')
        if prog_td:
            return prog_td.get_text(strip=True)

        # 2. Fallback: Estratégias padrão da classe pai (Breadcrumbs, Labels, etc.)
        return super()._find_program(soup)

    def _clean_program_name(self, raw):
        """
        Limpeza específica para remover siglas após hífen (comum na UFS)
        antes da limpeza padrão.
        """
        # Ex entrada: "Programa de Pós-Graduação em Direito - PRODIR"
        # Remove sufixo de sigla após hífen
        clean = raw.split(' - ')[0]
        
        # Ex intermediário: "Programa de Pós-Graduação em Direito"
        # Chama a limpeza padrão (remove "Programa de Pós-Graduação", etc.)
        return super()._clean_program_name(clean)