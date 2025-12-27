import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UFFSParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UFFS", universidade="Universidade Federal da Fronteira Sul")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UFFS (DSpace 5.2).
        Utiliza a tabela de metadados para encontrar o Programa e meta tags para o PDF.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UFFS: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia 1: Busca na tabela de metadados pelo label específico (em inglês no HTML fornecido)
            # <td class="metadataFieldLabel">Name of Program of Postgraduate studies:&nbsp;</td>
            # <td class="metadataFieldValue">Programa de Pós-Graduação em História</td>
            
            # Procura por células que contenham o texto chave
            target_labels = ["Name of Program of Postgraduate studies", "Programa de Pós-Graduação"]
            
            for label_text in target_labels:
                label_td = soup.find('td', class_='metadataFieldLabel', string=re.compile(label_text, re.IGNORECASE))
                if label_td:
                    value_td = label_td.find_next_sibling('td', class_='metadataFieldValue')
                    if value_td:
                        found_program = value_td.get_text(strip=True)
                        break

            # Estratégia 2: Busca por meta tags (DC.publisher)
            # O HTML tem vários DC.publisher, um deles é o programa.
            if not found_program:
                publishers = soup.find_all('meta', attrs={'name': 'DC.publisher'})
                for meta in publishers:
                    content = meta.get('content', '')
                    if "Programa de Pós-Graduação" in content:
                        found_program = content
                        break

            if found_program:
                # Limpeza: remove "Programa de Pós-Graduação em/no/na"
                clean_name = re.sub(
                    r'Programa de Pós-Graduação (em|no|na)?\s*', 
                    '', 
                    found_program, 
                    flags=re.IGNORECASE
                )
                
                data['programa'] = clean_name.strip()
                if on_progress: on_progress(f"UFFS: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"UFFS: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UFFS: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Presente no HTML fornecido)
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link na tabela de arquivos
            if not pdf_url:
                link_tag = soup.find('a', href=lambda h: h and '/bitstream/' in h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UFFS: PDF localizado.")
            else:
                if on_progress: on_progress("UFFS: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UFFS: Erro PDF: {str(e)[:20]}")

        return data
    
    