from parsers.dspace_jspui import DSpaceJSPUIParser

class UFMSParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UFMS", universidade="Universidade Federal de Mato Grosso do Sul")