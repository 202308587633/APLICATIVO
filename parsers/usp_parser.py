import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class USPParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="USP", universidade="Universidade de São Paulo")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da USP (teses.usp.br).
        Utiliza Meta Tags Dublin Core como fonte primária e estrutura de DIVs como fallback.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("USP: Analisando metadados...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        found_program = None

        # Estratégia A: Meta Tag DC.publisher.program (Muito confiável na USP)
        # Ex: <meta name="dc.publisher.program" content="Semiótica e Lingüística Geral">
        try:
            meta_prog = soup.find('meta', attrs={'name': 'dc.publisher.program'})
            if meta_prog:
                found_program = meta_prog.get('content')
        except: pass

        # Estratégia B: Visual (Área do Conhecimento)
        # Procura a div com título "Área do Conhecimento" e pega a próxima div de texto
        if not found_program:
            try:
                # <div class="DocumentoTituloTexto">Área do Conhecimento</div>
                label_div = soup.find('div', class_='DocumentoTituloTexto', string=re.compile(r'Área do Conhecimento', re.I))
                if label_div:
                    # A div com o valor vem logo em seguida: <div class="DocumentoTexto">...</div>
                    value_div = label_div.find_next_sibling('div', class_='DocumentoTexto')
                    if value_div:
                        found_program = value_div.get_text(strip=True)
            except Exception as e:
                if on_progress: on_progress(f"USP: Erro visual programa: {e}")

        if found_program:
            data['programa'] = found_program.strip()
            if on_progress: on_progress(f"USP: Programa detectado: {data['programa']}")
        else:
            if on_progress: on_progress("USP: Programa não identificado.")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Padrão Google Scholar)
            # <meta name="citation_pdf_url" content="...">
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')

            # Estratégia B: Link direto na classe "DocumentoTituloTexto2"
            # O layout da USP costuma colocar o link do PDF dentro dessa classe específica
            if not pdf_url:
                div_pdf = soup.find('div', class_='DocumentoTituloTexto2')
                if div_pdf:
                    link = div_pdf.find('a', href=re.compile(r'\.pdf$', re.I))
                    if link:
                        pdf_url = link['href']

            # Estratégia C: Varredura Genérica
            if not pdf_url:
                link = soup.find('a', href=re.compile(r'bitstream.*\.pdf$|/publico/.*\.pdf$', re.I))
                if link:
                    pdf_url = link['href']

            if pdf_url:
                # Garante URL absoluta (USP às vezes usa links relativos ou http misto)
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("USP: PDF localizado.")
            else:
                if on_progress: on_progress("USP: PDF não encontrado.")

        except Exception as e:
            if on_progress: on_progress(f"USP: Erro PDF: {e}")

        return data