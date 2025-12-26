import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UFMGParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UFMG", universidade="Universidade Federal de Minas Gerais")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UFMG (DSpace 8/Angular).
        Foca no campo de metadado 'Curso' para o programa e metatags para o PDF.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UFMG: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # O layout da UFMG exibe os metadados em blocos com a classe 'simple-view-element'
            # Procuramos o cabeçalho h2 que contém o texto "Curso"
            headers = soup.find_all('h2', class_='simple-view-element-header')
            
            for header in headers:
                if "Curso" in header.get_text(strip=True):
                    # O valor está na div irmã (body) logo após o header
                    body = header.find_next_sibling('div', class_='simple-view-element-body')
                    if body:
                        text = body.get_text(strip=True)
                        
                        # Limpeza: Remove "Programa de Pós-Graduação em/no/na"
                        # Exemplo: "Programa de Pós-Graduação em Direito" -> "Direito"
                        clean_name = re.sub(
                            r'.*Programa de Pós-Graduação\s*(em|no|na)?\s*', 
                            '', 
                            text, 
                            flags=re.IGNORECASE
                        )
                        found_program = clean_name.strip()
                        break
            
            # Fallback: Se não achar "Curso", tenta "Departamento" ou Breadcrumbs
            if not found_program:
                collection_links = soup.select('ds-base-breadcrumbs ol.breadcrumb li.active div.text-truncate')
                if collection_links:
                    # Tenta inferir algo, mas no DSpace 8 da UFMG o campo "Curso" é o mais seguro
                    pass

            if found_program:
                data['programa'] = found_program
                if on_progress: on_progress(f"UFMG: Programa identificado: {found_program}")

        except Exception as e:
            if on_progress: on_progress(f"UFMG: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UFMG: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Padrão e presente no HTML da UFMG)
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link direto na lista de arquivos (Layout Angular)
            if not pdf_url:
                # Procura links que contenham '/bitstreams/' e '/download'
                link_tag = soup.find('a', href=lambda h: h and '/bitstreams/' in h and '/download' in h)
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UFMG: PDF localizado.")
            else:
                if on_progress: on_progress("UFMG: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UFMG: Erro PDF: {str(e)[:20]}")

        return data