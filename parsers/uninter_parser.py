import re
from parsers.dspace_jspui import DSpaceJSPUIParser

class UninterParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UNINTER", universidade="Centro Universitário Internacional")

    def _find_program(self, soup):
        """
        Estratégia específica para UNINTER.
        O repositório utiliza DSpace JSPUI padrão, onde o programa aparece nas coleções.
        Ex: <div class="simple-item-view-collections">... <a href="...">Mestrado Acadêmico em Direito</a> ...</div>
        """
        # A implementação padrão da classe pai (DSpaceJSPUIParser) já cobre essa busca
        # na div 'simple-item-view-collections' e nos breadcrumbs.
        # Portanto, apenas chamamos o super().
        return super()._find_program(soup)

    def _clean_program_name(self, raw):
        """
        Limpeza específica para remover prefixos de grau acadêmico comuns na UNINTER.
        """
        # Remove "Mestrado Acadêmico em", "Mestrado Profissional em", etc.
        clean = re.sub(r'Mestrado (?:Acadêmico|Profissional)?\s*(?:em|no|na)\s+', '', raw, flags=re.IGNORECASE)
        
        # Remove "Doutorado em..."
        clean = re.sub(r'Doutorado (?:em|no|na)\s+', '', clean, flags=re.IGNORECASE)

        # Chama a limpeza padrão (para garantir remoção de outros prefixos genéricos)
        return super()._clean_program_name(clean)