import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UFPRParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UFPR", universidade="Universidade Federal do Paraná")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UFPR (DSpace).
        Trata códigos numéricos nos breadcrumbs e busca metadados específicos.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UFPR: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # A UFPR usa <ul class="breadcrumb"> diferentemente da UFOP (<ol>)
            # Exemplo alvo: 40001016017P3 Programa de Pós-Graduação em Direito
            crumbs = soup.select('ul.breadcrumb li a')
            
            for crumb in crumbs:
                text = crumb.get_text(strip=True)
                
                # Verifica se é o item do Programa
                if "Programa de Pós-Graduação" in text:
                    # Regex ajustada para remover:
                    # 1. Qualquer coisa no início (.*?) como códigos numéricos (40001016017P3)
                    # 2. A expressão "Programa de Pós-Graduação"
                    # 3. Preposições opcionais (em, no, na)
                    # O que sobrar é o nome do curso (ex: Direito)
                    clean_name = re.sub(
                        r'.*?Programa de Pós-Graduação\s*(em|no|na)?\s*', 
                        '', 
                        text, 
                        flags=re.IGNORECASE
                    )
                    found_program = clean_name.strip()
                    break 
            
            if found_program:
                data['programa'] = found_program
                if on_progress: on_progress(f"UFPR: Programa identificado: {found_program}")
            else:
                # Fallback: Meta tags (DC.contributor é muito usado na UFPR)
                # Ex: <meta name="DC.contributor" content="... Programa de Pós-Graduação em Direito">
                meta_contribs = soup.find_all('meta', attrs={'name': 'DC.contributor'})
                for meta in meta_contribs:
                    content = meta.get('content', '')
                    if "Programa de Pós-Graduação" in content:
                        clean_name = re.sub(r'.*?Programa de Pós-Graduação\s*(em|no|na)?\s*', '', content, flags=re.IGNORECASE)
                        data['programa'] = clean_name.strip()
                        break

        except Exception as e:
            if on_progress: on_progress(f"UFPR: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UFPR: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag (Padrão DSpace/Google Scholar)
            # <meta name="citation_pdf_url" content="...">
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link direto 'bitstream' na tabela de arquivos
            if not pdf_url:
                link_tag = soup.find('a', href=lambda h: h and 'bitstream' in h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UFPR: PDF localizado.")
            else:
                if on_progress: on_progress("UFPR: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UFPR: Erro PDF: {str(e)[:20]}")

        return data