import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UFSParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UFS", universidade="Universidade Federal de Sergipe")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UFS (DSpace 6.3).
        Foca na tabela de metadados específica e breadcrumbs para o Programa.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UFS: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia 1: Busca pela classe CSS específica do DSpace na tabela de metadados
            # O HTML mostra: <td class="metadataFieldValue dc_publisher_program">Pós-Graduação em Direito</td>
            prog_td = soup.find('td', class_='metadataFieldValue dc_publisher_program')
            if prog_td:
                found_program = prog_td.get_text(strip=True)
            
            # Estratégia 2: Busca nos Breadcrumbs (Conforme exemplo fornecido)
            # <ol class="breadcrumb btn-success"> ... <li>Programa de Pós-Graduação em Direito - PRODIR</li> ... </ol>
            if not found_program:
                crumbs = soup.select('ol.breadcrumb li')
                for crumb in crumbs:
                    text = crumb.get_text(strip=True)
                    
                    # Ignora itens genéricos
                    if text in ["Repositório Institucional da Universidade Federal de Sergipe - RI/UFS", 
                                "TESES E DISSERTAÇÕES", 
                                "BIBLIOTECA DIGITAL DE TESES E DISSERTAÇÕES (BDTD) - UFS"]:
                        continue
                    
                    # Tenta identificar o programa
                    if "Programa de Pós-Graduação" in text or "Mestrado" in text or "Doutorado" in text:
                        found_program = text
                        # Se encontrou "Programa de Pós-Graduação", geralmente é o mais completo antes do nível (Mestrado/Doutorado)
                        if "Programa de Pós-Graduação" in text:
                            break

            if found_program:
                # Limpeza: 
                # 1. Remove prefixos como "Programa de Pós-Graduação em", "Pós-Graduação em"
                clean_name = re.sub(
                    r'^(?:Programa de |)Pós-Graduação (?:em|no|na)\s*', 
                    '', 
                    found_program, 
                    flags=re.IGNORECASE
                )
                
                # 2. Remove prefixos de nível se sobrarem (ex: "Mestrado em Direito")
                clean_name = re.sub(
                    r'^(?:Mestrado|Doutorado)(?: Profissional)? (?:em|no|na)\s*', 
                    '', 
                    clean_name, 
                    flags=re.IGNORECASE
                )

                # 3. Remove sufixos de sigla após hífen (ex: "Direito - PRODIR" -> "Direito")
                clean_name = clean_name.split(' - ')[0]
                
                data['programa'] = clean_name.strip()
                if on_progress: on_progress(f"UFS: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"UFS: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UFS: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Padrão e presente no HTML)
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link na tabela de arquivos (Visualizar/Abrir)
            if not pdf_url:
                # Procura links que contenham '/bitstream/' e terminem em .pdf
                link_tag = soup.find('a', href=lambda h: h and '/bitstream/' in h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UFS: PDF localizado.")
            else:
                if on_progress: on_progress("UFS: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UFS: Erro PDF: {str(e)[:20]}")

        return data
    
    