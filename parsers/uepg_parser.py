import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UEPGParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UEPG", universidade="Universidade Estadual de Ponta Grossa")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UEPG (DSpace 5.x).
        Foca na tabela de metadados para o Programa e meta tags para o PDF.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UEPG: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # O DSpace da UEPG usa tabelas com classes específicas para metadados
            # Ex: <td class="metadataFieldLabel">metadata.dc.publisher.program:</td>
            
            # Estratégia 1: Busca direta na tabela de exibição do item
            program_td = soup.find('td', class_='metadataFieldLabel', string=re.compile(r'program', re.I))
            
            if program_td:
                value_td = program_td.find_next_sibling('td', class_='metadataFieldValue')
                if value_td:
                    text = value_td.get_text(strip=True)
                    # Texto cru: "Programa de Pós - Graduação em Direito Mestrado Profissional"
                    
                    # Limpeza com Regex
                    # Remove "Programa de Pós - Graduação em" (considerando variações de espaços e hífens)
                    clean_name = re.sub(
                        r'Programa de Pós\s*[-–]?\s*Graduação (em|no|na)\s*', 
                        '', 
                        text, 
                        flags=re.IGNORECASE
                    )
                    
                    # Remove sufixos comuns como "Mestrado", "Doutorado", "Profissional"
                    # Ex: "Direito Mestrado Profissional" -> "Direito"
                    clean_name = re.sub(r'\s+(Mestrado|Doutorado).*$', '', clean_name, flags=re.IGNORECASE)
                    
                    found_program = clean_name.strip()

            # Estratégia 2: Breadcrumbs (Fallback)
            if not found_program:
                # <a href="...">Programa de Pós - Graduação em Direito Mestrado Profissional</a>
                crumbs = soup.select('ul.breadcrumb li a') # Ou ol.breadcrumb dependendo da versão exata do tema
                if not crumbs: crumbs = soup.select('.breadcrumb a')
                
                for crumb in crumbs:
                    text = crumb.get_text(strip=True)
                    if "Programa de Pós" in text:
                        clean_name = re.sub(r'Programa de Pós\s*[-–]?\s*Graduação (em|no|na)\s*', '', text, flags=re.IGNORECASE)
                        clean_name = re.sub(r'\s+(Mestrado|Doutorado).*$', '', clean_name, flags=re.IGNORECASE)
                        found_program = clean_name.strip()
                        break

            if found_program:
                data['programa'] = found_program
                if on_progress: on_progress(f"UEPG: Programa identificado: {found_program}")

        except Exception as e:
            if on_progress: on_progress(f"UEPG: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UEPG: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Padrão e presente no HTML)
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link na tabela de arquivos ("View/Open" ou "Baixar")
            if not pdf_url:
                # Procura links que contenham 'bitstream' e terminem em .pdf
                link_tag = soup.find('a', href=lambda h: h and 'bitstream' in h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UEPG: PDF localizado.")
            else:
                if on_progress: on_progress("UEPG: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UEPG: Erro PDF: {str(e)[:20]}")

        return data