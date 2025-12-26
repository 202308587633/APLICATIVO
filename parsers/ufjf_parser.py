import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UFJFParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UFJF", universidade="Universidade Federal de Juiz de Fora")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UFJF (DSpace 6.3).
        Utiliza classes CSS específicas dos metadados (dc_publisher_program) para precisão.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UFJF: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia 1: Busca pela classe específica do DSpace da UFJF
            # O HTML mostra: <td class="metadataFieldValue dc_publisher_program">...</td>
            prog_td = soup.find('td', class_='metadataFieldValue dc_publisher_program')
            if prog_td:
                found_program = prog_td.get_text(strip=True)
            
            # Estratégia 2: Busca pelo Label "Program:" ou "Programa:"
            if not found_program:
                label_td = soup.find('td', class_='metadataFieldLabel', string=re.compile(r'Program', re.I))
                if label_td:
                    value_td = label_td.find_next_sibling('td')
                    if value_td:
                        found_program = value_td.get_text(strip=True)

            if found_program:
                # Limpeza: remove "Programa de Pós-graduação em"
                clean_name = re.sub(
                    r'Programa de Pós-graduação (em|no|na)?\s*', 
                    '', 
                    found_program, 
                    flags=re.IGNORECASE
                )
                data['programa'] = clean_name.strip()
                if on_progress: on_progress(f"UFJF: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"UFJF: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UFJF: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Padrão e presente no HTML)
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Botão "View/Open" ou links de bitstream
            if not pdf_url:
                # Procura links na tabela de arquivos ou botões primários
                link_tag = soup.find('a', href=lambda h: h and ('bitstream' in h and h.lower().endswith('.pdf')))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UFJF: PDF localizado.")
            else:
                if on_progress: on_progress("UFJF: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UFJF: Erro PDF: {str(e)[:20]}")

        return data