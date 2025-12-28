import re
from parsers.dspace_angular import DSpaceAngularParser

class UNIFALParser(DSpaceAngularParser):
    def __init__(self):
        super().__init__(sigla="UNIFAL", universidade="Universidade Federal de Alfenas")

    def _find_program_fallback(self, soup):
        """
        Estratégia específica da UNIFAL: Extrair o programa do campo 'Citação'.
        Exemplo: "... Dissertação (Mestrado em Gestão Pública e Sociedade) - Universidade..."
        """
        # Procura por blocos de metadados visuais do DSpace Angular
        elements = soup.find_all('div', class_='simple-view-element')
        
        for el in elements:
            header = el.find(class_='simple-view-element-header')
            
            # Verifica se é o bloco de Citação
            if header and 'citação' in header.get_text(strip=True).lower():
                body = el.find(class_='simple-view-element-body')
                if body:
                    text = body.get_text(strip=True)
                    
                    # Regex para capturar o texto dentro dos parênteses após o grau
                    # Procura por "Mestrado em X" ou "Doutorado em X" até encontrar ')' ou '-'
                    match = re.search(
                        r'(?:Mestrado|Doutorado|Programa).*?em\s+([^)\-]+)', 
                        text, 
                        re.IGNORECASE
                    )
                    
                    if match:
                        return match.group(1).strip()
        
        return None