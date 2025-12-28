import re
from parsers.dspace_jspui import DSpaceJSPUIParser

class UfmaParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UFMA", universidade="Universidade Federal do Maranhão")

    def _find_program(self, soup):
        """
        Sobrescreve a ordem de busca padrão.
        Na UFMA, o nome completo e descritivo do programa (ex: 'DIREITO E INSTITUIÇÕES...')
        está nos Breadcrumbs. A tabela de metadados geralmente traz a sigla (ex: 'DIREITO/CCSO').
        Portanto, priorizamos o Breadcrumb.
        """
        # Tenta Breadcrumbs primeiro (foco do exemplo do usuário)
        prog = self._try_breadcrumbs(soup)
        if prog: 
            return prog
            
        # Fallback para o comportamento padrão (Metadados, Coleções, etc)
        return super()._find_program(soup)

    def _clean_program_name(self, raw):
        """
        Limpeza específica para os padrões encontrados na UFMA.
        Ex de entrada: "DISSERTAÇÃO DE MESTRADO - PROGRAMA DE PÓS-GRADUAÇÃO EM DIREITO E INSTITUIÇÕES DO SISTEMA DE JUSTIÇA - PPGDIR"
        Ex de saída desejada: "DIREITO E INSTITUIÇÕES DO SISTEMA DE JUSTIÇA"
        """
        # 1. Remove prefixos de tipo de documento comuns na trilha da UFMA
        # Remove "DISSERTAÇÃO DE MESTRADO -" ou "TESE DE DOUTORADO -"
        name = re.sub(r'^(?:DISSERTAÇÃO|TESE) DE (?:MESTRADO|DOUTORADO)\s*-\s*', '', raw, flags=re.IGNORECASE)
        
        # 2. Executa a limpeza padrão da classe pai (remove "Programa de Pós-Graduação em...")
        name = super()._clean_program_name(name)
        
        # 3. Remove sufixo de sigla separado por hífen no final (ex: " - PPGDIR")
        name = re.sub(r'\s+-\s+[A-Z0-9]+$', '', name)
        
        return name.strip()