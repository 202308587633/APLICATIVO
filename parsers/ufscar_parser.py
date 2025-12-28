import re
from parsers.dspace_angular import DSpaceAngularParser

class UFSCARParser(DSpaceAngularParser):
    def __init__(self):
        super().__init__(sigla="UFSCAR", universidade="Universidade Federal de São Carlos")

    def _find_program_fallback(self, soup):
        # Procura na div de Citação
        elements = soup.find_all('div', class_='simple-view-element')
        for el in elements:
            header = el.find(class_='simple-view-element-header')
            if header and 'citação' in header.get_text(strip=True).lower():
                body = el.find(class_='simple-view-element-body')
                if body:
                    # Regex para capturar dentro dos parênteses: "Dissertação (Mestrado em X)"
                    match = re.search(r'\((?:Mestrado|Doutorado).*?em\s+([^)]+)\)', body.get_text())
                    if match: return match.group(1)
        return None
    