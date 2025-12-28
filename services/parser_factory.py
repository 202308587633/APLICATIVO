# services/parser_factory.py

from parsers.generic_parser import GenericParser
from parsers.ufop_parser import UfopParser
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
from parsers.uel_parser import UelParser
from parsers.ifro_parser import IFROParser
from parsers.ufma_parser import UfmaParser 
from parsers.ufsc_parser import UfscParser
from parsers.ufg_parser import UfgParser
from parsers.ufpr_parser import UfprParser
from parsers.unisinos_parser import UnisinosParser
from parsers.ufpe_parser import UfpeParser
from parsers.ufpb_parser import UfpbParser
from parsers.ufjf_parser import UfjfParser
from parsers.ufrgs_parser import UfrgsParser
from parsers.unb_parser import UnbParser
from parsers.ucb_parser import UcbParser
from parsers.upf_parser import UpfParser
from parsers.ufu_parser import UfuParser
from parsers.ucs_parser import UcsParser
from parsers.ufba_parser import UfbaParser
from parsers.fiocruz_parser import FiocruzParser
from parsers.unicap_parser import UnicapParser
from parsers.pucsp_parser import PucspParser
from parsers.ufmg_parser import UfmgParser
from parsers.mackenzie_parser import MackenzieParser
from parsers.unicamp_parser import UnicampParser
from parsers.umesp_parser import UMESPParser    
from parsers.uenp_parser import UenpParser
from parsers.ufc_parser import UfcParser
from parsers.ufs_parser import UfsParser
from parsers.ufv_parser import UfvParser
from parsers.unicesumar_parser import UnicesumarParser
from parsers.uea_parser import UeaParser
from parsers.unesp_parser import UnespParser
from parsers.ufsm_parser import UfsmParser
from parsers.uepb_parser import UepbParser
from parsers.pucrs_parser import PucrsParser
from parsers.unifor_parser import UniforParser
from parsers.ufpel_parser import UfpelParser
from parsers.uninter_parser import UninterParser
from parsers.ufrn_parser import UfrnParser
from parsers.ufes_parser import UfesParser


class ParserFactory:
    def __init__(self):
        self._default = GenericParser()
        # Mapeamento URL -> Classe
        self._map = {
            'repositorio.ufes.br': UfesParser,
            'ufes.br': UfesParser,
            'repositorio.ufrn.br': UfrnParser,
            'ufrn.br': UfrnParser,
            'repositorio.uninter.com': UninterParser,
            'uninter.com': UninterParser,
            'guaiaca.ufpel.edu.br': UfpelParser,
            'ufpel.edu.br': UfpelParser,
            'uol.unifor.br': UniforParser,
            'repositorio.unifor.br': UniforParser,
            'unifor.br': UniforParser,
            'repositorio.pucrs.br': PucrsParser,
            'pucrs.br': PucrsParser,
            'tede.bc.uepb.edu.br': UepbParser,
            'uepb.edu.br': UepbParser,
            'repositorio.ufsm.br': UfsmParser,
            'manancial.ufsm.br': UfsmParser, # URL alternativa comum
            'ufsm.br': UfsmParser,
            'repositorio.unesp.br': UnespParser,
            'unesp.br': UnespParser,
            'ri.uea.edu.br': UeaParser,
            'uea.edu.br': UeaParser,
            'repositorio.unicesumar.edu.br': UnicesumarParser,
            'unicesumar.edu.br': UnicesumarParser,
            'locus.ufv.br': UfvParser,
            'ufv.br': UfvParser,
            'ri.ufs.br': UfsParser,
            'ufs.br': UfsParser,
            'repositorio.ufc.br': UfcParser,
            'ufc.br': UfcParser,
            'repositorio.uenp.edu.br': UenpParser,
            'uenp.edu.br': UenpParser,
            'tede.metodista.br': UMESPParser,
            'metodista.br': UMESPParser,
            'repositorio.unicamp.br': UnicampParser,
            'unicamp.br': UnicampParser,
            'dspace.mackenzie.br': MackenzieParser,
            'mackenzie.br': MackenzieParser,
            'repositorio.ufmg.br': UfmgParser,
            'ufmg.br': UfmgParser,
            'sapientia.pucsp.br': PucspParser,
            'pucsp.br': PucspParser,
            'repositorio.unicap.br': UnicapParser,
            'unicap.br': UnicapParser,
            'arca.fiocruz.br': FiocruzParser,
            'fiocruz.br': FiocruzParser,
            'repositorio.ufba.br': UfbaParser,
            'ufba.br': UfbaParser,
            'repositorio.ucs.br': UcsParser,
            'ucs.br': UcsParser,
            'repositorio.ufu.br': UfuParser,
            'ufu.br': UfuParser,
            'repositorio.upf.br': UpfParser,
            'upf.br': UpfParser,
            'bdtd.ucb.br': UcbParser,
            'ucb.br': UcbParser,
            'repositorio.unb.br': UnbParser,
            'unb.br': UnbParser,
            'lume.ufrgs.br': UfrgsParser,
            'ufrgs.br': UfrgsParser,
            'repositorio.ufjf.br': UfjfParser,
            'ufjf.br': UfjfParser,
            'repositorio.ufpb.br': UfpbParser,
            'ufpb.br': UfpbParser,
            'repositorio.ufpe.br': UfpeParser,
            'ufpe.br': UfpeParser,
            "ufop.br": UfopParser,
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
            "repositorio.uel.br": UelParser,
            "uel.br": UelParser,
            "repositorio.ifro.edu.br": IFROParser,
            "ifro.edu.br": IFROParser,
            'ufma.br': UfmaParser,
            'tedebc.ufma.br': UfmaParser, # Domínio específico do repositório
            'repositorio.ufsc.br': UfscParser,            
            'repositorio.bc.ufg.br': UfgParser,
            'ufg.br': UfgParser,
            'acervodigital.ufpr.br': UfprParser,
            'ufpr.br': UfprParser,
            'repositorio.jesuita.org.br': UnisinosParser, # URL comum para Unisinos
            'unisinos.br': UnisinosParser,                        
        }

    def get_parser(self, url):
        if not url: return self._default
        
        url_lower = url.lower()
        for domain, parser_cls in self._map.items():
            if domain in url_lower:
                return parser_cls() # Instancia a classe aqui
        
        return self._default