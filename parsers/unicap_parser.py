import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UNICAPParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UNICAP", universidade="Universidade Católica de Pernambuco")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UNICAP.
        Identifica o programa pela classe 'program' ou pela estrutura da tabela de metadados.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UNICAP: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia A: Link com classe "program" (Padrão visto no HTML)
            # Ex: <a class="program" href="...">Doutorado em Direito</a>
            prog_link = soup.find('a', class_='program')
            
            if prog_link:
                raw_text = prog_link.get_text(strip=True)
                found_program = raw_text

            # Estratégia B: Tabela de Metadados (Fallback)
            # Procura pelo rótulo "Programa:" e pega o valor na próxima célula
            if not found_program:
                label_td = soup.find('td', class_='metadataFieldLabel', string=re.compile(r'Programa:', re.I))
                if label_td:
                    value_td = label_td.find_next_sibling('td', class_='metadataFieldValue')
                    if value_td:
                        found_program = value_td.get_text(strip=True)

            if found_program:
                # Limpeza padrão: remove "Programa de Pós-Graduação em" se houver
                # Mantém "Doutorado em Direito" caso não tenha o prefixo longo
                clean_name = re.sub(
                    r'^Programa de Pós-Graduação\s*(em|no|na)?\s*', 
                    '', 
                    found_program, 
                    flags=re.IGNORECASE
                )
                
                data['programa'] = clean_name.strip()
                if on_progress: on_progress(f"UNICAP: Programa identificado: {data['programa']}")
            else:
                # Fallback: Meta tags
                meta_prog = soup.find('meta', attrs={'name': 'citation_publisher'})
                if meta_prog:
                    data['programa'] = meta_prog.get('content')

        except Exception as e:
            if on_progress: on_progress(f"UNICAP: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UNICAP: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link com 'bitstream'
            if not pdf_url:
                link_tag = soup.find('a', href=lambda h: h and 'bitstream' in h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UNICAP: PDF localizado.")
            else:
                if on_progress: on_progress("UNICAP: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UNICAP: Erro PDF: {str(e)[:20]}")

        return data