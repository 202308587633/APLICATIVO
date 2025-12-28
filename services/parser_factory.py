# services/parser_factory.py

from parsers.generic_parser import GenericParser
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
from parsers.unifal_parser import UNIFALParser
from parsers.fdv_parser import FDVParser
from parsers.uninove_parser import UninoveParser
from parsers.usp_parser import USPParser
from parsers.ufgd_parser import UFGDParser
from parsers.uff_parser import UFFParser
from parsers.pucgoias_parser import PUCGOIASParser
from parsers.ufrr_parser import UFRRParser
from parsers.unifesp_parser import UNIFESPParser
from parsers.unifacs_parser import UNIFACSParser
from parsers.uel_parser import UELParser
from parsers.ifro_parser import IFROParser
from parsers.ufma_parser import UfmaParser 

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
            "repositorio.ufms.br": UFMSParser,
            "rima.ufrrj.br": UFRRJParser,
            "tede.unioeste.br": UNIOESTEParser,
            "tede.unisantos.br": UNISANTOSParser,
            "unisantos.br": UNISANTOSParser,
            "repositorio.unifal-mg.edu.br": UNIFALParser,
            "unifal-mg.edu.br": UNIFALParser,
            "fdv.br": FDVParser,          # Caso usem o domínio nominal
            "191.252.194.60": FDVParser,  # Para capturar o link do exemplo (IP)
            "/fdv/": FDVParser,
            "uninove.br": UninoveParser,
            "bibliotecatede.uninove.br": UninoveParser,
            "teses.usp.br": USPParser,
            "usp.br": USPParser,
            "repositorio.ufgd.edu.br": UFGDParser,
            "ufgd.edu.br": UFGDParser,
            "app.uff.br": UFFParser,
            "riuff": UFFParser,
            "uff.br": UFFParser,
            "pucgoias.edu.br": PUCGOIASParser,
            "tede2.pucgoias.edu.br": PUCGOIASParser,
            "repositorio.ufrr.br": UFRRParser,
            "ufrr.br": UFRRParser,            
            "repositorio.unifesp.br": UNIFESPParser,
            "unifesp.br": UNIFESPParser,
            "hdl.handle.net/11600": UNIFESPParser, # Prefixo Handle da UNIFESP
            "deposita.ibict.br": UNIFACSParser, # Mapeia o repositório compartilhado
            "unifacs.br": UNIFACSParser,        # Caso usem domínio próprio
            "repositorio.uel.br": UELParser,
            "uel.br": UELParser,
            "repositorio.ifro.edu.br": IFROParser,
            "ifro.edu.br": IFROParser,
            'ufma.br': UfmaParser,
            'tedebc.ufma.br': UfmaParser, # Domínio específico do repositório
        }

    def get_parser(self, url):
        if not url: return self._default
        
        url_lower = url.lower()
        for domain, parser_cls in self._map.items():
            if domain in url_lower:
                return parser_cls() # Instancia a classe aqui
        
        return self._default