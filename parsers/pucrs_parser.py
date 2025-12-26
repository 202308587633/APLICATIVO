import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class PUCRSParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="PUCRS", universidade="Pontifícia Universidade Católica do Rio Grande do Sul")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da PUCRS (DSpace 4.2).
        Utiliza IDs específicos da tabela de metadados para identificar o Programa.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("PUCRS: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia 1: Busca pelo ID específico na tabela de metadados (Muito confiável na PUCRS)
            # <td id="label.dc.publisher.program" ...>Programa:</td><td ...>...</td>
            program_label = soup.find('td', id='label.dc.publisher.program')
            if program_label:
                value_td = program_label.find_next_sibling('td')
                if value_td:
                    found_program = value_td.get_text(strip=True)

            # Estratégia 2: Breadcrumbs (Fallback)
            if not found_program:
                # <ol class="breadcrumb"> ... <li><a ...>Programa de Pós-Graduação em ...</a></li>
                crumbs = soup.select('ol.breadcrumb li a')
                for crumb in crumbs:
                    text = crumb.get_text(strip=True)
                    if "Programa de Pós-Graduação" in text:
                        found_program = text
                        break

            # Limpeza do nome
            if found_program:
                # Remove "Programa de Pós-Graduação em/no/na"
                clean_name = re.sub(
                    r'Programa de Pós-Graduação (em|no|na)?\s*', 
                    '', 
                    found_program, 
                    flags=re.IGNORECASE
                )
                data['programa'] = clean_name.strip()
                if on_progress: on_progress(f"PUCRS: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"PUCRS: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("PUCRS: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Presente no HTML)
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link na tabela de arquivos
            if not pdf_url:
                # Procura links que terminam em .pdf
                link_tag = soup.find('a', href=lambda h: h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("PUCRS: PDF localizado.")
            else:
                if on_progress: on_progress("PUCRS: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"PUCRS: Erro PDF: {str(e)[:20]}")

        return data