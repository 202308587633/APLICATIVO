import re
from parsers.dspace_jspui import DSpaceJSPUIParser

class PucspParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="PUCSP", universidade="Pontifícia Universidade Católica de São Paulo")

    def _find_program(self, soup):
        """
        Estratégia específica para PUCSP (DSpace).
        Identifica o departamento/programa via classes CSS específicas na tabela de metadados.
        """
        # 1. Busca por classes CSS específicas
        # A PUCSP usa classes como 'dc_publisher_program' ou 'dc_publisher_department'
        # Ex: <td class="metadataFieldValue dc_publisher_program">Programa de Estudos Pós-Graduados em História</td>
        target_td = soup.find('td', class_=lambda c: c and 'metadataFieldValue' in c and ('dc_publisher_program' in c or 'dc_publisher_department' in c))
        
        if target_td:
            return target_td.get_text(strip=True)

        # 2. Fallback: Estratégias padrão da classe pai (Labels, Breadcrumbs, Coleções)
        return super()._find_program(soup)

    def _clean_program_name(self, raw):
        """
        Limpeza específica para remover prefixos comuns na PUCSP antes da limpeza padrão.
        """
        # Remove prefixos específicos como:
        # "Faculdade de..."
        # "Programa de Estudos Pós-Graduados em..." (Muito comum na PUCSP)
        clean = re.sub(
            r'^(?:Faculdade de|Programa de Estudos Pós-Graduados)(?:\s+(?:em|no|na))?\s+', 
            '', 
            raw, 
            flags=re.IGNORECASE
        )
        
        # Chama a limpeza padrão (que remove "Programa de Pós-Graduação", parênteses finais, etc.)
        return super()._clean_program_name(clean)