import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class FiocruzParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="FIOCRUZ", universidade="Fundação Oswaldo Cruz")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da FIOCRUZ (Arca - DSpace 8.1).
        Utiliza a estrutura de 'simple-view-element' para localizar o campo 'Programa'.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("FIOCRUZ: Analisando estrutura da página (DSpace 8)...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # O DSpace 7/8 exibe metadados em blocos com a classe 'simple-view-element'
            # Procuramos o bloco cujo cabeçalho ('simple-view-element-header') contenha "Programa"
            elements = soup.find_all('div', class_='simple-view-element')
            
            for el in elements:
                header = el.find(class_='simple-view-element-header')
                if header and "Programa" in header.get_text():
                    body = el.find(class_='simple-view-element-body')
                    if body:
                        found_program = body.get_text(strip=True)
                        break

            # Fallback: Tenta pegar da coleção se o campo explícito não existir
            if not found_program:
                collection_divs = soup.find_all('div', class_='collections')
                for div in collection_divs:
                    text = div.get_text(strip=True)
                    if "Programa" in text or "Mestrado" in text or "Doutorado" in text:
                        found_program = text
                        break

            if found_program:
                # Limpeza: remove "Programa de Pós-Graduação em"
                # Ex: "Programa de Pós-Graduação em Saúde da Criança e da Mulher" -> "Saúde da Criança e da Mulher"
                clean_name = re.sub(
                    r'^(?:Programa de Pós-Graduação|Mestrado|Doutorado|Curso)(?:\s+(?:Profissional|Acadêmico))?(?: em| no| na)?\s*', 
                    '', 
                    found_program, 
                    flags=re.IGNORECASE
                )
                
                data['programa'] = clean_name.strip()
                if on_progress: on_progress(f"FIOCRUZ: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"FIOCRUZ: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("FIOCRUZ: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Padrão DSpace)
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link na seção de arquivos (DSpace 7/8 Angular)
            # Procura links que contenham '/bitstreams/' e '/download'
            if not pdf_url:
                link_tag = soup.find('a', href=lambda h: h and '/bitstreams/' in h and '/download' in h)
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("FIOCRUZ: PDF localizado.")
            else:
                if on_progress: on_progress("FIOCRUZ: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"FIOCRUZ: Erro PDF: {str(e)[:20]}")

        return data
    
