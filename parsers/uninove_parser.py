import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UninoveParser(BaseParser):
    def __init__(self):
        # Definição fixa conforme solicitado
        super().__init__(sigla="UNINOVE", universidade="Universidade Nove de Julho")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UNINOVE.
        Baseado na estrutura de breadcrumbs para o programa e meta tags para o PDF.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UNINOVE: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA (Via Breadcrumb) ---
        try:
            found_program = None
            
            # O HTML da UNINOVE usa <ol class="breadcrumb btn-success">
            # Selecionamos os links dentro dessa estrutura
            crumbs = soup.select('ol.breadcrumb li a')
            
            for crumb in crumbs:
                text = crumb.get_text(strip=True)
                
                # Procura pelo padrão "Programa de Pós-Graduação"
                if "Programa de Pós-Graduação" in text:
                    # Remove o prefixo para sobrar apenas o nome do curso (ex: "Direito")
                    clean_name = re.sub(
                        r'^Programa de Pós-Graduação\s*(em|no|na)?\s*', 
                        '', 
                        text, 
                        flags=re.IGNORECASE
                    )
                    found_program = clean_name.strip()
                    break # Encontrou o nível do programa, pode parar
            
            if found_program:
                data['programa'] = found_program
                if on_progress: on_progress(f"UNINOVE: Programa identificado: {found_program}")
            else:
                if on_progress: on_progress("UNINOVE: Programa não encontrado no breadcrumb.")

        except Exception as e:
            if on_progress: on_progress(f"UNINOVE: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UNINOVE: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag 'citation_pdf_url' (Presente no HTML de exemplo)
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Botão "Baixar/Abrir" (Visual)
            if not pdf_url:
                # Procura links que contenham texto como "Baixar" ou "Abrir"
                link_tag = soup.find('a', string=re.compile(r'Baixar|Abrir|Download', re.I))
                if link_tag and link_tag.get('href'):
                    pdf_url = link_tag['href']

            # Estratégia C: Genérica por extensão .pdf no bitstream
            if not pdf_url:
                link_tag = soup.find('a', href=lambda h: h and 'bitstream' in h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta usando urljoin com a URL base da página
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UNINOVE: PDF localizado.")
            else:
                if on_progress: on_progress("UNINOVE: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UNINOVE: Erro PDF: {str(e)[:20]}")

        return data