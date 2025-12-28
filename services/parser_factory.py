# services/parser_factory.py

from parsers.generic_parser import GenericParser
# Importe APENAS os parsers que você já refatorou ou criou
from parsers.ufop_parser import UFOPParser
from parsers.ufms_parser import UFMSParser
from parsers.ufscar_parser import UFSCARParser
from parsers.ufrrj_parser import UFRRJParser
from parsers.ufn_parser import UFNParser
from parsers.unioeste_parser import UNIOESTEParser
from parsers.utfpr_parser import UTFPRParser
from parsers.ufersa_parser import UFERSAParser
from parsers.ucsal_parser import UCSALParser
from parsers.unipampa_parser import UNIPAMPAParser
from parsers.fgv_parser import FGVParser
from parsers.unisantos_parser import UNISANTOSParser
# ... importe os outros parsers à medida que você os cria/refatora

class ParserFactory:
    def __init__(self):
        self._default = GenericParser()
        # Mapeamento URL -> Classe
        self._map = {
            "ufop.br": UFOPParser,
            "ufms.br": UFMSParser,
            "ufscar.br": UFSCARParser,
            "ufrrj.br": UFRRJParser,
            "universidadefranciscana.edu.br": UFNParser,
            "unioeste.br": UNIOESTEParser,
            "utfpr.edu.br": UTFPRParser,
            "ufersa.edu.br": UFERSAParser,
            "ucsal.br": UCSALParser,
            "unipampa.edu.br": UNIPAMPAParser,
            "fgv.br": FGVParser,
            
            # Adicione aqui os mapeamentos extras de URL se necessário
            "repositorio.ufms.br": UFMSParser,
            "rima.ufrrj.br": UFRRJParser,
            "tede.unioeste.br": UNIOESTEParser,
            "tede.unisantos.br": UNISANTOSParser,
            "unisantos.br": UNISANTOSParser,
        }

    def get_parser(self, url):
        if not url: return self._default
        
        url_lower = url.lower()
        for domain, parser_cls in self._map.items():
            if domain in url_lower:
                return parser_cls() # Instancia a classe aqui
        
        return self._default