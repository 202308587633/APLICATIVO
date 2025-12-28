import re
from parsers.dspace_jspui import DSpaceJSPUIParser

class UfopParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UFOP", universidade="Universidade Federal de Ouro Preto")

    def _find_program(self, soup):
        """
        Estratégia específica para UFOP (DSpace 8/Angular).
        Busca nos breadcrumbs, pois o repositório estrutura bem a hierarquia.
        Ex: Início > Escola... > Depto... > Programa de Pós-Graduação em Direito > ...
        """
        # 1. Estratégia Breadcrumbs
        crumbs = soup.select('ol.breadcrumb li')
        for crumb in crumbs:
            text = crumb.get_text(strip=True)
            # Verifica se é um nó de Programa de Pós-Graduação
            if "Programa de Pós-Graduação" in text:
                return text

        # 2. Estratégia: Metadado dc.description (comum em DSpace mais novos)
        # Ex: "Programa de Pós-Graduação em Direito. Departamento de Direito..."
        desc_meta = soup.find('meta', attrs={'name': 'description'})
        if desc_meta:
            content = desc_meta.get('content', '')
            if "Programa de Pós-Graduação" in content:
                # Tenta pegar a primeira frase ou até um ponto
                parts = content.split('.')
                for part in parts:
                    if "Programa de Pós-Graduação" in part:
                        return part.strip()

        # 3. Fallback: Padrão
        return super()._find_program(soup)

    def _clean_program_name(self, raw):
        """
        Limpeza específica para UFOP.
        """
        # Remove "Programa de Pós-Graduação em/no/na"
        clean = re.sub(r'Programa de Pós-Graduação (?:em|no|na)\s+', '', raw, flags=re.IGNORECASE)
        
        # Remove sufixos que possam vir no breadcrumb ou metadado (ex: datas, traços)
        if " - " in clean:
            clean = clean.split(" - ")[0]
            
        return super()._clean_program_name(clean)