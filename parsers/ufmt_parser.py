import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UFMTParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UFMT", universidade="Universidade Federal de Mato Grosso")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UFMT.
        Identifica o programa pela classe CSS 'program'.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UFMT: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # O HTML da UFMT usa a classe "program"
            # Ex: <a class="program" ...>Programa de Pós-Graduação em Economia</a>
            prog_link = soup.find('a', class_='program')
            
            if prog_link:
                raw_text = prog_link.get_text(strip=True)
                
                # Regex para remover "Programa de Pós-Graduação em/no/na"
                clean_name = re.sub(
                    r'^Programa de Pós-Graduação\s*(em|no|na)?\s*', 
                    '', 
                    raw_text, 
                    flags=re.IGNORECASE
                )
                
                found_program = clean_name.strip()

            if found_program:
                data['programa'] = found_program
                if on_progress: on_progress(f"UFMT: Programa identificado: {found_program}")
            else:
                # Fallback: Tenta meta tags padrão se a classe mudar
                meta_prog = soup.find('meta', attrs={'name': 'citation_publisher'})
                if meta_prog:
                    data['programa'] = meta_prog.get('content')

        except Exception as e:
            if on_progress: on_progress(f"UFMT: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UFMT: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link com 'bitstream' (Padrão DSpace)
            if not pdf_url:
                link_tag = soup.find('a', href=lambda h: h and 'bitstream' in h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UFMT: PDF localizado.")
            else:
                if on_progress: on_progress("UFMT: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UFMT: Erro PDF: {str(e)[:20]}")

        return data