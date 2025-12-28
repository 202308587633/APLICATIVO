from parsers.dspace_angular import DSpaceAngularParser

class UMESPParser(DSpaceAngularParser):
    def __init__(self):
        super().__init__(sigla="UMESP", universidade="Universidade Metodista de São Paulo")