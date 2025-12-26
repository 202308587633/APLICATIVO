import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class MackenzieParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="MACKENZIE", universidade="Universidade Presbiteriana Mackenzie")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da MACKENZIE (DSpace 7/Angular).
        Foca nos breadcrumbs e metadados específicos para o Programa e meta tags para o PDF.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("MACKENZIE: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia 1: Busca nos Breadcrumbs (Conforme exemplo fornecido)
            # Ex: "Direito Político e Econômico - Dissertações - Direito Higienópolis"
            crumbs = soup.select('ol.breadcrumb li')
            
            for crumb in crumbs:
                text = crumb.get_text(strip=True)
                
                # Ignora itens genéricos
                if text in ["Início", "Faculdade de Direito", "Dissertações", "Teses"]:
                    continue
                
                # Tenta identificar o nome do programa. Geralmente contém "Direito" ou "Pós-Graduação"
                # A Mackenzie costuma colocar o curso no breadcrumb com sufixos
                if "Direito" in text or "Programa" in text:
                    # Limpeza: Pega apenas a parte antes do primeiro hífen " - "
                    # Ex: "Direito Político e Econômico - ..." -> "Direito Político e Econômico"
                    found_program = text.split(' - ')[0].strip()
                    
                    # Se o texto capturado for muito curto ou genérico, continua procurando
                    if len(found_program) > 5 and found_program != "Faculdade de Direito":
                        break

            # Estratégia 2: Busca por Campo de Metadado Explícito (DSpace 7)
            # O HTML mostra: <h2 ...>Programa</h2> ... <span>Direito Político e Econômico</span>
            if not found_program:
                headers = soup.find_all('h2', class_='simple-view-element-header')
                for header in headers:
                    if "Programa" in header.get_text(strip=True):
                        body = header.find_next_sibling('div', class_='simple-view-element-body')
                        if body:
                            found_program = body.get_text(strip=True)
                            break

            if found_program:
                data['programa'] = found_program
                if on_progress: on_progress(f"MACKENZIE: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"MACKENZIE: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("MACKENZIE: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Padrão)
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link na seção "Arquivos" (Botão de Download)
            if not pdf_url:
                # Procura links que contenham '/bitstreams/' e '/download'
                link_tag = soup.find('a', href=lambda h: h and '/bitstreams/' in h and '/download' in h)
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("MACKENZIE: PDF localizado.")
            else:
                if on_progress: on_progress("MACKENZIE: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"MACKENZIE: Erro PDF: {str(e)[:20]}")

        return data