from parsers.dspace_angular import DSpaceAngularParser

class UNIPAMPAParser(DSpaceAngularParser):
    def __init__(self):
        super().__init__(sigla="UNIPAMPA", universidade="Universidade Federal do Pampa")