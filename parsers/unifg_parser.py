import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UNIFGParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UNIFG", universidade="Centro Universitário FG")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UNIFG (DSpace 9.1 - Rede Ânima).
        Foca em breadcrumbs e metadados de coleção para identificar o Programa.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UNIFG: Analisando estrutura da página (DSpace 9)...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia 1: Busca em links de Coleção (Estrutura DSpace 7+)
            # <div class="collections"><a ...><span>Programa de Pós-Graduação em Direito</span></a></div>
            collection_divs = soup.find_all('div', class_='collections')
            for div in collection_divs:
                a_tag = div.find('a')
                if a_tag:
                    text = a_tag.get_text(strip=True)
                    if "Programa" in text or "Pós-Graduação" in text:
                        found_program = text
                        break

            # Estratégia 2: Breadcrumbs (Trilha de navegação)
            # <ol class="breadcrumb"> ... <li>Programa de Pós-Graduação em Direito</li> ... </ol>
            if not found_program:
                crumbs = soup.select('ol.breadcrumb li')
                for crumb in crumbs:
                    text = crumb.get_text(strip=True)
                    
                    # Ignora itens genéricos
                    if text in ["Início", "Teses e dissertações", "UNIFG (BA)"]:
                        continue
                    
                    # Tenta capturar programas
                    if "Programa de Pós-Graduação" in text or "Mestrado" in text or "Doutorado" in text:
                        found_program = text

            if found_program:
                # Limpeza:
                # Remove "Programa de Pós-Graduação em", "Mestrado em", etc.
                # Ex: "Programa de Pós-Graduação em Direito" -> "Direito"
                clean_name = re.sub(
                    r'^(?:Programa de Pós-Graduação|Mestrado|Doutorado)(?:\s+(?:Profissional|Acadêmico))?(?: em| no| na)?\s*', 
                    '', 
                    found_program, 
                    flags=re.IGNORECASE
                )
                
                data['programa'] = clean_name.strip()
                if on_progress: on_progress(f"UNIFG: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"UNIFG: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UNIFG: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Padrão)
            # O HTML possui: <meta name="citation_pdf_url" content="...">
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link na seção de arquivos
            if not pdf_url:
                # Procura links que contenham '/bitstreams/' e '/download'
                link_tag = soup.find('a', href=lambda h: h and '/bitstreams/' in h and '/download' in h)
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UNIFG: PDF localizado.")
            else:
                if on_progress: on_progress("UNIFG: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UNIFG: Erro PDF: {str(e)[:20]}")

        return data
    
