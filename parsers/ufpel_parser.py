import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UFPELParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UFPEL", universidade="Universidade Federal de Pelotas")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UFPEL (DSpace 6.4 / Mirage2).
        Foca nos breadcrumbs para o Programa e meta tags para o PDF.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UFPEL: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # O repositório UFPEL organiza a hierarquia nos breadcrumbs (visíveis ou no menu dropdown mobile)
            # Exemplo: <a ...>Pós-Graduação em Direito - PPGD</a>
            
            # Seleciona links tanto do breadcrumb desktop quanto do menu mobile
            crumbs = soup.select('.breadcrumb li a, .dropdown-menu li a')
            
            for crumb in crumbs:
                text = crumb.get_text(strip=True)
                
                # Procura por "Pós-Graduação"
                if "Pós-Graduação" in text:
                    # Regex para limpar o nome
                    # Captura o que vem depois de "em" e antes de um hífen opcional ou fim da string
                    match = re.search(r'Pós-Graduação\s*(?:em|no|na)?\s+(.*?)(?:\s+-\s+|$)', text, re.IGNORECASE)
                    
                    if match:
                        found_program = match.group(1).strip()
                        # Remove a sigla se ela tiver ficado no final (ex: "Direito PPGD")
                        found_program = re.sub(r'\s+[A-Z0-9]+$', '', found_program)
                        break
                    else:
                        # Fallback simples se o regex falhar mas for a linha correta
                        found_program = text.replace("Pós-Graduação em", "").replace("- PPGD", "").strip()

            if found_program:
                data['programa'] = found_program
                if on_progress: on_progress(f"UFPEL: Programa identificado: {found_program}")

        except Exception as e:
            if on_progress: on_progress(f"UFPEL: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UFPEL: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Presente no HTML fornecido)
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link na seção "Visualizar/Abrir"
            if not pdf_url:
                # Procura links que contenham 'bitstream' e terminem em .pdf
                link_tag = soup.find('a', href=lambda h: h and 'bitstream' in h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UFPEL: PDF localizado.")
            else:
                if on_progress: on_progress("UFPEL: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UFPEL: Erro PDF: {str(e)[:20]}")

        return data