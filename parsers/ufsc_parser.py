import re
from parsers.dspace_jspui import DSpaceJSPUIParser

class UfscParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UFSC", universidade="Universidade Federal de Santa Catarina")

    def _find_program(self, soup):
        """
        Sobrescreve a busca de programa.
        A UFSC utiliza DSpace com interface XMLUI (tema Mirage), onde a trilha 
        de navegação fica em <ul id="ds-trail"> e é a fonte mais confiável.
        """
        # Tenta a estratégia específica do XMLUI/UFSC primeiro
        prog = self._try_xmlui_breadcrumbs(soup)
        if prog:
            return prog
            
        # Fallback para as estratégias padrões (caso mudem o layout)
        return super()._find_program(soup)

    def _try_xmlui_breadcrumbs(self, soup):
        """
        Analisa o breadcrumb específico do tema da UFSC:
        <ul id="ds-trail">
            <li class="ds-trail-link"><a ...>Programa de Pós-Graduação em Linguística</a></li>
        </ul>
        """
        crumbs = soup.select('ul#ds-trail li')
        
        # Itera do fim para o começo (do mais específico para o geral)
        for crumb in reversed(crumbs):
            text = crumb.get_text(strip=True)
            
            # Verifica se o texto contém indicativos de ser um programa
            # Ignora o último item se for "Ver item" ou o título
            if any(term in text for term in ["Programa", "Pós-Graduação", "Mestrado", "Doutorado"]):
                return text
                
        return None