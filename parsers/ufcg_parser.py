import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UFCGParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UFCG", universidade="Universidade Federal de Campina Grande")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UFCG (DSpace 4.2).
        Foca nos breadcrumbs para identificar o Programa.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UFCG: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia 1: Busca nos Breadcrumbs (Trilha de navegação)
            # O HTML mostra: 
            # <ol class="breadcrumb">
            #   <li>...</li>
            #   <li>PÓS-GRADUAÇÃO EM HISTÓRIA</li>
            #   <li>Doutorado em História ...</li>
            # </ol>
            crumbs = soup.select('ol.breadcrumb li')
            
            # Varre os breadcrumbs de baixo para cima (do mais específico para o mais geral)
            # ou de cima para baixo. No caso da UFCG, "PÓS-GRADUAÇÃO EM X" costuma ser o pai da coleção "Mestrado/Doutorado"
            for crumb in crumbs:
                text = crumb.get_text(strip=True)
                
                # Ignora itens genéricos
                if text in ["Biblioteca Digital de Teses e Dissertações da UFCG", "Página inicial"]:
                    continue
                
                # Tenta identificar o programa
                # Procura por "PÓS-GRADUAÇÃO" (com ou sem acento), "MESTRADO", "DOUTORADO"
                if re.search(r'(P(?:ó|o)s-Gradua(?:ç|c)(?:ã|a)o|Mestrado|Doutorado)', text, re.IGNORECASE):
                    found_program = text
                    # Se achar "Pós-Graduação", geralmente é o nome oficial do programa (ex: PÓS-GRADUAÇÃO EM HISTÓRIA)
                    # Se achar "Mestrado/Doutorado", pode ser a coleção.
                    # Vamos preferir "Pós-Graduação" se disponível, senão ficamos com o último achado.
                    if "PÓS-GRADUAÇÃO" in text.upper():
                        break 

            if found_program:
                # Limpeza:
                # 1. Remove "PÓS-GRADUAÇÃO EM", "PROGRAMA DE PÓS-GRADUAÇÃO EM"
                clean_name = re.sub(
                    r'^(?:Programa de |)(?:P(?:ó|o)s-Gradua(?:ç|c)(?:ã|a)o|Mestrado|Doutorado)(?: Profissional| Acadêmico)?(?: em| no| na)?\s*', 
                    '', 
                    found_program, 
                    flags=re.IGNORECASE
                )
                
                # 2. Remove sufixos comuns após hífen, se houver (ex: "- DINTER UFCG/USP", "- PPG...")
                clean_name = clean_name.split(' - ')[0]

                data['programa'] = clean_name.strip()
                if on_progress: on_progress(f"UFCG: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"UFCG: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UFCG: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Padrão)
            # O HTML fornecido possui: <meta name="citation_pdf_url" content="...">
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link na tabela de arquivos
            if not pdf_url:
                # Procura links que contenham '/bitstream/' e terminem em .pdf
                link_tag = soup.find('a', href=lambda h: h and '/bitstream/' in h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UFCG: PDF localizado.")
            else:
                if on_progress: on_progress("UFCG: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UFCG: Erro PDF: {str(e)[:20]}")

        return data
    
    