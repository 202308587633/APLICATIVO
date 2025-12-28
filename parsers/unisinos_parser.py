import re
from parsers.dspace_jspui import DSpaceJSPUIParser

class UnisinosParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UNISINOS", universidade="Universidade do Vale do Rio dos Sinos")

    def _find_program(self, soup):
        """
        Estratégia específica para UNISINOS (Interface XMLUI/Mirage).
        Busca no breadcrumb (ul#ds-trail) por 'PPG' ou 'Programa'.
        """
        # 1. Busca no Breadcrumb específico (id="ds-trail")
        # Itera sobre os links da trilha de navegação
        crumbs = soup.select('ul#ds-trail li a')
        
        for crumb in crumbs:
            text = crumb.get_text(strip=True)
            
            # Verifica se o texto contém indicativos de ser um programa
            # A Unisinos usa muito a sigla "PPG" nos breadcrumbs
            if "PPG" in text or "Programa" in text:
                return text
        
        # 2. Fallback: Tenta as estratégias padrão da classe pai (Metadados DC, etc)
        return super()._find_program(soup)

    def _clean_program_name(self, raw):
        """
        Limpeza específica para remover o prefixo 'PPG' comum na Unisinos,
        antes de passar para a limpeza padrão.
        Ex entrada: "PPG em Direito da Empresa"
        Ex saída: "Direito da Empresa"
        """
        # Remove o prefixo "PPG" se aparecer no início
        # O regex cuida de "PPG " ou "PPG em " (o 'em' será pego no super também, mas garante aqui)
        clean = re.sub(r'^PPG\s+(?:em\s+|no\s+|na\s+)?', '', raw, flags=re.IGNORECASE)
        
        # Chama a limpeza padrão (que remove "Programa de Pós-Graduação", parênteses finais, etc.)
        return super()._clean_program_name(clean)