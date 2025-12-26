import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class PUCCampinasParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="PUC-Campinas", universidade="Pontifícia Universidade Católica de Campinas")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da PUC-Campinas (DSpace 6.2).
        Foca nos blocos 'simple-item-view-description' para o programa e meta tags para o PDF.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("PUC-Campinas: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # O layout organiza os metadados em divs com a classe 'simple-item-view-description'
            # Exemplo: 
            # <div class="simple-item-view-description ...">
            #   <h5>Programa de Pós-Graduação</h5>Direito
            # </div>
            
            metadata_divs = soup.find_all('div', class_='simple-item-view-description')
            
            for div in metadata_divs:
                header = div.find('h5')
                if header and "Programa de Pós-Graduação" in header.get_text(strip=True):
                    # O nome do programa está no texto da div, logo após o h5.
                    # Pegamos o texto completo da div e removemos o texto do cabeçalho.
                    full_text = div.get_text(strip=True)
                    header_text = header.get_text(strip=True)
                    
                    found_program = full_text.replace(header_text, "").strip()
                    break
            
            # Fallback: Tenta meta tags se a estrutura visual mudar
            if not found_program:
                # Às vezes programas aparecem como 'publisher' ou 'subject'
                pass 

            if found_program:
                data['programa'] = found_program
                if on_progress: on_progress(f"PUC-Campinas: Programa identificado: {found_program}")

        except Exception as e:
            if on_progress: on_progress(f"PUC-Campinas: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("PUC-Campinas: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Presente no HTML fornecido)
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link na seção "Abrir arquivo"
            if not pdf_url:
                # Procura links que contenham 'bitstream' e terminem em .pdf
                # O HTML mostra links dentro de 'item-page-field-wrapper'
                link_tag = soup.find('a', href=lambda h: h and 'bitstream' in h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("PUC-Campinas: PDF localizado.")
            else:
                if on_progress: on_progress("PUC-Campinas: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"PUC-Campinas: Erro PDF: {str(e)[:20]}")

        return data