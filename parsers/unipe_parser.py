import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UNIPEParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UNIPÊ", universidade="Centro Universitário de João Pessoa")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UNIPÊ (DSpace 7/8 - Infraestrutura Cruzeiro do Sul).
        Foca nos breadcrumbs para identificar o Programa e meta tags para o PDF.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UNIPÊ: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # O DSpace 7/8 usa breadcrumbs na estrutura <ol class="breadcrumb">
            # Ex: Início > UNIPÊ > Dissertações > Mestrado em Direito
            crumbs = soup.select('ol.breadcrumb li')
            
            for crumb in crumbs:
                text = crumb.get_text(strip=True)
                
                # Ignora itens genéricos de navegação
                if text in ["Início", "UNIPÊ", "Dissertações", "Teses", "Comunidades & Coleções"]:
                    continue
                
                # Tenta identificar o programa baseado em palavras-chave de pós-graduação
                # No exemplo: "Mestrado em Direito"
                if any(k in text for k in ["Mestrado", "Doutorado", "Pós-Graduação"]):
                    # Limpeza: remove "Mestrado em", "Doutorado em", etc.
                    clean_name = re.sub(
                        r'^(?:Programa de Pós-Graduação|Mestrado|Doutorado|Curso)\s*(?:em|no|na)?\s*', 
                        '', 
                        text, 
                        flags=re.IGNORECASE
                    )
                    
                    found_program = clean_name.strip()
                    # Geralmente o programa é o último ou penúltimo item específico
                    # Se achamos algo válido, atualizamos (continuamos o loop caso haja algo mais específico, 
                    # mas geralmente paramos na coleção)
            
            # Se não achou pelo loop (caso o nome da coleção não tenha "Mestrado"), 
            # tenta pegar o último breadcrumb que não seja o título do trabalho
            if not found_program and len(crumbs) > 2:
                # Pega o penúltimo item (o último é o título do trabalho, ativo)
                candidate = crumbs[-2].get_text(strip=True)
                if candidate not in ["Dissertações", "Teses"]:
                    found_program = candidate

            if found_program:
                data['programa'] = found_program
                if on_progress: on_progress(f"UNIPÊ: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"UNIPÊ: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UNIPÊ: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Padrão e presente no HTML)
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link na seção de arquivos (DSpace 7/8 Angular)
            if not pdf_url:
                # Procura links que contenham '/bitstreams/' e '/download'
                link_tag = soup.find('a', href=lambda h: h and '/bitstreams/' in h and '/download' in h)
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UNIPÊ: PDF localizado.")
            else:
                if on_progress: on_progress("UNIPÊ: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UNIPÊ: Erro PDF: {str(e)[:20]}")

        return data
    
    