import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class PUCGOIASParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="PUC Goiás", universidade="Pontifícia Universidade Católica de Goiás")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da PUC Goiás (DSpace 4.2).
        Prioriza breadcrumbs e meta tags DC.publisher.program.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("PUC Goiás: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        found_program = None
        
        # Regex para limpar prefixos comuns na PUC Goiás
        # Ex: "Programa de Pós-Graduação STRICTO SENSU em Psicologia" -> "Psicologia"
        regex_clean = r'^Programa de Pós-Graduação(?: STRICTO SENSU)?(?: em)?\s+'

        try:
            # ESTRATÉGIA A: Breadcrumbs (Conforme destaque do usuário)
            # <ol class="breadcrumb btn-success"> ... <li><a...>Programa...</a></li>
            crumbs = soup.select('ol.breadcrumb li a')
            for crumb in crumbs:
                text = crumb.get_text(strip=True)
                if "Programa de Pós-Graduação" in text:
                    # Remove o prefixo e fica só com o nome do curso
                    found_program = re.sub(regex_clean, '', text, flags=re.IGNORECASE).strip()
                    break
            
            # ESTRATÉGIA B: Meta Tag Específica (DC.publisher.program)
            # Ex: <meta name="DC.publisher.program" content="Programa de Pós-Graduação STRICTO SENSU em Psicologia">
            if not found_program:
                meta_prog = soup.find('meta', attrs={'name': 'DC.publisher.program'})
                if meta_prog:
                    content = meta_prog.get('content', '')
                    found_program = re.sub(regex_clean, '', content, flags=re.IGNORECASE).strip()

            # ESTRATÉGIA C: Citação Bibliográfica (Fallback)
            if not found_program:
                meta_cit = soup.find('meta', attrs={'name': 'DCTERMS.bibliographicCitation'})
                if meta_cit:
                    # Procura por "Mestrado em X" ou "Doutorado em X"
                    match = re.search(r'\((?:Mestrado|Doutorado) em ([^)]+)\)', meta_cit.get('content', ''), re.IGNORECASE)
                    if match:
                        found_program = match.group(1).strip()

            if found_program:
                data['programa'] = found_program
                if on_progress: on_progress(f"PUC Goiás: Programa identificado: {found_program}")
            else:
                if on_progress: on_progress("PUC Goiás: Programa não encontrado.")

        except Exception as e:
            if on_progress: on_progress(f"PUC Goiás: Erro Programa: {e}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            pdf_url = None
            
            # ESTRATÉGIA A: Meta Tag 'citation_pdf_url'
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # ESTRATÉGIA B: Botão Visual "Baixar/Abrir" ou Link Bitstream
            if not pdf_url:
                link_tag = soup.find('a', href=lambda h: h and 'bitstream' in h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("PUC Goiás: PDF localizado.")
            else:
                if on_progress: on_progress("PUC Goiás: PDF não encontrado.")

        except Exception as e:
            if on_progress: on_progress(f"PUC Goiás: Erro PDF: {e}")

        return data