import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UNESPParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UNESP", universidade="Universidade Estadual Paulista")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UNESP (DSpace 7+ / Angular).
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UNESP: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # O layout Angular organiza metadados em blocos 'simple-view-element'
            # Procuramos o cabeçalho H2 que contém "Pós-graduação"
            headers = soup.find_all('h2', class_='simple-view-element-header')
            
            for header in headers:
                if "Pós-graduação" in header.get_text(strip=True):
                    # O valor está na div irmã (body) logo após o header
                    body = header.find_next_sibling('div', class_='simple-view-element-body')
                    if body:
                        text = body.get_text(strip=True)
                        
                        # Exemplo: "Direito - FCHS" -> Queremos apenas "Direito"
                        # Removemos o sufixo da unidade (separado por hífen) se existir
                        if ' - ' in text:
                            text = text.split(' - ')[0]
                        
                        found_program = text.strip()
                        break
            
            # Fallback: Tentar meta tags se o bloco visual não for achado
            if not found_program:
                # UNESP às vezes usa dc.publisher.program ou similar em metatags customizadas
                # Mas o DSpace 7 costuma expor isso visualmente. Vamos tentar extrair de keywords
                # caso falhe, mas o método acima é o principal.
                pass

            if found_program:
                data['programa'] = found_program
                if on_progress: on_progress(f"UNESP: Programa identificado: {found_program}")

        except Exception as e:
            if on_progress: on_progress(f"UNESP: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UNESP: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Presente no HTML fornecido)
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link direto na lista de arquivos (Padrão DSpace Angular)
            if not pdf_url:
                # Procura links que contenham '/bitstreams/' e '/download'
                link_tag = soup.find('a', href=lambda h: h and '/bitstreams/' in h and '/download' in h)
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UNESP: PDF localizado.")
            else:
                if on_progress: on_progress("UNESP: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UNESP: Erro PDF: {str(e)[:20]}")

        return data