import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UFNParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UFN", universidade="Universidade Franciscana")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UFN (DSpace 4.2 / TEDE).
        Foca nos breadcrumbs para identificar o Programa e meta tags para o PDF.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UFN: Analisando estrutura da página (TEDE/DSpace 4)...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia A: Breadcrumbs (Trilha de navegação) - Conforme exemplo
            # O HTML mostra: <ol class="breadcrumb btn-success"> ... <li>Programa de Pós-Graduação em Ensino...</li> </ol>
            crumbs = soup.select('ol.breadcrumb li')
            
            for crumb in crumbs:
                text = crumb.get_text(strip=True)
                
                # Ignora itens genéricos
                if text in ["UFN Universidade Franciscana", "Programas de Pós-Graduação da UFN"]:
                    continue
                
                # Tenta identificar o programa pelo padrão de texto
                # Ex: "Programa de Pós-Graduação em Ensino de Humanidades e Linguagens"
                if "Programa de Pós-Graduação" in text or "Mestrado" in text or "Doutorado" in text:
                    found_program = text
                    # No exemplo da UFN, o programa parece ser o último ou penúltimo item do breadcrumb
                    # Como iteramos do início, o último válido encontrado será o mais específico.
            
            # Estratégia B: Metadados na Tabela (Backup)
            # <td class="metadataFieldLabel">Programa:&nbsp;</td> <td class="metadataFieldValue">...</td>
            if not found_program:
                label_td = soup.find('td', class_='metadataFieldLabel', string=re.compile("Programa", re.IGNORECASE))
                if label_td:
                    value_td = label_td.find_next_sibling('td', class_='metadataFieldValue')
                    if value_td:
                        found_program = value_td.get_text(strip=True)

            if found_program:
                # Limpeza:
                # Remove "Programa de Pós-Graduação em", "Mestrado Acadêmico em", etc.
                clean_name = re.sub(
                    r'^(?:Programa de |)(?:Pós-Graduação|Mestrado|Doutorado)(?:\s+(?:Acadêmico|Profissional))?(?: em| no| na)?\s*', 
                    '', 
                    found_program, 
                    flags=re.IGNORECASE
                )
                
                data['programa'] = clean_name.strip()
                if on_progress: on_progress(f"UFN: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"UFN: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UFN: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Padrão e presente no HTML)
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
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UFN: PDF localizado.")
            else:
                if on_progress: on_progress("UFN: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UFN: Erro PDF: {str(e)[:20]}")

        return data
    
