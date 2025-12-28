from parsers.dspace_jspui import DSpaceJSPUIParser

class UFRRJParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UFRRJ", universidade="Universidade Federal Rural do Rio de Janeiro")