import re
from parsers.dspace_jspui import DSpaceJSPUIParser

class UnicesumarParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UNICESUMAR", universidade="Universidade Cesumar")

    def _find_program(self, soup):
        """
        Estratégia específica para UNICESUMAR (DSpace JSPUI).
        Prioriza a classe CSS 'dc_publisher_program' e Meta Tags Dublin Core com formatação específica.
        """
        # 1. Estratégia: Classe CSS específica na tabela de metadados
        # Ex: <td class="metadataFieldValue dc_publisher_program">Ciências Jurídicas (Mestrado)</td>
        prog_td = soup.find('td', class_='dc_publisher_program')
        if prog_td:
            return prog_td.get_text(strip=True)

        # 2. Estratégia: Meta Tag DC.publisher
        # Ex: <meta name="DC.publisher" content="Ciências Jurídicas (Mestrado)">
        publishers = soup.find_all('meta', attrs={'name': 'DC.publisher'})
        for meta in publishers:
            content = meta.get('content', '')
            # Validação específica da UNICESUMAR (costuma indicar o nível entre parênteses)
            if '(' in content and any(k in content for k in ['Mestrado', 'Doutorado']):
                return content

        # 3. Fallback: Estratégias padrão da classe pai (Labels, Breadcrumbs, etc.)
        return super()._find_program(soup)

    def _clean_program_name(self, raw):
        """
        Limpeza específica para remover sufixos de nível como "(Mestrado)" antes da limpeza padrão.
        """
        # Remove sufixos entre parênteses contendo Mestrado/Doutorado
        # Ex: "Ciências Jurídicas (Mestrado)" -> "Ciências Jurídicas"
        clean = re.sub(r'\s*\(?(?:Mestrado|Doutorado).*?\)?', '', raw, flags=re.IGNORECASE)
        
        # Chama a limpeza padrão (remove "Programa de Pós-Graduação em", siglas, etc.)
        return super()._clean_program_name(clean)