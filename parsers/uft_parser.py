import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UFTParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UFT", universidade="Universidade Federal do Tocantins")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UFT (DSpace 6.3).
        Foca na tabela de metadados específica para o Programa e meta tags para o PDF.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UFT: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia 1: Busca pela classe CSS específica do DSpace na tabela de metadados
            # O HTML mostra: <td class="metadataFieldValue dc_publisher_program">Programa de Pós-Graduação em ... - PPGPJDH</td>
            prog_td = soup.find('td', class_='metadataFieldValue dc_publisher_program')
            if prog_td:
                found_program = prog_td.get_text(strip=True)
            
            # Estratégia 2: Busca por meta tags (Padrão DSpace)
            # O HTML não mostrou meta tag explícita para o programa com esse nome, mas é um fallback comum
            if not found_program:
                publishers = soup.find_all('meta', attrs={'name': 'DC.publisher'})
                for meta in publishers:
                    content = meta.get('content', '')
                    if "Programa de Pós-Graduação" in content:
                        found_program = content
                        break

            # Estratégia 3: Breadcrumbs (Trilha de navegação)
            # <ol class="breadcrumb label-success"> ... <li>Pós-Graduação em Prestação Jurisdicional e Direitos Humanos - PPGPJDH</li> ... </ol>
            if not found_program:
                crumbs = soup.select('ol.breadcrumb li')
                for crumb in crumbs:
                    text = crumb.get_text(strip=True)
                    # Ignora itens genéricos
                    if text in ["Repositório UFT", "BDTD - Biblioteca Digital de Teses e Dissertações da UFT"]:
                        continue
                    
                    # Tenta identificar o programa
                    if "Pós-Graduação" in text or "Mestrado" in text or "Doutorado" in text:
                        found_program = text
                        # Geralmente o programa é o antepenúltimo ou penúltimo, antes da coleção específica de teses/dissertações
                        # Mas se tiver "Programa de Pós-Graduação", é um forte candidato.
                        if "Programa de Pós-Graduação" in text:
                            break

            if found_program:
                # Limpeza:
                # 1. Remove "Programa de Pós-Graduação em", "Pós-Graduação em"
                clean_name = re.sub(
                    r'^(?:Programa de |)Pós-Graduação (?:em|no|na)\s*', 
                    '', 
                    found_program, 
                    flags=re.IGNORECASE
                )
                
                # 2. Remove prefixos de nível se sobrarem (ex: "Mestrado profissional e interdisciplinar em")
                clean_name = re.sub(
                    r'^(?:Mestrado|Doutorado)(?: profissional| acadêmico| e interdisciplinar)? (?:em|no|na)\s*', 
                    '', 
                    clean_name, 
                    flags=re.IGNORECASE
                )

                # 3. Remove siglas após hífen (ex: "Direitos Humanos - PPGPJDH" -> "Direitos Humanos")
                clean_name = clean_name.split(' - ')[0].strip()
                
                data['programa'] = clean_name
                if on_progress: on_progress(f"UFT: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"UFT: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UFT: Buscando arquivo PDF...")
            
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
                if on_progress: on_progress("UFT: PDF localizado.")
            else:
                if on_progress: on_progress("UFT: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UFT: Erro PDF: {str(e)[:20]}")

        return data
    
    