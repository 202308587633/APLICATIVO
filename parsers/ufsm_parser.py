import re
from parsers.dspace_jspui import DSpaceJSPUIParser

class UfsmParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UFSM", universidade="Universidade Federal de Santa Maria")

    def _find_program(self, soup):
        """
        Estratégia específica para UFSM (DSpace XMLUI).
        Busca na seção de coleções (simple-item-view-collections) ou Meta Tags.
        """
        # 1. Estratégia: Seção "Coleções" (XMLUI Mirage)
        # Ex: <div class="simple-item-view-collections">... <a ...>Programa de Pós-Graduação em Direito</a> ...</div>
        collections_div = soup.find('div', class_='simple-item-view-collections')
        if collections_div:
            # Busca links dentro da lista de referência (padrão DSpace)
            links = collections_div.select('ul.ds-referenceSet-list li a')
            for link in links:
                text = link.get_text(strip=True)
                if "Programa de Pós-Graduação" in text:
                    return text
            
            # Fallback: Se não achar na lista específica, busca qualquer link na div
            links = collections_div.find_all('a')
            for link in links:
                text = link.get_text(strip=True)
                if "Programa de Pós-Graduação" in text:
                    return text

        # 2. Estratégia: Meta Tag DC.publisher
        # Ex: <meta name="DC.publisher" content="Programa de Pós-Graduação em Direito">
        publishers = soup.find_all('meta', attrs={'name': 'DC.publisher'})
        for meta in publishers:
            content = meta.get('content', '')
            if "Programa de Pós-Graduação" in content:
                return content

        # 3. Fallback: Estratégias padrão da classe pai
        return super()._find_program(soup)

    def _clean_program_name(self, raw):
        """
        Limpeza para garantir que removemos tudo antes de "Programa..." se houver lixo no texto.
        """
        # Remove qualquer texto que preceda "Programa de Pós-Graduação"
        # Ex: "Manancial - Programa de Pós-Graduação em Educação" -> "Educação"
        if "Programa de Pós-Graduação" in raw:
            raw = re.sub(r'^.*?(?=Programa)', '', raw, flags=re.IGNORECASE)
            
        # Chama a limpeza padrão (remove "Programa de Pós-Graduação em", etc.)
        return super()._clean_program_name(raw)