import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UCSALParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UCSAL", universidade="Universidade Católica do Salvador")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UCSAL (DSpace 7 - Angular).
        Foca nos breadcrumbs para identificar o Programa e meta tags para o PDF.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UCSAL: Analisando estrutura da página (DSpace 7)...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia: Breadcrumbs (Trilha de navegação)
            # Estrutura típica no HTML fornecido:
            # Home -> Pró-Reitoria... -> [NOME DO PROGRAMA] -> Dissertações... -> Título
            crumbs = soup.select('ol.breadcrumb li')
            
            for crumb in crumbs:
                text = crumb.get_text(strip=True)
                
                # Ignora itens de nível superior ou genéricos
                if text in ["Home", "Início", "Pró-Reitoria de Pesquisa e Pós-Graduação"]:
                    continue
                
                # Ignora o nível da coleção (onde ficam os documentos)
                if "Dissertações" in text or "Teses" in text:
                    continue
                
                # Ignora o próprio título da tese/dissertação (geralmente o último item e 'active')
                if "active" in crumb.get('class', []):
                    continue

                # Se passou pelos filtros, é provavelmente o nome do Programa
                # Ex: "Território, Ambiente e Sociedade"
                if text:
                    found_program = text
                    # Não damos break imediatamente, mas armazenamos. 
                    # Na estrutura da UCSAL, o programa vem antes da coleção de Teses/Dissertações.
            
            if found_program:
                # Limpeza: Caso haja prefixos como "Programa de Pós-Graduação em"
                clean_name = re.sub(
                    r'^(?:Programa de |)Pós-Graduação (?:em|no|na)\s*', 
                    '', 
                    found_program, 
                    flags=re.IGNORECASE
                )
                
                data['programa'] = clean_name.strip()
                if on_progress: on_progress(f"UCSAL: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"UCSAL: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UCSAL: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Padrão e presente no HTML fornecido)
            # <meta name="citation_pdf_url" content="...">
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link na seção de arquivos (DSpace 7)
            if not pdf_url:
                # Procura links que contenham '/bitstreams/' e '/download'
                link_tag = soup.find('a', href=lambda h: h and '/bitstreams/' in h and '/download' in h)
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UCSAL: PDF localizado.")
            else:
                if on_progress: on_progress("UCSAL: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UCSAL: Erro PDF: {str(e)[:20]}")

        return data
    