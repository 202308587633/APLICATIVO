import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class IDPParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="IDP", universidade="Instituto Brasileiro de Ensino, Desenvolvimento e Pesquisa")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório do IDP (DSpace 6.3).
        Foca nos breadcrumbs para identificar o Programa e meta tags para o PDF.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("IDP: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia: Busca nos Breadcrumbs (Conforme exemplo fornecido)
            # <ol class="breadcrumb btn-success">
            #   <li>...</li>
            #   <li>...Mestrado Acadêmico em Direito Constitucional</li>
            # </ol>
            crumbs = soup.select('ol.breadcrumb li')
            
            for crumb in crumbs:
                text = crumb.get_text(strip=True)
                
                # Ignora itens genéricos
                if text in ["DSpace IDP", "Página inicial", "Comunidades e coleções"]:
                    continue
                
                # Tenta identificar o programa
                if any(k in text for k in ["Mestrado", "Doutorado", "Programa"]):
                    found_program = text
                    # Geralmente o programa é o último ou penúltimo item específico
            
            if found_program:
                # Limpeza: remove "Mestrado Acadêmico em", "Mestrado Profissional em", etc.
                # Ex: "Mestrado Acadêmico em Direito Constitucional" -> "Direito Constitucional"
                clean_name = re.sub(
                    r'^(?:Programa de Pós-Graduação|Mestrado|Doutorado)(?:\s+(?:Profissional|Acadêmico))?(?: em| no| na)?\s*', 
                    '', 
                    found_program, 
                    flags=re.IGNORECASE
                )
                
                data['programa'] = clean_name.strip()
                if on_progress: on_progress(f"IDP: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"IDP: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("IDP: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Padrão e presente no HTML)
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link na tabela de arquivos (Visualizar/Abrir)
            if not pdf_url:
                # Procura links que contenham '/bitstream/' e terminem em .pdf
                link_tag = soup.find('a', href=lambda h: h and '/bitstream/' in h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("IDP: PDF localizado.")
            else:
                if on_progress: on_progress("IDP: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"IDP: Erro PDF: {str(e)[:20]}")

        return data
    
    