import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UELParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UEL", universidade="Universidade Estadual de Londrina")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UEL (DSpace 7.6 - Angular).
        Foca nos breadcrumbs para identificar o Programa e meta tags para o PDF.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UEL: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # O DSpace 7 usa breadcrumbs na estrutura <ol class="breadcrumb">
            # Ex: Início > CESA... > 02 - Mestrado - Direito Negocial
            crumbs = soup.select('ol.breadcrumb li')
            
            for crumb in crumbs:
                text = crumb.get_text(strip=True)
                
                # Ignora itens genéricos
                if text in ["Início", "Comunidades e Coleções"]:
                    continue
                
                # Tenta identificar o programa. Na UEL, eles seguem o padrão "XX - Mestrado - Nome"
                # Exemplo: "02 - Mestrado - Direito Negocial"
                if "Mestrado" in text or "Doutorado" in text or "Pós-Graduação" in text:
                    # Limpeza:
                    # 1. Remove números iniciais e traços (ex: "02 - ")
                    # 2. Remove "Mestrado -", "Doutorado -", etc.
                    clean_name = re.sub(r'^\d+\s*-\s*', '', text) # Remove "02 - "
                    clean_name = re.sub(r'(Mestrado|Doutorado|Programa de Pós-Graduação em)\s*-?\s*', '', clean_name, flags=re.IGNORECASE)
                    
                    found_program = clean_name.strip()
                    # Geralmente é o penúltimo breadcrumb, então se acharmos um melhor depois, atualizamos.
            
            if found_program:
                data['programa'] = found_program
                if on_progress: on_progress(f"UEL: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"UEL: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UEL: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Padrão DSpace)
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
                if on_progress: on_progress("UEL: PDF localizado.")
            else:
                if on_progress: on_progress("UEL: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UEL: Erro PDF: {str(e)[:20]}")

        return data
    
    