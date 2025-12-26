import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UNICESUMARParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UNICESUMAR", universidade="Universidade Cesumar")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UNICESUMAR (DSpace 6.3).
        Utiliza classes CSS específicas dos metadados (dc_publisher_program) para precisão.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UNICESUMAR: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia 1: Busca pela classe específica do DSpace
            # O HTML mostra: <td class="metadataFieldValue dc_publisher_program">...</td>
            prog_td = soup.find('td', class_='metadataFieldValue dc_publisher_program')
            if prog_td:
                found_program = prog_td.get_text(strip=True)
            
            # Estratégia 2: Busca por meta tags (Padrão Dublin Core)
            # <meta name="DC.publisher" content="Ciências Jurídicas (Mestrado)">
            if not found_program:
                publishers = soup.find_all('meta', attrs={'name': 'DC.publisher'})
                for meta in publishers:
                    content = meta.get('content', '')
                    # Verifica se parece um programa (tem parênteses indicando grau ou palavras chave)
                    if '(' in content and any(k in content for k in ['Mestrado', 'Doutorado']):
                        found_program = content
                        break

            if found_program:
                # Limpeza: remove "(Mestrado)", "(Doutorado)", "Programa de Pós-Graduação em"
                # Ex: "Ciências Jurídicas (Mestrado)" -> "Ciências Jurídicas"
                clean_name = re.sub(
                    r'\s*\(?(Mestrado|Doutorado).*?\)?', 
                    '', 
                    found_program, 
                    flags=re.IGNORECASE
                )
                clean_name = re.sub(
                    r'Programa de Pós-Graduação (em|no|na)?\s*', 
                    '', 
                    clean_name, 
                    flags=re.IGNORECASE
                )
                
                data['programa'] = clean_name.strip()
                if on_progress: on_progress(f"UNICESUMAR: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"UNICESUMAR: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UNICESUMAR: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Padrão e presente no HTML)
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link na tabela de arquivos
            if not pdf_url:
                # Procura links que contenham '/bitstream/' e terminem em .pdf
                link_tag = soup.find('a', href=lambda h: h and '/bitstream/' in h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UNICESUMAR: PDF localizado.")
            else:
                if on_progress: on_progress("UNICESUMAR: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UNICESUMAR: Erro PDF: {str(e)[:20]}")

        return data
    
    