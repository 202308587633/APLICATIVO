import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UNIPAMPAParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UNIPAMPA", universidade="Universidade Federal do Pampa")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UNIPAMPA (DSpace 8 - Angular).
        Foca nos breadcrumbs e meta tags para identificar o Programa e o PDF.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UNIPAMPA: Analisando estrutura da página (DSpace 8)...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia A: Meta Tag 'citation_publisher' ou 'DC.publisher.program'
            # O HTML de exemplo tem <meta name="citation_publisher" content="Universidade Federal do Pampa">
            # Mas vamos procurar pela tag específica do programa se existir.
            # No exemplo: <meta name="DC.publisher.program" content="Mestrado Profissional em Políticas Públicas"> (Hipótese baseada em DSpace padrão)
            # Mas no snippet fornecido, temos metadados como DC.subject e citation_keywords. 
            # O DSpace Angular costuma ter muitas meta tags.
            
            # Vamos procurar no head primeiro se houver algo explícito
            # (O HTML fornecido no prompt não mostra 'DC.publisher.program' explicitamente no head, mas é comum em DSpace)
            # Se não achar, vamos para os breadcrumbs que é garantido pelo exemplo.

            # Estratégia B: Breadcrumbs (Trilha de navegação) - CONFORME EXEMPLO
            # O HTML mostra: <ol class="container breadcrumb"> ... <li>Mestrado Profissional em Políticas Públicas</li> ... </ol>
            if not found_program:
                crumbs = soup.select('ol.breadcrumb li')
                
                for crumb in crumbs:
                    text = crumb.get_text(strip=True)
                    
                    # Ignora itens genéricos
                    if text in ["Início", "Teses e Dissertações", "Ciências Humanas-Teses e Dissertações"]:
                        continue
                    
                    # Tenta identificar o programa pelo padrão de texto
                    # Ex: "Mestrado Profissional em Políticas Públicas"
                    if "Mestrado" in text or "Doutorado" in text or "Programa de Pós-Graduação" in text:
                        found_program = text
                        # Geralmente é o penúltimo item, antes do título do trabalho
                        break
            
            if found_program:
                # Limpeza:
                # Remove "Mestrado Profissional em", "Programa de Pós-Graduação em", etc.
                clean_name = re.sub(
                    r'^(?:Programa de |)(?:Pós-Graduação em |)(?:Mestrado|Doutorado)(?:\s+(?:Profissional|Acadêmico))?(?: em| no| na)?\s*', 
                    '', 
                    found_program, 
                    flags=re.IGNORECASE
                )
                
                data['programa'] = clean_name.strip()
                if on_progress: on_progress(f"UNIPAMPA: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"UNIPAMPA: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UNIPAMPA: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Presente no HTML fornecido)
            # <meta name="citation_pdf_url" content="https://repositorio.unipampa.edu.br/bitstreams/4136b98d.../download">
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link na seção de arquivos (DSpace Angular)
            if not pdf_url:
                # Procura links que contenham '/bitstreams/' e '/download'
                link_tag = soup.find('a', href=lambda h: h and '/bitstreams/' in h and '/download' in h)
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UNIPAMPA: PDF localizado.")
            else:
                if on_progress: on_progress("UNIPAMPA: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UNIPAMPA: Erro PDF: {str(e)[:20]}")

        return data
    
    