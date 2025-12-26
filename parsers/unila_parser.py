import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UNILAParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UNILA", universidade="Universidade Federal da Integração Latino-Americana")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UNILA (DSpace 7.6 - Angular).
        Foca nos breadcrumbs para identificar o Programa e meta tags para o PDF.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UNILA: Analisando estrutura da página (DSpace 7)...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia 1: Breadcrumbs (Trilha de navegação)
            # O HTML mostra: <ol class="container breadcrumb"> ... <li>PPGICAL - Programa...</li> ... </ol>
            crumbs = soup.select('ol.breadcrumb li')
            
            for crumb in crumbs:
                text = crumb.get_text(strip=True)
                
                # Ignora itens genéricos ou de nível superior
                if text in ["Início", "UNILA | Biblioteca Digital de Dissertações e Teses"]:
                    continue
                
                # Tenta identificar o programa
                # Na UNILA, muitas vezes aparece a sigla antes: "PPGICAL - Programa..."
                if "Programa de Pós-Graduação" in text or "Mestrado" in text or "Doutorado" in text:
                    found_program = text
                    # Geralmente o programa é a comunidade "pai" da coleção de dissertações
                    # Não damos break imediato para garantir que não pegamos uma sub-comunidade errada,
                    # mas se tiver "Programa de Pós-Graduação", é um forte candidato.
            
            # Estratégia 2: Metadados visuais (DSpace 7 simple-view-element)
            if not found_program:
                elements = soup.find_all('div', class_='simple-view-element')
                for el in elements:
                    header = el.find(['h2', 'h3', 'h4', 'h5'], class_='simple-view-element-header')
                    if header and "Programa" in header.get_text(strip=True):
                        body = el.find('div', class_='simple-view-element-body')
                        if body:
                            found_program = body.get_text(strip=True)
                            break

            if found_program:
                # Limpeza:
                # 1. Remove siglas no início (ex: "PPGICAL - ")
                clean_name = re.sub(r'^[A-Z0-9]+(?:\s+)?-\s+', '', found_program)
                
                # 2. Remove "Programa de Pós-Graduação em"
                clean_name = re.sub(
                    r'^(?:Programa de |)Pós-Graduação (?:em|no|na)\s*', 
                    '', 
                    clean_name, 
                    flags=re.IGNORECASE
                )
                
                data['programa'] = clean_name.strip()
                if on_progress: on_progress(f"UNILA: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"UNILA: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UNILA: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Padrão e presente no HTML)
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link na seção de arquivos (DSpace 7)
            if not pdf_url:
                # Procura links que contenham '/bitstreams/' e '/download'
                link_tag = soup.find('a', href=lambda h: h and '/bitstreams/' in h and '/download' in h)
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UNILA: PDF localizado.")
            else:
                if on_progress: on_progress("UNILA: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UNILA: Erro PDF: {str(e)[:20]}")

        return data
    
