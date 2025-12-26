import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UFSMParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UFSM", universidade="Universidade Federal de Santa Maria")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UFSM (DSpace).
        Busca o programa na seção 'Coleções' ou Meta Tags e o PDF via metadados padrão.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UFSM: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia 1: Seção "Coleções" (Conforme exemplo fornecido)
            # <div class="simple-item-view-collections ..."> ... <a ...>Programa de Pós-Graduação em Direito</a>
            collection_links = soup.select('div.simple-item-view-collections ul.ds-referenceSet-list li a')
            
            for link in collection_links:
                text = link.get_text(strip=True)
                
                if "Programa de Pós-Graduação" in text:
                    # Remove "Programa de Pós-Graduação em/no/na" para sobrar apenas "Direito"
                    clean_name = re.sub(
                        r'.*Programa de Pós-Graduação\s*(em|no|na)?\s*', 
                        '', 
                        text, 
                        flags=re.IGNORECASE
                    )
                    found_program = clean_name.strip()
                    break
            
            # Estratégia 2: Meta Tags (Fallback)
            # A UFSM usa <meta name="DC.publisher" content="Programa de Pós-Graduação em Direito">
            if not found_program:
                meta_publishers = soup.find_all('meta', attrs={'name': 'DC.publisher'})
                for meta in meta_publishers:
                    content = meta.get('content', '')
                    if "Programa de Pós-Graduação" in content:
                        clean_name = re.sub(
                            r'.*Programa de Pós-Graduação\s*(em|no|na)?\s*', 
                            '', 
                            content, 
                            flags=re.IGNORECASE
                        )
                        found_program = clean_name.strip()
                        break

            if found_program:
                data['programa'] = found_program
                if on_progress: on_progress(f"UFSM: Programa identificado: {found_program}")

        except Exception as e:
            if on_progress: on_progress(f"UFSM: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UFSM: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Padrão e presente no HTML da UFSM)
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link direto na tabela "Visualizar/Abrir"
            if not pdf_url:
                link_tag = soup.find('a', href=lambda h: h and 'bitstream' in h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UFSM: PDF localizado.")
            else:
                if on_progress: on_progress("UFSM: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UFSM: Erro PDF: {str(e)[:20]}")

        return data
    