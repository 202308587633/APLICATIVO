import re
from urllib.parse import unquote
from parsers.base_parser import BaseParser

class PucMinasParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="PUC MINAS", universidade="Pontifícia Universidade Católica de Minas Gerais")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da PUC Minas.
        
        OBSERVAÇÃO ESPECÍFICA:
        A PUC Minas frequentemente fornece o link direto para o PDF como sendo o link do trabalho.
        Neste caso, não há HTML para parsear metadados.
        A lógica abaixo identifica se é um PDF e tenta extrair informações da própria URL.
        """
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("PUC MINAS: Analisando URL...")

        # --- LÓGICA PARA LINK DIRETO DE PDF ---
        # Exemplo: http://bib.pucminas.br/teses/ComunicacaoSocial_AlyssonLisboaNeves_19174_Textocompleto.pdf
        if url.lower().endswith('.pdf'):
            data['link_pdf'] = url
            if on_progress: on_progress("PUC MINAS: Link direto para PDF identificado.")

            # Tenta extrair o programa da estrutura da URL
            # Procura pelo texto entre "/teses/" e o primeiro "_"
            # Ex: .../teses/ComunicacaoSocial_... -> "ComunicacaoSocial"
            try:
                match = re.search(r'/teses/([^_]+)_', url)
                if match:
                    raw_program = match.group(1)
                    
                    # Decodifica URL caso tenha caracteres especiais (%20, etc)
                    raw_program = unquote(raw_program)
                    
                    # Tenta separar CamelCase se houver (Ex: "ComunicacaoSocial" -> "Comunicacao Social")
                    # Regex: Insere espaço entre uma letra minúscula e uma maiúscula
                    clean_program = re.sub(r'([a-z])([A-Z])', r'\1 \2', raw_program)
                    
                    data['programa'] = clean_program.strip()
                    
                    if on_progress: on_progress(f"PUC MINAS: Programa estimado pela URL: {data['programa']}")
                else:
                    if on_progress: on_progress("PUC MINAS: Não foi possível extrair o programa da URL.")
            except Exception as e:
                if on_progress: on_progress(f"PUC MINAS: Erro ao processar URL: {e}")

        # --- LÓGICA DE FALLBACK (CASO SEJA UMA PÁGINA HTML) ---
        else:
            # Caso o sistema mude e passe a fornecer uma landing page HTML,
            # aqui você implementaria o BeautifulSoup normal.
            # Por enquanto, assumimos que o link pode ser salvo como o "link do repositório"
            # e tentamos achar um link de PDF dentro do HTML se existir.
            if on_progress: on_progress("PUC MINAS: URL não é PDF direto, analisando HTML...")
            # (Implementação futura se necessário)

        return data
    
    