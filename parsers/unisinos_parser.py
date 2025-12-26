import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UnisinosParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UNISINOS", universidade="Universidade do Vale do Rio dos Sinos")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UNISINOS.
        Identifica o programa via Breadcrumb procurando por 'PPG'.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UNISINOS: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA (Via Breadcrumb com 'PPG') ---
        try:
            found_program = None
            
            # Seleciona os links dentro da lista de trilha (ds-trail)
            crumbs = soup.select('ul#ds-trail li a')
            
            for crumb in crumbs:
                text = crumb.get_text(strip=True)
                
                # Verifica se contém "PPG" ou "Programa de Pós-Graduação"
                if "PPG" in text or "Programa de Pós-Graduação" in text:
                    
                    # Regex para remover o prefixo PPG e espaços extras
                    # Ex: "PPG Direito da Empresa dos Negócios" -> "Direito da Empresa dos Negócios"
                    clean_name = re.sub(
                        r'^(PPG|Programa de Pós-Graduação\s*(em|no|na)?)\s+', 
                        '', 
                        text, 
                        flags=re.IGNORECASE
                    )
                    
                    found_program = clean_name.strip()
                    break # Encontrou, para o loop

            if found_program:
                data['programa'] = found_program
                if on_progress: on_progress(f"UNISINOS: Programa identificado: {found_program}")
            else:
                # Fallback: Tenta meta tags padrão
                meta_prog = soup.find('meta', attrs={'name': 'citation_publisher'})
                if meta_prog:
                    data['programa'] = meta_prog.get('content')

        except Exception as e:
            if on_progress: on_progress(f"UNISINOS: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UNISINOS: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link com 'bitstream'
            if not pdf_url:
                link_tag = soup.find('a', href=lambda h: h and 'bitstream' in h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UNISINOS: PDF localizado.")
            else:
                if on_progress: on_progress("UNISINOS: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UNISINOS: Erro PDF: {str(e)[:20]}")

        return data
    
    