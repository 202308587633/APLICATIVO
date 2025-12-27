import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UNIOESTEParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UNIOESTE", universidade="Universidade Estadual do Oeste do Paraná")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UNIOESTE (DSpace 4.2 / TEDE).
        Utiliza IDs de tabela específicos do JSPUI e metadados Dublin Core.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UNIOESTE: Analisando estrutura da página (TEDE/DSpace 4)...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia A: Campo explícito "Program" na tabela de metadados (Mais preciso)
            # <td id="label.dc.publisher.program" ...>
            program_row = soup.find('td', id='label.dc.publisher.program')
            if program_row:
                value_td = program_row.find_next_sibling('td', class_='metadataFieldValue')
                if value_td:
                    found_program = value_td.get_text(strip=True)

            # Estratégia B: Extração via Citação (Conforme solicitado no prompt)
            # <td id="label.dc.identifier.citation" ...>
            if not found_program:
                citation_row = soup.find('td', id='label.dc.identifier.citation')
                if citation_row:
                    value_td = citation_row.find_next_sibling('td', class_='metadataFieldValue')
                    if value_td:
                        citation_text = value_td.get_text(strip=True)
                        # Regex para capturar: "Dissertação (Mestrado em XXXXX) - Universidade..."
                        # Captura até encontrar um parêntese fechando ou um hífen
                        match = re.search(
                            r'(?:Mestrado|Doutorado|Mestre|Doutor)(?:\s+Profissional|\s+Acadêmico)?\s+em\s+([^)\-]+)', 
                            citation_text, 
                            re.IGNORECASE
                        )
                        if match:
                            found_program = match.group(1).strip()

            # Estratégia C: Breadcrumbs (Trilha de navegação)
            # Geralmente o penúltimo item é o programa no TEDE
            if not found_program:
                crumbs = soup.select('ol.breadcrumb li')
                if len(crumbs) >= 2:
                    # Ignora o último (título) e pega o anterior
                    candidate = crumbs[-2].get_text(strip=True)
                    if "Programa" in candidate or "Mestrado" in candidate or "Doutorado" in candidate:
                        found_program = candidate

            if found_program:
                # Limpeza: Remove prefixos comuns como "Programa de Pós-Graduação em"
                clean_name = re.sub(
                    r'^(?:Programa de Pós-Graduação|Curso|Mestrado|Doutorado)(?:\s+(?:Profissional|Acadêmico))?(?: em| no| na)?\s*', 
                    '', 
                    found_program, 
                    flags=re.IGNORECASE
                )
                data['programa'] = clean_name.strip('.,- ')
                if on_progress: on_progress(f"UNIOESTE: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"UNIOESTE: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UNIOESTE: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Padrão Google Scholar)
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link na tabela de arquivos "Files in This Item"
            if not pdf_url:
                # Procura links que contenham 'bitstream' e terminem em .pdf
                # Geralmente dentro de uma tabela com class 'panel-body' ou cabeçalho 'File'
                link_tag = soup.find('a', href=lambda h: h and '/bitstream/' in h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UNIOESTE: PDF localizado.")
            else:
                if on_progress: on_progress("UNIOESTE: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UNIOESTE: Erro PDF: {str(e)[:20]}")

        return data
    
    