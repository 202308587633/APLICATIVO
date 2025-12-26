import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UFOPParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UFOP", universidade="Universidade Federal de Ouro Preto")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UFOP (DSpace/Angular).
        Aprimorado para lidar com prefixos de siglas no Breadcrumb (ex: PPGHis - ...).
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UFOP: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA (Via Breadcrumb) ---
        try:
            found_program = None
            
            # Seleciona links dentro da lista de breadcrumb
            # Exemplo de HTML alvo: <li ...><a ...>PPGHis - Programa de Pós-graduação em História</a></li>
            crumbs = soup.select('ol.breadcrumb li a, ul.breadcrumb li a')
            
            for crumb in crumbs:
                text = crumb.get_text(strip=True)
                
                # Verifica se é o item do Programa (ignorando maiúsculas/minúsculas)
                if "Programa de Pós-Graduação" in text or "Programa de Pós-graduação" in text:
                    # Regex Aprimorada:
                    # 1. '.*' no início: casa com qualquer coisa antes (ex: "PPGHis - ")
                    # 2. Remove a frase "Programa de Pós-Graduação" e preposições
                    clean_name = re.sub(
                        r'.*Programa de Pós-Graduação\s*(em|no|na)?\s*', 
                        '', 
                        text, 
                        flags=re.IGNORECASE
                    )
                    
                    # Remove sufixos comuns que possam sobrar ou hífens no início
                    clean_name = clean_name.strip(" -")
                    
                    if clean_name:
                        found_program = clean_name
                        break 
            
            if found_program:
                data['programa'] = found_program
                if on_progress: on_progress(f"UFOP: Programa identificado: {found_program}")
            else:
                # Fallback: Tenta meta tags padrão se o breadcrumb falhar
                meta_prog = soup.find('meta', attrs={'name': 'citation_publisher'}) # Às vezes o programa está aqui na UFOP
                if meta_prog:
                    # Tenta limpar se vier com nome da universidade junto
                    prog_text = meta_prog.get('content', '')
                    if "Universidade" not in prog_text:
                        data['programa'] = prog_text

        except Exception as e:
            if on_progress: on_progress(f"UFOP: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UFOP: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link direto 'bitstream' (Comum em DSpace)
            if not pdf_url:
                # Procura links que contenham 'bitstream' e terminem em .pdf
                link_tag = soup.find('a', href=lambda h: h and 'bitstream' in h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            # Estratégia C: Botão de Download (Estrutura Angular UFOP)
            if not pdf_url:
                # Procura links com texto "Visualizar/Abrir" ou similar
                dl_link = soup.find('a', string=re.compile(r'Visualizar|Abrir|Download', re.I))
                if dl_link and dl_link.get('href'):
                    href = dl_link['href']
                    if 'bitstream' in href:
                        pdf_url = href

            if pdf_url:
                # Normaliza URL (adiciona domínio se for relativo)
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UFOP: PDF localizado.")
            else:
                if on_progress: on_progress("UFOP: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UFOP: Erro PDF: {str(e)[:20]}")

        return data