import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UENPParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UENP", universidade="Universidade Estadual do Norte do Paraná")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UENP (DSpace 7.5 - Angular).
        Foca nos breadcrumbs para identificar o Programa e meta tags para o PDF.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UENP: Analisando estrutura da página (DSpace 7)...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia 1: Breadcrumbs (Trilha de navegação)
            # DSpace 7 usa <ol class="breadcrumb"><li>...</li></ol>
            # Exemplo: Início > Ciências Sociais Aplicadas > Programa de Pós-Graduação em Ciência Jurídica > Dissertações
            crumbs = soup.select('ol.breadcrumb li')
            
            for crumb in crumbs:
                text = crumb.get_text(strip=True)
                
                # Ignora itens genéricos
                if text in ["Início", "Comunidades e Coleções"]:
                    continue
                
                # Busca por "Programa de Pós-Graduação"
                if "Programa de Pós-Graduação" in text:
                    found_program = text
                    # Geralmente é o item mais específico antes da coleção (Dissertações/Teses)
                    # Não damos break imediato pois pode haver sub-hierarquias, mas neste caso
                    # "Programa..." é um forte indicador.
                
                # Fallback: Se tiver "Mestrado em" ou "Doutorado em" no nome da comunidade
                elif not found_program and ("Mestrado" in text or "Doutorado" in text):
                     # Cuidado para não pegar o título do trabalho ou a coleção "Dissertações de Mestrado"
                     if "Dissertações" not in text and "Teses" not in text:
                         found_program = text

            # Estratégia 2: Metadados na página (Fallback)
            if not found_program:
                # DSpace 7 usa a classe 'simple-view-element' para exibir metadados
                elements = soup.find_all('div', class_='simple-view-element')
                for el in elements:
                    header = el.find('h5', class_='simple-view-element-header') # DSpace 7 costuma usar h5 ou h2
                    if header and "Programa" in header.get_text():
                        body = el.find('div', class_='simple-view-element-body')
                        if body:
                            found_program = body.get_text(strip=True)
                            break

            if found_program:
                # Limpeza: remove "Programa de Pós-Graduação em"
                # Ex: "Programa de Pós-Graduação em Ciência Jurídica" -> "Ciência Jurídica"
                clean_name = re.sub(
                    r'^(?:Programa de |)Pós-Graduação (?:em|no|na)\s*', 
                    '', 
                    found_program, 
                    flags=re.IGNORECASE
                )
                
                data['programa'] = clean_name.strip()
                if on_progress: on_progress(f"UENP: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"UENP: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UENP: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Padrão DSpace e presente no HTML)
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
                if on_progress: on_progress("UENP: PDF localizado.")
            else:
                if on_progress: on_progress("UENP: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UENP: Erro PDF: {str(e)[:20]}")

        return data
    
