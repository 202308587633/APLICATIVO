from parsers.dspace_angular import DSpaceAngularParser

class UCSALParser(DSpaceAngularParser):
    def __init__(self):
        super().__init__(sigla="UCSAL", universidade="Universidade Católica do Salvador")
        
        