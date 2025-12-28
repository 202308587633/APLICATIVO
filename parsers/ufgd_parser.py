import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UFGDParser(BaseParser):
    def __init__(self):
        # Definição fixa da Sigla e Nome conforme solicitado
        super().__init__(sigla="UFGD", universidade="Universidade Federal da Grande Dourados")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UFGD (DSpace).
        Foca na citação bibliográfica para o Programa e meta tags para o PDF.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UFGD: Analisando HTML...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        found_program = None

        # ESTRATÉGIA A: Citação Bibliográfica (Conforme exemplo do usuário)
        # Ex: "... (Mestrado em Fronteiras e Direitos Humanos) ..."
        try:
            citation_meta = soup.find('meta', attrs={'name': 'DCTERMS.bibliographicCitation'})
            if citation_meta:
                content = citation_meta.get('content', '')
                # Regex procura por "(Mestrado/Doutorado em NOME)"
                match = re.search(r'\((?:Mestrado|Doutorado)\s+(?:Profissional\s+)?em\s+([^)]+)\)', content, re.IGNORECASE)
                if match:
                    found_program = match.group(1).strip()
        except Exception as e:
            if on_progress: on_progress(f"UFGD: Erro Regex Citação: {e}")

        # ESTRATÉGIA B: Meta Tag Específica do Programa (Fallback)
        # Ex: <meta name="DC.publisher.program" content="Programa de pós-graduação em...">
        if not found_program:
            try:
                prog_meta = soup.find('meta', attrs={'name': 'DC.publisher.program'})
                if prog_meta:
                    raw_text = prog_meta.get('content', '')
                    # Remove o prefixo comum para limpar o nome
                    found_program = re.sub(r'^Programa de pós-graduação em\s+', '', raw_text, flags=re.IGNORECASE).strip()
            except: pass

        if found_program:
            data['programa'] = found_program
            if on_progress: on_progress(f"UFGD: Programa detectado: {found_program}")
        else:
            if on_progress: on_progress("UFGD: Programa não identificado.")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            pdf_url = None
            
            # ESTRATÉGIA A: Meta Tag 'citation_pdf_url' (Padrão DSpace/Google)
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # ESTRATÉGIA B: Link visual na tabela de arquivos
            if not pdf_url:
                # Procura link que contenha bitstream e termine em pdf
                link_tag = soup.find('a', href=lambda h: h and 'bitstream' in h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta (importante para DSpace)
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UFGD: PDF localizado.")
            else:
                if on_progress: on_progress("UFGD: PDF não encontrado.")

        except Exception as e:
            if on_progress: on_progress(f"UFGD: Erro PDF: {e}")

        return data