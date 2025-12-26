import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UniCEUBParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UniCEUB", universidade="Centro Universitário de Brasília")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório do UniCEUB (DSpace 5.7).
        Foca na tabela de metadados para o Programa (via Coleções) e meta tags para o PDF.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UniCEUB: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia 1: Citação Bibliográfica (Mais preciso quando disponível)
            # Ex: "Tese (Doutorado em Direito)"
            citation_meta = soup.find('meta', attrs={'name': 'DCTERMS.bibliographicCitation'})
            if citation_meta:
                content = citation_meta.get('content', '')
                match = re.search(r'\((Mestrado|Doutorado) em ([^)]+)\)', content, re.IGNORECASE)
                if match:
                    found_program = match.group(2).strip()

            # Estratégia 2: Campo "Aparece nas coleções" (Conforme solicitado)
            # Ex: <a href="...">DIR - Doutorado</a> -> DIR = Direito
            if not found_program:
                collection_label = soup.find('td', class_='metadataFieldLabel', string=re.compile(r'Aparece nas coleções', re.I))
                if collection_label:
                    value_td = collection_label.find_next_sibling('td', class_='metadataFieldValue')
                    if value_td:
                        coll_text = value_td.get_text(strip=True)
                        
                        # Mapeamento de Siglas Específicas do UniCEUB
                        if "DIR" in coll_text:
                            found_program = "Direito"
                        elif "GPP" in coll_text: # Exemplo hipotético para Gestão de Políticas Públicas
                             found_program = "Gestão de Políticas Públicas"
                        else:
                             # Tenta limpar o texto da coleção (Remove " - Doutorado", " - Mestrado")
                             found_program = re.sub(r'\s*-\s*(Mestrado|Doutorado).*', '', coll_text, flags=re.IGNORECASE)

            if found_program:
                data['programa'] = found_program
                if on_progress: on_progress(f"UniCEUB: Programa identificado: {found_program}")

        except Exception as e:
            if on_progress: on_progress(f"UniCEUB: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UniCEUB: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Padrão e presente no HTML)
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
                # Garante URL absoluta (embora a meta tag já traga absoluta)
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UniCEUB: PDF localizado.")
            else:
                if on_progress: on_progress("UniCEUB: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UniCEUB: Erro PDF: {str(e)[:20]}")

        return data