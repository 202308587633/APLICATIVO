import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class USPParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="USP", universidade="Universidade de São Paulo")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da USP.
        Lógica ajustada para encontrar o Programa após 'Unidade da USP' e limpar o nome.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("USP: Analisando HTML...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # ESTRATÉGIA PRINCIPAL: Procura pelo texto exato "Unidade da USP"
            # O HTML tem: <div class="DocumentoTituloTexto">Unidade da USP</div>
            label_node = soup.find(string=lambda t: t and "Unidade da USP" in t)
            
            if label_node:
                # O nó de texto está dentro de uma DIV. Pegamos o pai (a div do título)
                label_div = label_node.parent
                
                # O valor está na próxima DIV irmã
                value_div = label_div.find_next_sibling('div')
                
                if value_div:
                    found_program = value_div.get_text(strip=True)

            # Fallback 1: Se não achou pela Unidade, tenta meta tag específica do programa
            if not found_program:
                meta_prog = soup.find('meta', attrs={'name': 'dc.publisher.program'})
                if meta_prog:
                    found_program = meta_prog.get('content')

            # Fallback 2: Meta tag citation_publisher
            if not found_program:
                meta_pub = soup.find('meta', attrs={'name': 'citation_publisher'})
                if meta_pub:
                    content = meta_pub.get('content', '')
                    if "Programa" in content or "Faculdade" in content:
                        found_program = content

            # --- LIMPEZA E TRATAMENTO FINAL ---
            if found_program:
                # Remove "Faculdade de "
                clean_name = found_program.replace("Faculdade de ", "")
                
                # Remove "de Ribeirão Preto" (Nova solicitação)
                clean_name = clean_name.replace("de Ribeirão Preto", "")
                
                # Remove espaços extras no início/fim
                data['programa'] = clean_name.strip()
                
                if on_progress: on_progress(f"USP: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"USP: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("USP: Buscando PDF...")
            
            pdf_url = None
            
            # Prioridade: Meta Tag 'citation_pdf_url'
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')

            # Fallback: Links com 'bitstream' ou 'download'
            if not pdf_url:
                link_tag = soup.find('a', href=lambda h: h and ('bitstream' in h or 'download' in h) and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("USP: PDF localizado.")
            else:
                if on_progress: on_progress("USP: PDF público não encontrado.")

        except Exception as e:
            if on_progress: on_progress(f"USP: Erro PDF: {str(e)[:20]}")

        return data