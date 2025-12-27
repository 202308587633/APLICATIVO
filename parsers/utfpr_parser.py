import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UTFPRParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UTFPR", universidade="Universidade Tecnológica Federal do Paraná")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UTFPR (DSpace 6.3 - JSPUI).
        Foca na tabela 'itemDisplayTable' para encontrar o Programa e meta tags para o PDF.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UTFPR: Analisando estrutura da página (JSPUI)...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # O HTML mostra que os dados estão em uma tabela com classe 'itemDisplayTable'
            # Procuramos a linha que contém "Aparece nas coleções"
            # Ex: <tr><td class="metadataFieldLabel">Aparece nas coleções:</td><td class="metadataFieldValue"><a ...>PB - Programa de Pós-Graduação em Letras</a></td></tr>
            
            target_labels = ["Aparece nas coleções", "Appears in Collections"]
            
            for label_text in target_labels:
                label_td = soup.find('td', class_='metadataFieldLabel', string=re.compile(label_text, re.IGNORECASE))
                if label_td:
                    value_td = label_td.find_next_sibling('td', class_='metadataFieldValue')
                    if value_td:
                        # Geralmente há um link <a> com o nome da coleção/programa
                        links = value_td.find_all('a')
                        for link in links:
                            text = link.get_text(strip=True)
                            # Filtro para garantir que é um programa
                            if "Programa" in text or "Mestrado" in text or "Doutorado" in text:
                                found_program = text
                                break
                    if found_program:
                        break

            if found_program:
                # Limpeza:
                # Ex: "PB - Programa de Pós-Graduação em Letras" -> "Letras"
                # Ex: "CP - Programa de Pós-Graduação em Tecnologia (PPGTE)" -> "Tecnologia"
                
                # 1. Remove prefixos de campus (XX - )
                clean_name = re.sub(r'^[A-Z]{2,3}\s*-\s*', '', found_program)
                
                # 2. Remove "Programa de Pós-Graduação em/no/na"
                clean_name = re.sub(r'Programa de Pós-Graduação (?:em|no|na)\s*', '', clean_name, flags=re.IGNORECASE)
                
                # 3. Remove siglas entre parênteses no final (ex: (PPGTE))
                clean_name = re.sub(r'\s*\([A-Z0-9-]+\)$', '', clean_name)
                
                data['programa'] = clean_name.strip()
                if on_progress: on_progress(f"UTFPR: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"UTFPR: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UTFPR: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Presente no HTML fornecido)
            # <meta name="citation_pdf_url" content="...">
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link na tabela de arquivos "Files in This Item"
            if not pdf_url:
                # Procura links que contenham 'bitstream' e terminem em .pdf
                link_tag = soup.find('a', href=lambda h: h and '/bitstream/' in h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta (O HTML mostra que citation_pdf_url já pode ser absoluta, mas hrefs podem ser relativos)
                # No exemplo: http://repositorio.utfpr.edu.br:8080/jspui/bitstream/...
                if pdf_url.startswith('/'):
                    # Ajusta base se necessário (o exemplo usa porta 8080)
                    base_url = "http://repositorio.utfpr.edu.br/jspui/" 
                    if '/jspui' in pdf_url:
                         base_url = "http://repositorio.utfpr.edu.br"
                    
                    pdf_url = urljoin(base_url, pdf_url)
                
                data['link_pdf'] = pdf_url
                if on_progress: on_progress("UTFPR: PDF localizado.")
            else:
                if on_progress: on_progress("UTFPR: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UTFPR: Erro PDF: {str(e)[:20]}")

        return data
    
