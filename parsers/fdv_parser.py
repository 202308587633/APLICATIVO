import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class FDVParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="FDV", universidade="Faculdade de Direito de Vitória")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da FDV (DSpace 5.7).
        Foca na tabela de metadados para Programa (via Editor ou Citação) e meta tags para o PDF.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("FDV: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # A FDV usa o campo "Editor" para indicar a Faculdade (que é Direito)
            # ou "Citação" que contém o nome do Programa
            
            # Estratégia 1: Citação Bibliográfica (Mais preciso para o Programa)
            # Ex: "... (Mestrado em Direitos e Garantias Fundamentais) - Programa de Pós-Graduação em ..."
            citation_meta = soup.find('meta', attrs={'name': 'DCTERMS.bibliographicCitation'})
            if citation_meta:
                content = citation_meta.get('content', '')
                # Tenta extrair o nome do programa
                match = re.search(r'Programa de Pós-Graduação em ([^,]+)', content, re.IGNORECASE)
                if match:
                    found_program = match.group(1).strip()
            
            # Estratégia 2: Campo Editor (Conforme solicitado no exemplo)
            # Ex: <tr><td class="metadataFieldLabel">Editor:&nbsp;</td><td class="metadataFieldValue">Faculdade de Direito de Vitoria</td></tr>
            if not found_program:
                editor_td = soup.find('td', class_='metadataFieldLabel', string=re.compile(r'Editor', re.I))
                if editor_td:
                    value_td = editor_td.find_next_sibling('td', class_='metadataFieldValue')
                    if value_td:
                        text = value_td.get_text(strip=True)
                        if "Faculdade de Direito" in text:
                            found_program = "Direito"
                        else:
                            found_program = text

            if found_program:
                data['programa'] = found_program
                if on_progress: on_progress(f"FDV: Programa identificado: {found_program}")

        except Exception as e:
            if on_progress: on_progress(f"FDV: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("FDV: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Padrão)
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link na tabela de arquivos ("Visualizar/Abrir")
            if not pdf_url:
                # Procura links que contenham 'bitstream' e terminem em .pdf
                link_tag = soup.find('a', href=lambda h: h and 'bitstream' in h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("FDV: PDF localizado.")
            else:
                if on_progress: on_progress("FDV: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"FDV: Erro PDF: {str(e)[:20]}")

        return data