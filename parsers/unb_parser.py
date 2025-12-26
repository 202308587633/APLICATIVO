import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UnbParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UNB", universidade="Universidade de Brasília")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UNB.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UNB: Analisando HTML...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Tática 1: Busca em links com "Programa de Pós-Graduação"
            # A UnB geralmente coloca isso na tabela de metadados ou breadcrumbs
            prog_link = soup.find('a', string=re.compile(r'Programa de Pós-[Gg]raduação', re.I))
            if prog_link:
                found_program = prog_link.get_text(strip=True)
            
            # Tática 2: Busca por meta tags (DC.publisher)
            if not found_program:
                metas = soup.find_all('meta', attrs={'name': ['DC.publisher', 'citation_publisher']})
                for meta in metas:
                    content = meta.get('content', '')
                    if "Programa" in content or "Mestrado" in content or "Doutorado" in content:
                        # Evita pegar só o nome da universidade
                        if len(content) > len("Universidade de Brasília") + 5:
                            found_program = content
                            break

            # Limpeza
            if found_program:
                # Remove "Programa de Pós-Graduação em"
                clean_name = re.sub(
                    r'^(Programa de Pós-[Gg]raduação|Mestrado|Doutorado)\s*(em|no|na)?\s+', 
                    '', 
                    found_program, 
                    flags=re.IGNORECASE
                )
                data['programa'] = clean_name.strip(' .;-')
                if on_progress: on_progress(f"UNB: Programa identificado: {data['programa']}")
            else:
                if on_progress: on_progress("UNB: Programa não identificado.")

        except Exception as e:
            if on_progress: on_progress(f"UNB: Erro programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            pdf_url = None
            
            # Tática 1: Meta Tag citation_pdf_url
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Tática 2: Links bitstream
            if not pdf_url:
                links = soup.find_all('a', href=True)
                for link in links:
                    href = link['href']
                    if 'bitstream' in href and href.lower().endswith('.pdf'):
                        # Evita links de "license" ou "policy"
                        if 'license' not in href.lower() and 'policy' not in href.lower():
                            pdf_url = href
                            break

            if pdf_url:
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UNB: PDF localizado.")
            else:
                if on_progress: on_progress("UNB: PDF não encontrado.")

        except Exception as e:
            if on_progress: on_progress(f"UNB: Erro PDF: {str(e)[:20]}")

        return data