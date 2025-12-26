import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UniforParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UNIFOR", universidade="Universidade de Fortaleza")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UNIFOR.
        Identifica o programa procurando por links com título específico,
        suportando 'Mestrado Profissional', 'Doutorado', etc.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UNIFOR: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Palavras-chave para identificar o link do programa
            # Abrange: "Programa de Pós-Graduação", "Mestrado Profissional", "Mestrado", "Doutorado"
            keywords_regex = r'(Programa de Pós-Graduação|Mestrado|Doutorado)'
            
            # 1. Tenta achar pelo atributo 'title' (mais comum na Unifor)
            target_link = soup.find('a', title=re.compile(keywords_regex, re.IGNORECASE))
            
            # 2. Se não achar, tenta pelo texto visível do link
            if not target_link:
                target_link = soup.find('a', string=re.compile(keywords_regex, re.IGNORECASE))

            if target_link:
                # Pega o conteúdo: prefere o title, senão o texto
                raw_text = target_link.get('title') if target_link.get('title') else target_link.get_text(strip=True)
                
                # Etapa A: Remove o nome da universidade e pontuação inicial
                # Ex: "Universidade de Fortaleza. Mestrado..." -> "Mestrado..."
                text_no_uni = re.sub(r'Universidade de Fortaleza\.?\s*', '', raw_text, flags=re.IGNORECASE)
                
                # Etapa B: Remove o prefixo do tipo de curso e preposições
                # Remove: "Mestrado Profissional em ", "Programa de Pós-Graduação na ", etc.
                clean_name = re.sub(
                    r'^(Programa de Pós-Graduação|Mestrado Profissional|Mestrado|Doutorado)\s*(em|no|na|de)?\s+', 
                    '', 
                    text_no_uni, 
                    flags=re.IGNORECASE
                )
                
                found_program = clean_name.strip()

            if found_program:
                data['programa'] = found_program
                if on_progress: on_progress(f"UNIFOR: Programa identificado: {found_program}")
            else:
                # Fallback: Meta tags padrão
                meta_prog = soup.find('meta', attrs={'name': 'citation_publisher'})
                if meta_prog:
                    data['programa'] = meta_prog.get('content')

        except Exception as e:
            if on_progress: on_progress(f"UNIFOR: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UNIFOR: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link genérico de download
            if not pdf_url:
                link_tag = soup.find('a', href=lambda h: h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UNIFOR: PDF localizado.")
            else:
                if on_progress: on_progress("UNIFOR: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UNIFOR: Erro PDF: {str(e)[:20]}")

        return data