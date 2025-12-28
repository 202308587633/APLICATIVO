from parsers.dspace_angular import DSpaceAngularParser

class FGVParser(DSpaceAngularParser):
    def __init__(self):
        super().__init__(
            sigla="FGV", 
            universidade="Escola de Direito de São Paulo da Fundação Getulio Vargas"
        )

    def _check_dynamic_context(self, soup, on_progress):
        # Verifica se é EBAPE e altera a instância dinamicamente
        if "EBAPE" in soup.get_text().upper():
            self.sigla = "FGV-RJ"
            self.universidade = "Escola Brasileira de Administração Pública e de Empresas da Fundação Getúlio Vargas"
            if on_progress: on_progress("FGV: Contexto EBAPE identificado.")