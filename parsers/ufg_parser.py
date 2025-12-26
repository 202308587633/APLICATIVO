import re
import warnings
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UFGParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UFG", universidade="Universidade Federal de Goiás")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UFG (DSpace 7.x).
        """
        # --- FIX 1: Variáveis locais para evitar AttributeError no 'self' ---
        sigla = "UFG"
        universidade = "Universidade Federal de Goiás"

        # --- FIX 2: Suprimir aviso de URL vs HTML ---
        warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

        # Verificação de segurança para HTML vazio
        if not html_content:
            return {
                'sigla': sigla,
                'universidade': universidade,
                'programa': '-',
                'link_pdf': '-'
            }

        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': sigla,
            'universidade': universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UFG: Analisando estrutura DSpace 7...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # ESTRATÉGIA A (Solicitada): Busca na div de Coleções
            # Ex: <div class="collections"><a ...><span>Mestrado em Direito Agrário (FD)</span></a></div>
            collections_div = soup.find('div', class_='collections')
            
            if collections_div:
                # Pega o texto do primeiro link dentro dessa div
                link_tag = collections_div.find('a')
                if link_tag:
                    found_program = link_tag.get_text(strip=True)

            # ESTRATÉGIA B (Fallback): Breadcrumbs (Trilha de navegação)
            # DSpace 7 costuma ter: Home > Comunidade > Programa > Coleção
            if not found_program:
                breadcrumbs = soup.select('ol.breadcrumb li.breadcrumb-item')
                for crumb in breadcrumbs:
                    text = crumb.get_text(strip=True)
                    if "Programa" in text or "Mestrado" in text or "Doutorado" in text:
                        found_program = text

            # LIMPEZA E TRATAMENTO
            if found_program:
                # Remove prefixos comuns para deixar só o nome do curso
                clean_name = re.sub(
                    r'^(Programa de Pós-graduação|Mestrado|Doutorado)\s*(em|no|na)?\s+', 
                    '', 
                    found_program, 
                    flags=re.IGNORECASE
                )
                
                # Remove espaços extras e pontuação no início/fim
                data['programa'] = clean_name.strip(' .;-')
                
                if on_progress: on_progress(f"UFG: Programa identificado: {data['programa']}")
            else:
                if on_progress: on_progress("UFG: Programa não identificado na seção de coleções.")

        except Exception as e:
            if on_progress: on_progress(f"UFG: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UFG: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Tática 1: Meta Tag citation_pdf_url (A mais confiável no DSpace 7)
            # Ex: <meta name="citation_pdf_url" content="...">
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Tática 2: Link direto com tipo 'application/pdf' (Presente no head do exemplo)
            if not pdf_url:
                link_pdf = soup.find('link', attrs={'type': 'application/pdf'})
                if link_pdf:
                    pdf_url = link_pdf.get('href')

            # Tática 3: Botão de Download na interface (Fallback)
            if not pdf_url:
                # Procura links que contenham 'bitstreams' e terminem com 'download' ou '.pdf'
                dl_link = soup.find('a', href=lambda x: x and 'bitstreams' in x and ('download' in x or x.endswith('.pdf')))
                if dl_link:
                    pdf_url = dl_link['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UFG: PDF localizado.")
            else:
                if on_progress: on_progress("UFG: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UFG: Erro PDF: {str(e)[:20]}")

        return data