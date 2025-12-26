import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UFPEParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UFPE", universidade="Universidade Federal de Pernambuco")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UFPE (Attena - DSpace 6.3).
        Foca nos breadcrumbs para identificar o Programa.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UFPE: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia 1: Busca nos Breadcrumbs (Trilha de navegação)
            # Ex: ... > Programa de Pós-Graduação em Direitos Humanos > ...
            crumbs = soup.select('ol.breadcrumb li')
            for crumb in crumbs:
                text = crumb.get_text(strip=True)
                
                # Procura explicitamente por "Programa de Pós-Graduação"
                # O HTML pode ter ou não acentos dependendo da codificação, então usamos regex flexível
                if re.search(r'Programa de P(?:ó|o)s-Gradua(?:ç|c)(?:ã|a)o', text, re.IGNORECASE):
                    found_program = text
                    break
            
            # Estratégia 2: Busca por meta tags DC.publisher
            # O HTML mostra: <meta name="DC.publisher" content="Programa de Pos Graduacao em ...">
            if not found_program:
                publishers = soup.find_all('meta', attrs={'name': 'DC.publisher'})
                for meta in publishers:
                    content = meta.get('content', '')
                    if re.search(r'Programa de P(?:ó|o)s-Gradua(?:ç|c)(?:ã|a)o', content, re.IGNORECASE):
                        found_program = content
                        break

            if found_program:
                # Limpeza: remove "Programa de Pós-Graduação em", "Programa de Pos Graduacao em", etc.
                # Ex: "Programa de Pós-Graduação em Direitos Humanos" -> "Direitos Humanos"
                clean_name = re.sub(
                    r'Programa de P(?:ó|o)s-Gradua(?:ç|c)(?:ã|a)o (?:em|no|na)?\s*', 
                    '', 
                    found_program, 
                    flags=re.IGNORECASE
                )
                
                data['programa'] = clean_name.strip()
                if on_progress: on_progress(f"UFPE: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"UFPE: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UFPE: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Padrão)
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link na tabela de arquivos
            if not pdf_url:
                # Procura links que contenham '/bitstream/' e terminem em .pdf
                link_tag = soup.find('a', href=lambda h: h and '/bitstream/' in h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta e limpa parâmetros extras se necessário
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UFPE: PDF localizado.")
            else:
                if on_progress: on_progress("UFPE: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UFPE: Erro PDF: {str(e)[:20]}")

        return data
    
