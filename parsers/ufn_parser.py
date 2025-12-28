from parsers.dspace_jspui import DSpaceJSPUIParser

class UFNParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UFN", universidade="Universidade Franciscana")