import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class PUCSPParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="PUCSP", universidade="Pontifícia Universidade Católica de São Paulo")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da PUCSP (DSpace).
        Identifica o departamento/programa via classes de metadados na tabela.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("PUCSP: Analisando tabela de metadados...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # O HTML da PUCSP usa classes específicas nas TDs de valor
            # Ex: <td class="metadataFieldValue dc_publisher_department">Faculdade de Direito</td>
            # Procuramos por 'program' ou 'department' nas classes
            target_td = soup.find('td', class_=lambda c: c and 'metadataFieldValue' in c and ('dc_publisher_program' in c or 'dc_publisher_department' in c))
            
            if target_td:
                raw_text = target_td.get_text(strip=True)
                
                # Regex poderosa para limpar os variados prefixos da PUCSP
                # Remove: "Faculdade de", "Programa de Pós-Graduação em", "Programa de Estudos Pós-Graduados em"
                clean_name = re.sub(
                    r'^(Faculdade de|Programa de Pós-Graduação\s*(em|no|na)?|Programa de Estudos Pós-Graduados\s*(em|no|na)?)\s*', 
                    '', 
                    raw_text, 
                    flags=re.IGNORECASE
                )
                
                found_program = clean_name.strip()

            if found_program:
                data['programa'] = found_program
                if on_progress: on_progress(f"PUCSP: Programa identificado: {found_program}")
            else:
                # Fallback: Meta tags padrão
                meta_prog = soup.find('meta', attrs={'name': 'citation_publisher'})
                if meta_prog:
                    data['programa'] = meta_prog.get('content')

        except Exception as e:
            if on_progress: on_progress(f"PUCSP: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("PUCSP: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link com 'bitstream' (Padrão DSpace PUCSP)
            if not pdf_url:
                link_tag = soup.find('a', href=lambda h: h and 'bitstream' in h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("PUCSP: PDF localizado.")
            else:
                if on_progress: on_progress("PUCSP: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"PUCSP: Erro PDF: {str(e)[:20]}")

        return data