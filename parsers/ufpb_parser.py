import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UFPBParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UFPB", universidade="Universidade Federal da Paraíba")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UFPB (DSpace 5.7).
        Foca na tabela de metadados genérica para encontrar o Programa.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UFPB: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia 1: Busca na tabela 'itemDisplayTable' por labels específicos
            # O HTML mostra: <tr><td class="metadataFieldLabel">Programa:</td><td class="metadataFieldValue">...</td></tr>
            # Ou: <tr><td class="metadataFieldLabel">Aparece nas coleções:</td><td class="metadataFieldValue">...</td></tr>
            
            # Tenta primeiro o label explícito "Programa:"
            label_td = soup.find('td', class_='metadataFieldLabel', string=re.compile(r'Programa', re.I))
            if label_td:
                value_td = label_td.find_next_sibling('td', class_='metadataFieldValue')
                if value_td:
                    found_program = value_td.get_text(strip=True)

            # Se não achou, tenta "Aparece nas coleções:"
            if not found_program:
                label_td = soup.find('td', class_='metadataFieldLabel', string=re.compile(r'Aparece nas coleções', re.I))
                if label_td:
                    value_td = label_td.find_next_sibling('td', class_='metadataFieldValue')
                    if value_td:
                        text = value_td.get_text(strip=True)
                        # O texto geralmente é longo, ex: "Centro de Ciências Jurídicas (CCJ) - Programa de Pós-Graduação em Ciências Jurídicas"
                        # Vamos tentar extrair a parte do Programa
                        if "Programa de Pós-Graduação" in text:
                            # Pega tudo depois de "Programa de Pós-Graduação [em/no/na]"
                            match = re.search(r'Programa de Pós-Graduação\s*(?:em|no|na)?\s+(.*)', text, re.IGNORECASE)
                            if match:
                                found_program = match.group(1).strip()
                            else:
                                found_program = text # Fallback: pega tudo
                        else:
                            # Tenta pegar a última parte se houver hífen (comum em hierarquias)
                            parts = text.split(' - ')
                            if len(parts) > 1:
                                found_program = parts[-1].strip()
                            else:
                                found_program = text

            if found_program:
                # Limpeza final: remove "Programa de Pós-Graduação em" se ainda estiver lá (caso tenha vindo direto do label "Programa")
                clean_name = re.sub(
                    r'^(?:Programa de Pós-Graduação|Mestrado|Doutorado)(?:\s+(?:Profissional|Acadêmico))?\s*(?:em|no|na)?\s*', 
                    '', 
                    found_program, 
                    flags=re.IGNORECASE
                )
                data['programa'] = clean_name.strip()
                if on_progress: on_progress(f"UFPB: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"UFPB: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UFPB: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Padrão)
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link na tabela de arquivos (Visualizar/Abrir)
            if not pdf_url:
                # Procura links que contenham 'bitstream' e terminem em .pdf
                link_tag = soup.find('a', href=lambda h: h and 'bitstream' in h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UFPB: PDF localizado.")
            else:
                if on_progress: on_progress("UFPB: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UFPB: Erro PDF: {str(e)[:20]}")

        return data
    
    