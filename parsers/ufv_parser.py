import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UFVParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UFV", universidade="Universidade Federal de Viçosa")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UFV (Locus - DSpace 8.0).
        Utiliza metadados visuais e regex na citação para identificar o Programa.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UFV: Analisando estrutura da página (DSpace 8)...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # O DSpace 8 exibe metadados em blocos <div class="simple-view-element">
            # Vamos iterar sobre eles para achar 'Citação' ou 'Programa'
            elements = soup.find_all('div', class_='simple-view-element')
            
            for el in elements:
                header = el.find(class_='simple-view-element-header')
                if not header:
                    continue
                
                header_text = header.get_text(strip=True).lower()
                body = el.find(class_='simple-view-element-body')
                
                if not body:
                    continue
                
                content_text = body.get_text(strip=True)

                # Estratégia A: Campo "Citação" (Conforme seu exemplo)
                # Ex: "... Tese (Doutorado em Economia Doméstica) - Universidade..."
                if 'citação' in header_text:
                    # Regex para capturar o texto após "Mestrado em" ou "Doutorado em"
                    # Até encontrar um parêntese fechando ')' ou um hífen '-'
                    match = re.search(
                        r'(?:Mestrado|Doutorado|Mestre|Doutor)(?:\s+Profissional|\s+Acadêmico)?\s+em\s+([^)\-]+)', 
                        content_text, 
                        re.IGNORECASE
                    )
                    if match:
                        found_program = match.group(1).strip()
                        break
                
                # Estratégia B: Campo "Programa" ou "Titulação" (Fallback explícito)
                # O HTML pode conter um campo explícito de programa
                elif 'programa' in header_text or 'titulação' in header_text:
                    # Limpa prefixos como "Programa de Pós-Graduação em"
                    found_program = content_text
                    break

            if found_program:
                # Limpeza final
                clean_name = re.sub(
                    r'^(?:Programa de Pós-Graduação|Curso|Mestrado|Doutorado)(?:\s+(?:Profissional|Acadêmico))?(?: em| no| na)?\s*', 
                    '', 
                    found_program, 
                    flags=re.IGNORECASE
                )
                # Remove caracteres de pontuação finais que podem ter sobrado da citação
                clean_name = clean_name.strip('.,- ')
                
                data['programa'] = clean_name
                if on_progress: on_progress(f"UFV: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"UFV: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UFV: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Padrão e presente no HTML)
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link na seção de arquivos (DSpace 8)
            # Procura links que contenham '/bitstreams/' e '/download'
            if not pdf_url:
                link_tag = soup.find('a', href=lambda h: h and '/bitstreams/' in h and '/download' in h)
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UFV: PDF localizado.")
            else:
                if on_progress: on_progress("UFV: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UFV: Erro PDF: {str(e)[:20]}")

        return data
    