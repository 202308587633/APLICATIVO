import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UEAParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UEA", universidade="Universidade do Estado do Amazonas")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UEA (DSpace 7/8 - Angular).
        Foca em breadcrumbs e metadados 'simple-view-element' para o Programa.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UEA: Analisando estrutura da página (DSpace 7+)...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia 1: Busca em links de Coleção (Estrutura DSpace 7)
            # <div class="collections"><a href="..."><span>Mestrado em Direito ambiental</span></a></div>
            collection_divs = soup.find_all('div', class_='collections')
            for div in collection_divs:
                a_tag = div.find('a')
                if a_tag:
                    text = a_tag.get_text(strip=True)
                    # Verifica se parece um nome de programa
                    if any(k in text for k in ["Mestrado", "Doutorado", "Pós-Graduação", "Programa"]):
                        found_program = text
                        break

            # Estratégia 2: Breadcrumbs (Trilha de navegação)
            # Ex: Início > ... > Mestrado em Direito ambiental
            if not found_program:
                crumbs = soup.select('ol.breadcrumb li')
                for crumb in crumbs:
                    text = crumb.get_text(strip=True)
                    # Ignora genéricos
                    if text in ["Início", "Comunidades e Coleções"]:
                        continue
                    
                    # Tenta capturar programas
                    if any(k in text for k in ["Mestrado", "Doutorado", "Pós-Graduação", "PPG"]):
                        found_program = text
                        # Não damos break aqui, pois o último breadcrumb específico costuma ser a coleção mais precisa

            # Estratégia 3: Metadados DSpace 7 (simple-view-element)
            if not found_program:
                 elements = soup.find_all('div', class_='simple-view-element')
                 for el in elements:
                    header = el.find(['h2', 'h3', 'h4', 'h5'], class_='simple-view-element-header')
                    if header:
                        header_text = header.get_text(strip=True)
                        if "Programa" in header_text or "Pós-Graduação" in header_text:
                            body = el.find('div', class_='simple-view-element-body')
                            if body:
                                found_program = body.get_text(strip=True)
                                break

            if found_program:
                # Limpeza:
                # Remove "Mestrado em", "Doutorado em", "Programa de Pós-Graduação em", etc.
                # Ex: "Mestrado em Direito ambiental" -> "Direito ambiental"
                clean_name = re.sub(
                    r'^(?:Programa de Pós-Graduação|Mestrado|Doutorado|Curso)(?:\s+(?:Profissional|Acadêmico))?(?: em| no| na)?\s*', 
                    '', 
                    found_program, 
                    flags=re.IGNORECASE
                )
                
                data['programa'] = clean_name.strip()
                if on_progress: on_progress(f"UEA: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"UEA: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UEA: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Padrão e presente no HTML)
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link na seção de arquivos (DSpace 7/8 Angular)
            if not pdf_url:
                # Procura links que contenham '/bitstreams/' e '/download'
                # <a href="/bitstreams/.../download">
                link_tag = soup.find('a', href=lambda h: h and '/bitstreams/' in h and '/download' in h)
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UEA: PDF localizado.")
            else:
                if on_progress: on_progress("UEA: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UEA: Erro PDF: {str(e)[:20]}")

        return data
    
    