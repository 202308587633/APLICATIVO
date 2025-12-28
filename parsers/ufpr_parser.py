import re
from parsers.dspace_jspui import DSpaceJSPUIParser

class UfprParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UFPR", universidade="Universidade Federal do Paraná")

    def _find_program(self, soup):
        """
        Sobrescreve a busca de programa para priorizar os padrões da UFPR.
        """
        # 1. Estratégia Breadcrumb (Padrão UFPR: <ul class="breadcrumb">)
        # Procura link que contenha explicitamente "Programa de Pós-Graduação"
        crumbs = soup.select('ul.breadcrumb li a')
        for crumb in crumbs:
            text = crumb.get_text(strip=True)
            if "Programa de Pós-Graduação" in text:
                return text

        # 2. Estratégia Meta Tags (Herdado do parser antigo da UFPR)
        # Muitas vezes o programa está em uma meta tag DC.contributor
        meta_contribs = soup.find_all('meta', attrs={'name': 'DC.contributor'})
        for meta in meta_contribs:
            content = meta.get('content', '')
            if "Programa de Pós-Graduação" in content:
                return content

        # 3. Fallback: Estratégias padrão do DSpace JSPUI (Tabela de metadados, etc.)
        return super()._find_program(soup)

    def _clean_program_name(self, raw):
        """
        Limpeza específica para remover os códigos numéricos da UFPR antes da limpeza padrão.
        Ex entrada: "40001016017P3 Programa de Pós-Graduação em Direito"
        Ex saída: "Direito"
        """
        # 1. Remove qualquer prefixo (código) antes da palavra "Programa"
        # O regex (?=...) é um lookahead para parar antes de consumir a palavra "Programa"
        if "Programa" in raw:
            raw = re.sub(r'^.*?(?=Programa)', '', raw, flags=re.IGNORECASE)

        # 2. Executa a limpeza padrão da classe pai 
        # (Remove "Programa de Pós-Graduação em", sufixos entre parênteses, etc.)
        return super()._clean_program_name(raw)