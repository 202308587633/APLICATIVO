import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UNINTERParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UNINTER", universidade="Centro Universitário Internacional")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UNINTER (DSpace 6 - Mirage2).
        Foca na extração do Programa a partir da lista de Coleções e meta tags para o PDF.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UNINTER: Analisando estrutura da página (Mirage2)...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia A: Metadados Visuais "Collections" (Conforme exemplo fornecido)
            # <div class="simple-item-view-collections ..."> ... <ul class="ds-referenceSet-list"> <li> <a ...>Mestrado Acadêmico em Direito</a>
            collections_div = soup.find('div', class_='simple-item-view-collections')
            if collections_div:
                collection_link = collections_div.find('a', href=True)
                if collection_link:
                    found_program = collection_link.get_text(strip=True)

            # Estratégia B: Breadcrumbs (Trilha de navegação)
            # <ul class="breadcrumb"> ... <li><a ...>Mestrado Acadêmico em Direito</a></li> ...
            if not found_program:
                crumbs = soup.select('ul.breadcrumb li a')
                for crumb in crumbs:
                    text = crumb.get_text(strip=True)
                    # Procura por padrões de programa
                    if "Mestrado" in text or "Doutorado" in text or "Programa" in text:
                        # Ignora níveis genéricos
                        if text not in ["Página inicial", "Teses e Dissertações", "Mestrado UNINTER"]:
                            found_program = text
                            # Geralmente o último nível específico antes do item é o programa
                            # Mas em breadcrumbs, o último <li> é o item atual (active), o penúltimo é a coleção/programa
            
            if found_program:
                # Limpeza:
                # Remove "Mestrado Acadêmico em", "Programa de Pós-Graduação em", etc.
                clean_name = re.sub(
                    r'^(?:Mestrado|Doutorado|Programa de Pós-Graduação)(?:\s+(?:Acadêmico|Profissional))?(?: em| no| na)?\s*', 
                    '', 
                    found_program, 
                    flags=re.IGNORECASE
                )
                data['programa'] = clean_name.strip()
                if on_progress: on_progress(f"UNINTER: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"UNINTER: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UNINTER: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Padrão e presente no HTML)
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link na tabela de visualização do item (Mirage2)
            if not pdf_url:
                # Procura links que contenham 'bitstream' e terminem em .pdf, geralmente dentro de item-page-field-wrapper
                link_tag = soup.find('a', href=lambda h: h and '/bitstream/' in h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UNINTER: PDF localizado.")
            else:
                if on_progress: on_progress("UNINTER: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UNINTER: Erro PDF: {str(e)[:20]}")

        return data
    
    