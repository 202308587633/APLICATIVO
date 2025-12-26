import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UFUParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UFU", universidade="Universidade Federal de Uberlândia")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UFU (DSpace 6.3).
        Utiliza classes CSS específicas dos metadados (dc_publisher_program) para precisão.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UFU: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia 1: Busca pela classe específica do DSpace
            # O HTML mostra: <td class="metadataFieldValue dc_publisher_program">...</td>
            prog_td = soup.find('td', class_='metadataFieldValue dc_publisher_program')
            if prog_td:
                found_program = prog_td.get_text(strip=True)
            
            # Estratégia 2: Busca por meta tags (Padrão Dublin Core)
            # <meta name="DC.publisher" content="Programa de Pós-graduação em Direito">
            if not found_program:
                publishers = soup.find_all('meta', attrs={'name': 'DC.publisher'})
                for meta in publishers:
                    content = meta.get('content', '')
                    # Verifica se parece um programa (tem "Programa" ou "Pós-graduação")
                    if 'Programa' in content or 'Pós-graduação' in content:
                        found_program = content
                        break

            if found_program:
                # Limpeza: remove "Programa de Pós-graduação em"
                clean_name = re.sub(
                    r'Programa de Pós-graduação (em|no|na)?\s*', 
                    '', 
                    found_program, 
                    flags=re.IGNORECASE
                )
                
                data['programa'] = clean_name.strip()
                if on_progress: on_progress(f"UFU: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"UFU: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UFU: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Padrão e presente no HTML)
            # Obs: No HTML de exemplo não havia citation_pdf_url explícito, mas é padrão DSpace.
            # Vamos manter a busca por precaução.
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link na tabela de arquivos
            # No exemplo: <a href="/bitstream/123456789/29269/7/DiscursoJudicialCriminalizacao.pdf">
            if not pdf_url:
                # Procura links que contenham '/bitstream/' e terminem em .pdf
                link_tag = soup.find('a', href=lambda h: h and '/bitstream/' in h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UFU: PDF localizado.")
            else:
                if on_progress: on_progress("UFU: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UFU: Erro PDF: {str(e)[:20]}")

        return data
    
    