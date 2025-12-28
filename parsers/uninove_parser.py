import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UninoveParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UNINOVE", universidade="Universidade Nove de Julho")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UNINOVE (DSpace 4.2).
        Prioriza breadcrumbs para o programa e meta tags para o PDF.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UNINOVE: Analisando HTML...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        found_program = None
        
        # Regex para limpar o prefixo: Remove "Programa de Pós-Graduação em/no/na"
        # Ex: "Programa de Pós-Graduação em Cidades Inteligentes..." -> "Cidades Inteligentes..."
        regex_clean_prog = r'^Programa de Pós-Graduação\s*(em|no|na)?\s*'

        try:
            # ESTRATÉGIA A: Breadcrumbs (Solicitado pelo usuário)
            # <ol class="breadcrumb btn-success"> ... <li><a...>Programa...</a></li>
            crumbs = soup.select('ol.breadcrumb li a')
            for crumb in crumbs:
                text = crumb.get_text(strip=True)
                if "Programa de Pós-Graduação" in text:
                    found_program = re.sub(regex_clean_prog, '', text, flags=re.IGNORECASE).strip()
                    break
            
            # ESTRATÉGIA B: Meta Tags (Fallback robusto)
            # O HTML possui: <meta name="DC.publisher" content="Programa de Pós-Graduação em ...">
            if not found_program:
                meta_pubs = soup.find_all('meta', attrs={'name': 'DC.publisher'})
                for meta in meta_pubs:
                    content = meta.get('content', '')
                    if "Programa de Pós-Graduação" in content:
                        found_program = re.sub(regex_clean_prog, '', content, flags=re.IGNORECASE).strip()
                        break

            if found_program:
                data['programa'] = found_program
                if on_progress: on_progress(f"UNINOVE: Programa detectado: {found_program}")
            else:
                if on_progress: on_progress("UNINOVE: Programa não identificado.")

        except Exception as e:
            if on_progress: on_progress(f"UNINOVE: Erro Programa: {e}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            pdf_url = None
            
            # ESTRATÉGIA A: Meta Tag 'citation_pdf_url' (Padrão e presente no seu HTML)
            # Ex: content="http://bibliotecatede.uninove.br/bitstream/..."
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # ESTRATÉGIA B: Botão Visual "Baixar/Abrir"
            if not pdf_url:
                # No seu HTML o botão é: <a class="btn btn-success" ...>Baixar/Abrir</a>
                link_tag = soup.find('a', string=re.compile(r'Baixar|Abrir|Download', re.I))
                if link_tag and link_tag.get('href'):
                    pdf_url = link_tag['href']

            # ESTRATÉGIA C: Busca genérica por bitstream e .pdf
            if not pdf_url:
                link_tag = soup.find('a', href=lambda h: h and 'bitstream' in h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta (Se vier relativa como /bitstream..., o urljoin corrige)
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UNINOVE: PDF localizado.")
            else:
                if on_progress: on_progress("UNINOVE: PDF não encontrado.")

        except Exception as e:
            if on_progress: on_progress(f"UNINOVE: Erro PDF: {e}")

        return data