import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class FDVParser(BaseParser):
    def __init__(self):
        # Define a Sigla e o Nome padrão conforme solicitado
        super().__init__(sigla="FDV", universidade="Faculdade de Direito de Vitória")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da FDV (DSpace 5.7).
        Baseado no padrão de citação: "... - Programa de Pós-Graduação em [NOME], ..."
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("FDV: Analisando metadados e citações...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        # Padrão regex: Procura "Programa de Pós-Graduação em" e captura tudo até a próxima vírgula ou fim da linha.
        # Ex: "... - Programa de Pós-Graduação em Direitos e Garantias Fundamentais, Faculdade..."
        regex_programa = r'Programa de Pós-Graduação em\s+([^,]+)'
        
        found_program = None
        raw_citation_text = ""

        # ESTRATÉGIA A: Meta Tag (Geralmente mais limpa)
        # <meta name="DCTERMS.bibliographicCitation" content="...">
        try:
            meta_cit = soup.find('meta', attrs={'name': 'DCTERMS.bibliographicCitation'})
            if meta_cit:
                raw_citation_text = meta_cit.get('content', '')
                match = re.search(regex_programa, raw_citation_text, re.IGNORECASE)
                if match:
                    found_program = match.group(1).strip()
        except Exception as e:
            pass

        # ESTRATÉGIA B: Tabela Visual (Citation / Citação)
        # <tr><td class="metadataFieldLabel">Citation:&nbsp;</td><td class="metadataFieldValue">...</td></tr>
        if not found_program:
            try:
                # Procura célula que contenha "Citation" ou "Citação"
                label_td = soup.find('td', class_='metadataFieldLabel', string=re.compile(r'Cita(tion|ção)', re.IGNORECASE))
                if label_td:
                    value_td = label_td.find_next_sibling('td', class_='metadataFieldValue')
                    if value_td:
                        raw_text = value_td.get_text(" ", strip=True)
                        match = re.search(regex_programa, raw_text, re.IGNORECASE)
                        if match:
                            found_program = match.group(1).strip()
            except Exception:
                pass

        if found_program:
            data['programa'] = found_program
            if on_progress: on_progress(f"FDV: Programa identificado: {found_program}")
        else:
            if on_progress: on_progress("FDV: Programa não encontrado na citação.")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            pdf_url = None
            
            # ESTRATÉGIA A: Meta Tag 'citation_pdf_url' (Padrão Google Scholar/DSpace)
            # Ex: <meta name="citation_pdf_url" content="http://.../bitstream/.../arquivo.pdf">
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta and pdf_meta.get('content'):
                pdf_url = pdf_meta.get('content')

            # ESTRATÉGIA B: Botão de Download na tabela "Files in This Item"
            # Procura links que contenham 'bitstream' e terminem em .pdf
            if not pdf_url:
                # Procura especificamente dentro da tabela de arquivos para evitar links duplicados
                file_table = soup.find('table', class_='panel-body')
                if file_table:
                    link_tag = file_table.find('a', href=True)
                    if link_tag:
                        href = link_tag['href']
                        if href.lower().endswith('.pdf'):
                            pdf_url = href

            if pdf_url:
                # Garante que o link seja absoluto (caso venha /bitstream/...)
                # O urljoin resolve problemas com IPs ou domínios
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("FDV: PDF localizado.")
            else:
                data['link_pdf'] = '-'
                if on_progress: on_progress("FDV: PDF não encontrado.")

        except Exception as e:
            if on_progress: on_progress(f"FDV: Erro na extração do PDF: {str(e)}")

        return data
    