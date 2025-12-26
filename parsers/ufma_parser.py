import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UFMAParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UFMA", universidade="Universidade Federal do Maranhão")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UFMA (DSpace 4.2).
        Foca nos breadcrumbs para o Programa e meta tags para o PDF.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UFMA: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia 1: Breadcrumbs (Solicitado)
            # <ol class="breadcrumb btn-success"> ... <li> ... </li> </ol>
            crumbs = soup.select('ol.breadcrumb li a')
            
            for crumb in crumbs:
                text = crumb.get_text(strip=True)
                
                # Procura o item que define o programa
                if "PROGRAMA DE PÓS-GRADUAÇÃO" in text.upper():
                    # Texto cru: "PROGRAMA DE PÓS-GRADUAÇÃO EM DIREITO E INSTITUIÇÕES DO SISTEMA DE JUSTIÇA - PPGDIR"
                    
                    # 1. Remove o prefixo
                    clean_name = re.sub(
                        r'^PROGRAMA DE PÓS-GRADUAÇÃO (EM|NO|NA)?\s*', 
                        '', 
                        text, 
                        flags=re.IGNORECASE
                    )
                    
                    # 2. Remove o sufixo da sigla (ex: " - PPGDIR")
                    clean_name = re.sub(r'\s*-\s*[A-Z0-9]+$', '', clean_name)
                    
                    found_program = clean_name.strip()
                    break
            
            # Estratégia 2: Tabela de Metadados (Fallback)
            # <tr><td ...>Programa:</td><td>...</td></tr>
            if not found_program:
                program_td = soup.find('td', string=re.compile(r'Programa', re.I))
                if program_td:
                    value_td = program_td.find_next_sibling('td')
                    if value_td:
                        text = value_td.get_text(strip=True)
                        # Aplica a mesma limpeza
                        clean_name = re.sub(r'^PROGRAMA DE PÓS-GRADUAÇÃO (EM|NO|NA)?\s*', '', text, flags=re.IGNORECASE)
                        found_program = clean_name.split('/')[0].strip() # Remove /CCSO se houver

            if found_program:
                data['programa'] = found_program
                if on_progress: on_progress(f"UFMA: Programa identificado: {found_program}")

        except Exception as e:
            if on_progress: on_progress(f"UFMA: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UFMA: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Padrão e presente no HTML)
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link na tabela de arquivos ("Baixar/Abrir")
            if not pdf_url:
                link_tag = soup.find('a', href=lambda h: h and 'bitstream' in h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UFMA: PDF localizado.")
            else:
                if on_progress: on_progress("UFMA: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UFMA: Erro PDF: {str(e)[:20]}")

        return data