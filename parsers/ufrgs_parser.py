import re
from parsers.dspace_jspui import DSpaceJSPUIParser

class UfrgsParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UFRGS", universidade="Universidade Federal do Rio Grande do Sul")

    def _find_program(self, soup):
        """
        Estratégia específica para UFRGS (Lume).
        Busca na seção 'Instituição' (classe simple-item-view-authors) ou nas coleções.
        """
        # 1. Estratégia Prioritária: Seção "Instituição"
        # Estrutura típica: <div class="simple-item-view-authors"><h5>Instituição</h5><div>...</div></div>
        inst_divs = soup.find_all('div', class_='simple-item-view-authors')
        for div in inst_divs:
            h5 = div.find('h5')
            if h5 and "Instituição" in h5.get_text():
                value_div = div.find('div')
                if value_div:
                    text = value_div.get_text(strip=True)
                    
                    # Tenta extrair a parte do Programa usando Regex
                    if "Programa" in text:
                        # Procura algo como "Programa de Pós-Graduação em X."
                        match = re.search(r'Programa de Pós-Graduação\s*(?:em|no|na)?\s+(.*?)[\.$]', text, re.IGNORECASE)
                        if match:
                            return match.group(1).strip().rstrip('.')
                        
                        # Fallback: Se o regex falhar, tenta pegar a frase que contém "Programa"
                        parts = text.split('.')
                        for part in parts:
                            if "Programa" in part:
                                return part.strip()
                    
                    return text

        # 2. Estratégia: Lista de Coleções (XMLUI)
        # Procura por <div class="itemCommunityOthersCollections"> ou <ul> de referência
        
        # Opção A: Divs de coleção
        coll_divs = soup.find_all('div', class_='itemCommunityOthersCollections')
        for div in coll_divs:
            link = div.find('a')
            if link:
                text = link.get_text(strip=True)
                if text not in ["Teses e Dissertações", "Ciências Sociais Aplicadas"]:
                    return text

        # Opção B: Lista UL (ds-referenceSet-list)
        collection_list = soup.find('ul', class_='ds-referenceSet-list')
        if collection_list:
            links = collection_list.find_all('a')
            candidates = []
            for link in links:
                text = link.get_text(strip=True)
                # Filtra coleções genéricas
                if text not in ["Teses e Dissertações", "Ciências Sociais Aplicadas"]:
                    candidates.append(text)
            
            # Retorna o último (geralmente o mais específico)
            if candidates:
                return candidates[-1]

        # 3. Fallback: Tenta estratégias genéricas (Breadcrumbs, Metadados Dublin Core)
        return super()._find_program(soup)