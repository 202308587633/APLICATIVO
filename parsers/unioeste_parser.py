import re
from parsers.dspace_jspui import DSpaceJSPUIParser

class UNIOESTEParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UNIOESTE", universidade="Universidade Estadual do Oeste do Paraná")

    def _find_program(self, soup):
        # 1. Tenta a lógica padrão da classe pai (Tabelas, Breadcrumbs...)
        prog = super()._find_program(soup)
        if prog: return prog

        # 2. Estratégia Específica: Extração via Citação (Fallback)
        # Ex: "Dissertação (Mestrado em Saúde Pública) - Universidade..."
        citation_row = soup.find('td', id='label.dc.identifier.citation')
        if citation_row:
            value_td = citation_row.find_next_sibling('td', class_='metadataFieldValue')
            if value_td:
                citation_text = value_td.get_text(strip=True)
                match = re.search(
                    r'(?:Mestrado|Doutorado|Mestre|Doutor)(?:\s+Profissional|\s+Acadêmico)?\s+em\s+([^)\-]+)', 
                    citation_text, 
                    re.IGNORECASE
                )
                if match:
                    return match.group(1).strip()
        
        return None