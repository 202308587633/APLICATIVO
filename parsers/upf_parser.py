import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UPFParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UPF", universidade="Universidade de Passo Fundo")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UPF (DSpace 7/8).
        Utiliza a estrutura de classes 'simple-view-element' para metadados e meta tags para PDF.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UPF: Analisando estrutura da página (DSpace 7+)...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # O DSpace 7 estrutura os metadados em blocos:
            # <div class="simple-view-element">
            #    <h2 class="simple-view-element-header">Label</h2>
            #    <div class="simple-view-element-body">Value</div>
            # </div>
            
            elements = soup.find_all('div', class_='simple-view-element')
            
            for el in elements:
                header = el.find(['h2', 'h3', 'h4', 'h5'], class_='simple-view-element-header')
                if header:
                    header_text = header.get_text(strip=True)
                    
                    # Procura pelo cabeçalho "Programa de Pós-graduação" (conforme seu exemplo)
                    # Também verifica "Programa" para ser mais genérico
                    if "Programa" in header_text or "Pós-graduação" in header_text:
                        body = el.find('div', class_='simple-view-element-body')
                        if body:
                            found_program = body.get_text(strip=True)
                            break
            
            # Fallback: Tenta achar nos breadcrumbs se não achou no metadado explícito
            if not found_program:
                crumbs = soup.select('ol.breadcrumb li')
                for crumb in crumbs:
                    text = crumb.get_text(strip=True)
                    # Geralmente o programa aparece nos breadcrumbs em DSpace
                    if "Programa de" in text or "Mestrado" in text or "Doutorado" in text:
                        found_program = text

            if found_program:
                # Limpeza: remove "Programa de Pós-Graduação em"
                clean_name = re.sub(
                    r'Programa de Pós-Graduação (em|no|na)?\s*', 
                    '', 
                    found_program, 
                    flags=re.IGNORECASE
                )
                data['programa'] = clean_name.strip()
                if on_progress: on_progress(f"UPF: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"UPF: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UPF: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Presente e confiável no exemplo)
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link na seção de arquivos (DSpace 7)
            if not pdf_url:
                # Procura links que contenham '/bitstreams/' e '/download'
                link_tag = soup.find('a', href=lambda h: h and '/bitstreams/' in h and '/download' in h)
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UPF: PDF localizado.")
            else:
                if on_progress: on_progress("UPF: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UPF: Erro PDF: {str(e)[:20]}")

        return data
    