from parsers.dspace_jspui import DSpaceJSPUIParser

class UTFPRParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UTFPR", universidade="Universidade Tecnológica Federal do Paraná")