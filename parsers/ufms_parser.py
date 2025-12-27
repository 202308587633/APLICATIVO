import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UFMSParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UFMS", universidade="Universidade Federal de Mato Grosso do Sul")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UFMS (DSpace 6.3 - JSPUI).
        Foca na tabela 'itemDisplayTable' para encontrar o Programa e meta tags para o PDF.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UFMS: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # O HTML mostra que os dados estão em uma tabela com classe 'itemDisplayTable'
            # Procuramos a célula que contém "Aparece nas coleções" ou "Appears in Collections"
            # Exemplo: <tr><td class="metadataFieldLabel">Aparece nas coleções:</td><td class="metadataFieldValue"><a ...>...</a></td></tr>
            
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
                            # Filtro para garantir que é um programa e não uma coleção genérica
                            if "Programa" in text or "Mestrado" in text or "Doutorado" in text:
                                found_program = text
                                break
                    if found_program:
                        break

            if found_program:
                # Limpeza:
                # Ex: "CPTL - Programa de Pós-Graduação em Letras (PPGLetras)" -> "Letras"
                
                # 1. Remove prefixos comuns (CPTL -, FAALC -, etc) se houver "Programa..." depois
                if "Programa de" in found_program:
                    clean_name = re.sub(r'.*?Programa de Pós-Graduação em\s*', '', found_program, flags=re.IGNORECASE)
                elif "Mestrado" in found_program:
                    clean_name = re.sub(r'.*?Mestrado (?:Profissional |Acadêmico )?em\s*', '', found_program, flags=re.IGNORECASE)
                elif "Doutorado" in found_program:
                    clean_name = re.sub(r'.*?Doutorado em\s*', '', found_program, flags=re.IGNORECASE)
                else:
                    clean_name = found_program

                # 2. Remove sufixos entre parênteses (ex: (PPGLetras)) ou após traços
                # Mas cuidado para não cortar nomes compostos sem querer. 
                # No exemplo: "Letras (PPGLetras)" -> "Letras"
                clean_name = re.split(r'\(', clean_name)[0]
                
                data['programa'] = clean_name.strip()
                if on_progress: on_progress(f"UFMS: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"UFMS: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UFMS: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Presente no HTML fornecido)
            # <meta name="citation_pdf_url" content="...">
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link na tabela de arquivos (Backup)
            if not pdf_url:
                # Procura links que contenham 'bitstream' e terminem em .pdf
                link_tag = soup.find('a', href=lambda h: h and '/bitstream/' in h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UFMS: PDF localizado.")
            else:
                if on_progress: on_progress("UFMS: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UFMS: Erro PDF: {str(e)[:20]}")

        return data
    