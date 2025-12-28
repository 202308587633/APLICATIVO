from parsers.dspace_jspui import DSpaceJSPUIParser

class UFOPParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UFOP", universidade="Universidade Federal de Ouro Preto")