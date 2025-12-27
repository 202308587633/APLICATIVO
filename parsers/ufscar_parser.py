import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UFSCARParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UFSCAR", universidade="Universidade Federal de São Carlos")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UFSCAR (DSpace 9.1 - Angular).
        Foca na extração do Programa a partir do campo 'Citação' e meta tags para o PDF.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UFSCAR: Analisando estrutura da página (DSpace 9)...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # O DSpace 9 exibe metadados em blocos <div class="simple-view-element">
            # Vamos iterar sobre eles para achar 'Citação'
            elements = soup.find_all('div', class_='simple-view-element')
            
            for el in elements:
                header = el.find(class_='simple-view-element-header')
                if not header:
                    continue
                
                header_text = header.get_text(strip=True).lower()
                
                # Estratégia A: Campo "Citação" (Conforme seu exemplo)
                # Ex: "... Dissertação (Mestrado em Enfermagem) – Universidade..."
                if 'citação' in header_text:
                    body = el.find(class_='simple-view-element-body')
                    if body:
                        content_text = body.get_text(strip=True)
                        # Regex para capturar o texto dentro dos parênteses após Mestrado/Doutorado em
                        match = re.search(
                            r'(?:Mestrado|Doutorado|Mestre|Doutor)(?:\s+Profissional|\s+Acadêmico)?\s+em\s+([^)\-]+)', 
                            content_text, 
                            re.IGNORECASE
                        )
                        if match:
                            found_program = match.group(1).strip()
                            break

            # Estratégia B: Fallback para breadcrumbs se a citação não funcionar
            if not found_program:
                crumbs = soup.select('ol.breadcrumb li')
                for crumb in crumbs:
                    text = crumb.get_text(strip=True)
                    if "Programa de Pós-Graduação" in text:
                        found_program = text
                        break

            if found_program:
                # Limpeza final
                clean_name = re.sub(
                    r'^(?:Programa de Pós-Graduação|Curso|Mestrado|Doutorado)(?:\s+(?:Profissional|Acadêmico))?(?: em| no| na)?\s*', 
                    '', 
                    found_program, 
                    flags=re.IGNORECASE
                )
                clean_name = clean_name.strip('.,- ')
                
                data['programa'] = clean_name
                if on_progress: on_progress(f"UFSCAR: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"UFSCAR: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UFSCAR: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Padrão e presente no HTML da UFSCar)
            # <meta name="citation_pdf_url" content="...">
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
                # Garante URL absoluta (embora no seu exemplo já venha http://127.0.0.1:4000, vamos corrigir para o domínio real se necessário)
                # Nota: O HTML fornecido tem citation_pdf_url apontando para localhost. 
                # Vamos assumir que em produção ele aponta para o domínio correto ou usar urljoin.
                if '127.0.0.1' in pdf_url or 'localhost' in pdf_url:
                     # Tenta corrigir URL de localhost para o domínio base se detectado
                     path = pdf_url.split('/bitstreams/')[-1]
                     pdf_url = f"https://repositorio.ufscar.br/bitstreams/{path}"
                
                data['link_pdf'] = urljoin("https://repositorio.ufscar.br", pdf_url) # Garante base correta
                if on_progress: on_progress("UFSCAR: PDF localizado.")
            else:
                if on_progress: on_progress("UFSCAR: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UFSCAR: Erro PDF: {str(e)[:20]}")

        return data
    
