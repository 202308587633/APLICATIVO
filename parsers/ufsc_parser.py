import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UFSCParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UFSC", universidade="Universidade Federal de Santa Catarina")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UFSC (DSpace 6.x).
        Foca na trilha de navegação (ds-trail) para achar o programa.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UFSC: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # UFSC usa <ul id="ds-trail"> ... <li> ... <a ...>Texto</a>
            # Exemplo: <li><a ...>Programa de Pós-Graduação em Direito</a></li>
            crumbs = soup.select('ul#ds-trail li.ds-trail-link a')
            
            for crumb in crumbs:
                text = crumb.get_text(strip=True)
                
                # Verifica se é o item do Programa
                if "Programa de Pós-Graduação" in text:
                    # Limpeza: Remove "Programa de Pós-Graduação em/no/na"
                    # Exemplo: "Programa de Pós-Graduação em Direito" -> "Direito"
                    clean_name = re.sub(
                        r'.*Programa de Pós-Graduação\s*(em|no|na)?\s*', 
                        '', 
                        text, 
                        flags=re.IGNORECASE
                    )
                    found_program = clean_name.strip()
                    break
            
            # Fallback: Tentar meta tags se o breadcrumb falhar
            if not found_program:
                # Às vezes o programa aparece em dc.publisher ou dc.contributor
                meta_contribs = soup.find_all('meta', attrs={'name': 'DC.contributor'})
                for meta in meta_contribs:
                    content = meta.get('content', '')
                    if "Programa de Pós-Graduação" in content:
                        clean_name = re.sub(r'.*Programa de Pós-Graduação\s*(em|no|na)?\s*', '', content, flags=re.IGNORECASE)
                        found_program = clean_name.strip()
                        break

            if found_program:
                data['programa'] = found_program
                if on_progress: on_progress(f"UFSC: Programa identificado: {found_program}")

        except Exception as e:
            if on_progress: on_progress(f"UFSC: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UFSC: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Presente no HTML da UFSC)
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link direto na tabela de arquivos
            if not pdf_url:
                # Procura links que contenham 'bitstream' e terminem em .pdf
                link_tag = soup.find('a', href=lambda h: h and 'bitstream' in h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UFSC: PDF localizado.")
            else:
                if on_progress: on_progress("UFSC: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UFSC: Erro PDF: {str(e)[:20]}")

        return data