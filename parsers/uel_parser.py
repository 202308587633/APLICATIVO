import re
from bs4 import BeautifulSoup
from parsers.dspace_angular import DSpaceAngularParser

class UELParser(DSpaceAngularParser):
    def __init__(self):
        # Inicializa com os dados fixos da UEL
        super().__init__(sigla="UEL", universidade="Universidade Estadual de Londrina")

    def _find_program_fallback(self, soup):
        """
        Estratégia específica para UEL:
        O programa geralmente está listado na seção "Coleções" com um formato específico.
        Ex: <div class="collections"><a ...><span>01 - Doutorado - Estudos da Linguagem</span></a></div>
        """
        try:
            # Procura a div de coleções
            collections_div = soup.find('div', class_='collections')
            if collections_div:
                # Pega o primeiro link dentro dela
                link = collections_div.find('a')
                if link:
                    return link.get_text(strip=True)
        except Exception:
            pass
        
        return None

    def _clean_program_name(self, raw):
        """
        Limpeza específica para o padrão da UEL.
        Entrada típica: "01 - Doutorado - Estudos da Linguagem"
        Saída desejada: "Estudos da Linguagem"
        """
        if not raw: return "-"
        
        # 1. Remove prefixos numéricos (Ex: "01 - ", "15 - ")
        clean = re.sub(r'^\d+\s*-\s*', '', raw)
        
        # 2. Remove o nível acadêmico se estiver seguido de traço (Ex: "Doutorado - ", "Mestrado Profissional - ")
        clean = re.sub(r'^(?:Mestrado|Doutorado)(?: Profissional)?\s*-\s*', '', clean, flags=re.IGNORECASE)
        
        # 3. Executa a limpeza padrão da classe pai (remove "Programa de Pós-Graduação", etc)
        return super()._clean_program_name(clean)