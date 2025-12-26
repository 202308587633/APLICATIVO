import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UFPAParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UFPA", universidade="Universidade Federal do Pará")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UFPA (DSpace 7+).
        Busca o programa no campo de metadado específico ou breadcrumbs, e o PDF via meta tags.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UFPA: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia 1: Busca pelo campo de metadado "Programa" (Específico do layout da UFPA)
            # <h2 class="simple-view-element-header">Programa</h2>
            headers = soup.find_all('h2', class_='simple-view-element-header')
            
            for header in headers:
                if "Programa" in header.get_text(strip=True):
                    # O valor está na div irmã (body) logo após o header
                    body = header.find_next_sibling('div', class_='simple-view-element-body')
                    if body:
                        text = body.get_text(strip=True)
                        found_program = text
                        break
            
            # Estratégia 2: Breadcrumbs (Fallback)
            if not found_program:
                crumbs = soup.select('ol.breadcrumb li a')
                for crumb in crumbs:
                    text = crumb.get_text(strip=True)
                    if "Programa de Pós-Graduação" in text:
                        found_program = text
                        break

            # Limpeza do nome do programa
            if found_program:
                # Remove "Programa de Pós-Graduação em/no/na"
                clean_name = re.sub(
                    r'.*Programa de Pós-Graduação\s*(em|no|na)?\s*', 
                    '', 
                    found_program, 
                    flags=re.IGNORECASE
                )
                
                # Remove sufixos como "- PPGEDAM/NUMA" se houver hífen
                if ' - ' in clean_name:
                    clean_name = clean_name.split(' - ')[0]

                data['programa'] = clean_name.strip()
                if on_progress: on_progress(f"UFPA: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"UFPA: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UFPA: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Padrão e presente no HTML da UFPA)
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link direto na lista de arquivos (Layout Angular)
            if not pdf_url:
                # Procura links que contenham '/bitstreams/' e '/download'
                link_tag = soup.find('a', href=lambda h: h and '/bitstreams/' in h and '/download' in h)
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UFPA: PDF localizado.")
            else:
                if on_progress: on_progress("UFPA: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UFPA: Erro PDF: {str(e)[:20]}")

        return data