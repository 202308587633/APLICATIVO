import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UFESParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UFES", universidade="Universidade Federal do Espírito Santo")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UFES (DSpace 7+ / Angular).
        Foca em breadcrumbs e links de coleção para identificar o Programa.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UFES: Analisando estrutura da página (DSpace 7+)...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia 1: Busca em links de Coleção (Estrutura DSpace 7)
            # <div class="collections"><a href="..."><span>Mestrado Profissional em Gestão Pública</span></a></div>
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
            # Ex: Início > Teses e Dissertações > Gestão Pública - Mestrado Profissional
            if not found_program:
                crumbs = soup.select('ol.breadcrumb li')
                for crumb in crumbs:
                    text = crumb.get_text(strip=True)
                    # Ignora genéricos
                    if text in ["Início", "Teses e Dissertações", "Comunidades e Coleções"]:
                        continue
                    
                    # Tenta capturar programas
                    if any(k in text for k in ["Mestrado", "Doutorado", "Pós-Graduação", "PPG"]):
                        found_program = text
                        # Não damos break aqui, pois o último breadcrumb específico costuma ser a coleção mais precisa
                        
            # Estratégia 3: Metadados textuais (Fallback para VuFind antigo se ainda existir)
            if not found_program:
                 target_th = soup.find('th', string=re.compile(r'dc\.publisher\.none\.fl_str_mv', re.IGNORECASE))
                 if target_th:
                    td = target_th.find_next_sibling('td')
                    if td:
                        text_content = td.get_text(separator='\n', strip=True)
                        for line in text_content.split('\n'):
                            if "Programa de Pós-Graduação" in line:
                                found_program = line.strip()
                                break

            if found_program:
                # Limpeza:
                # Remove "Mestrado Profissional em", "Programa de Pós-Graduação em", etc.
                # Ex: "Gestão Pública - Mestrado Profissional" -> "Gestão Pública"
                
                # 1. Remove sufixos comuns tipo " - Mestrado Profissional"
                clean_name = re.sub(r'\s*-\s*(Mestrado|Doutorado).*$', '', found_program, flags=re.IGNORECASE)
                
                # 2. Remove prefixos comuns
                clean_name = re.sub(
                    r'^(?:Programa de Pós-Graduação|Mestrado|Doutorado|Curso)(?:\s+(?:Profissional|Acadêmico))?(?: em| no| na)?\s*', 
                    '', 
                    clean_name, 
                    flags=re.IGNORECASE
                )
                
                data['programa'] = clean_name.strip()
                if on_progress: on_progress(f"UFES: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"UFES: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UFES: Buscando arquivo PDF...")
            
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
                if on_progress: on_progress("UFES: PDF localizado.")
            else:
                if on_progress: on_progress("UFES: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UFES: Erro PDF: {str(e)[:20]}")

        return data
    
    