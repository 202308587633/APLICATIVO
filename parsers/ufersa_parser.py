from parsers.dspace_angular import DSpaceAngularParser

class UFERSAParser(DSpaceAngularParser):
    def __init__(self):
        super().__init__(sigla="UFERSA", universidade="Universidade Federal Rural do Semi-Árido")