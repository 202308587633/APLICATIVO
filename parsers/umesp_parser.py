import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UMESPParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UMESP", universidade="Universidade Metodista de São Paulo")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UMESP (DSpace 7.6 - Angular).
        Foca nos breadcrumbs para identificar o Programa e meta tags para o PDF.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UMESP: Analisando estrutura da página (DSpace 7)...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia Principal: Breadcrumbs (Trilha de navegação)
            # O HTML mostra: <ol class="container breadcrumb"> ... <li>Programa de Pós-Graduação...</li> ... </ol>
            crumbs = soup.select('ol.breadcrumb li')
            
            for crumb in crumbs:
                text = crumb.get_text(strip=True)
                
                # Ignora itens genéricos como "Início", "Dissertações" (Coleção genérica)
                if text in ["Início", "Página inicial"]:
                    continue
                
                # Tenta identificar o programa pelo padrão de texto
                # Ex: "Programa de Pós-Graduação em Ciências da Religião"
                if "Programa de Pós-Graduação" in text or "Mestrado" in text or "Doutorado" in text:
                    found_program = text
                    # Geralmente no DSpace, o programa é a comunidade/coleção pai imediata ou anterior ao item
                    # Se achamos algo explícito como "Programa de...", é o nosso alvo.
                    break
            
            # Estratégia de Backup: Metadados visuais (DSpace 7 simple-view-element)
            # Caso não ache no breadcrumb, tenta achar nos metadados exibidos na tela
            if not found_program:
                collection_divs = soup.find_all('div', class_='collections')
                for div in collection_divs:
                    text = div.get_text(strip=True)
                    if "Programa" in text:
                        found_program = text
                        break

            if found_program:
                # Limpeza:
                # Remove "Programa de Pós-Graduação em", "Curso de...", etc.
                clean_name = re.sub(
                    r'^(?:Programa de |)Pós-Graduação (?:em|no|na)\s*', 
                    '', 
                    found_program, 
                    flags=re.IGNORECASE
                )
                
                data['programa'] = clean_name.strip()
                if on_progress: on_progress(f"UMESP: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"UMESP: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UMESP: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Presente no HTML fornecido)
            # <meta name="citation_pdf_url" content="...">
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link na seção de arquivos (DSpace 7)
            if not pdf_url:
                # Procura links que contenham '/bitstreams/' e '/download'
                # Ex: href="/bitstreams/00d053ce.../download"
                link_tag = soup.find('a', href=lambda h: h and '/bitstreams/' in h and '/download' in h)
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UMESP: PDF localizado.")
            else:
                if on_progress: on_progress("UMESP: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UMESP: Erro PDF: {str(e)[:20]}")

        return data
    