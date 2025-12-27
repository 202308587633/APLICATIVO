import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UFERSAParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UFERSA", universidade="Universidade Federal Rural do Semi-Árido")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UFERSA (DSpace 7 - Angular).
        Foca nos breadcrumbs para identificar o Programa e meta tags para o PDF.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UFERSA: Analisando estrutura da página (DSpace 7)...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia Principal: Breadcrumbs (Trilha de navegação)
            # O HTML mostra: <ol class="container breadcrumb"> ... <li>PROGRAMA DE PÓS-GRADUAÇÃO EM DIREITO</li> ... </ol>
            crumbs = soup.select('ol.breadcrumb li')
            
            for crumb in crumbs:
                text = crumb.get_text(strip=True)
                
                # Ignora itens genéricos
                if text in ["Início", "BIBLIOTECA DIGITAL DE TESES E DISSERTAÇÕES - BDTD"]:
                    continue
                
                # Tenta identificar o programa. Na UFERSA, geralmente aparece em caixa alta:
                # "PROGRAMA DE PÓS-GRADUAÇÃO EM DIREITO"
                if "PROGRAMA DE PÓS-GRADUAÇÃO" in text.upper():
                    found_program = text
                    break
                
                # Fallback: Se não achar o "Programa...", tenta achar "Mestrado em" ou "Doutorado em"
                # Ex: "Mestrado em Direito"
                if "MESTRADO EM" in text.upper() or "DOUTORADO EM" in text.upper():
                    found_program = text
                    # Não damos break aqui imediatamente caso haja um nível superior mais descritivo
            
            if found_program:
                # Limpeza:
                # Remove "PROGRAMA DE PÓS-GRADUAÇÃO EM", "Mestrado em", etc.
                # Regex case insensitive para pegar variações
                clean_name = re.sub(
                    r'^(PROGRAMA DE PÓS-GRADUAÇÃO|MESTRADO|DOUTORADO|CURSO)\s+(EM|NO|NA)\s*', 
                    '', 
                    found_program, 
                    flags=re.IGNORECASE
                )
                
                # Converte para Title Case (Ex: "DIREITO" -> "Direito") para ficar padronizado
                data['programa'] = clean_name.strip().title()
                
                if on_progress: on_progress(f"UFERSA: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"UFERSA: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UFERSA: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Padrão e presente no HTML da UFERSA)
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
                if on_progress: on_progress("UFERSA: PDF localizado.")
            else:
                if on_progress: on_progress("UFERSA: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UFERSA: Erro PDF: {str(e)[:20]}")

        return data
    
