import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UFFParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UFF", universidade="Universidade Federal Fluminense")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UFF (DSpace 6.3).
        Prioriza breadcrumbs para o Programa e meta tags para o PDF.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UFF: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        found_program = None
        
        # Regex para limpar:
        # Remove "Sigla - ", "Programa de Pós-Graduação em" e sufixos como " - Niterói"
        # Ex: "PPGDC - Programa de Pós-Graduação em Direito Constitucional - Niterói"
        # Captura: "Direito Constitucional"
        regex_prog = r'Programa de Pós-Graduação (?:Stricto Sensu )?em\s+([^-]+)'

        try:
            # ESTRATÉGIA A: Breadcrumbs (Conforme solicitado)
            # <ul class="breadcrumb hidden-xs"> ... <li><a>...</a></li>
            crumbs = soup.select('ul.breadcrumb li a')
            for crumb in crumbs:
                text = crumb.get_text(strip=True)
                if "Programa de Pós-Graduação" in text:
                    match = re.search(regex_prog, text, re.IGNORECASE)
                    if match:
                        found_program = match.group(1).strip()
                        break
            
            # ESTRATÉGIA B: Citação Bibliográfica (Fallback)
            # Ex: "... – Programa de Pós-Graduação Stricto Sensu em Direito Constitucional, ..."
            if not found_program:
                meta_cit = soup.find('meta', attrs={'name': 'DCTERMS.bibliographicCitation'})
                if meta_cit:
                    content = meta_cit.get('content', '')
                    match = re.search(regex_prog, content, re.IGNORECASE)
                    if match:
                        found_program = match.group(1).strip()

            if found_program:
                data['programa'] = found_program
                if on_progress: on_progress(f"UFF: Programa identificado: {found_program}")
            else:
                if on_progress: on_progress("UFF: Programa não encontrado.")

        except Exception as e:
            if on_progress: on_progress(f"UFF: Erro Programa: {e}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            pdf_url = None
            
            # ESTRATÉGIA A: Meta Tag 'citation_pdf_url'
            # <meta content="https://..." name="citation_pdf_url">
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # ESTRATÉGIA B: Link Visual (Thumbnail ou Texto)
            if not pdf_url:
                # Procura link para bitstream que termine em .pdf
                link_tag = soup.find('a', href=lambda h: h and 'bitstream' in h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UFF: PDF localizado.")
            else:
                if on_progress: on_progress("UFF: PDF não encontrado.")

        except Exception as e:
            if on_progress: on_progress(f"UFF: Erro PDF: {e}")

        return data