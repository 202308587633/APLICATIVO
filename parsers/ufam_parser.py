import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UFAMParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UFAM", universidade="Universidade Federal do Amazonas")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UFAM (Interface VuFind/TEDE).
        Foca nas tabelas de metadados (th/td) para encontrar o Programa.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UFAM: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia 1: Busca na tabela de metadados pelo campo específico 'dc.publisher.none.fl_str_mv'
            # O HTML mostra: <th>dc.publisher.none.fl_str_mv</th> ... <td> ... Programa ... </td>
            # Esse campo contém várias linhas (Universidade, Faculdade, País, Sigla, Programa)
            target_th = soup.find('th', string=re.compile(r'dc\.publisher\.none\.fl_str_mv', re.IGNORECASE))
            
            if target_th:
                td = target_th.find_next_sibling('td')
                if td:
                    # O conteúdo é separado por <br>, então pegamos o texto com separador
                    text_content = td.get_text(separator='\n', strip=True)
                    lines = text_content.split('\n')
                    
                    for line in lines:
                        if "Programa de Pós-Graduação" in line:
                            found_program = line.strip()
                            break

            # Estratégia 2: Busca pelo rótulo visível "Programa de Pós-Graduação:"
            # Ex: <th>Programa de Pós-Graduação:</th>
            if not found_program:
                label_th = soup.find('th', string=re.compile(r'Programa de Pós-Graduação', re.I))
                if label_th:
                    td = label_th.find_next_sibling('td')
                    if td:
                        text = td.get_text(strip=True)
                        if "Não Informado" not in text:
                            found_program = text

            # Estratégia 3: Metadados DC.publisher (Meta tags)
            if not found_program:
                # <meta name="DC.publisher" content="...">
                publishers = soup.find_all('meta', attrs={'name': 'DC.publisher'})
                for meta in publishers:
                    content = meta.get('content', '')
                    if "Programa de" in content:
                        found_program = content
                        break

            if found_program:
                # Limpeza: remove "Programa de Pós-Graduação em"
                clean_name = re.sub(
                    r'Programa de Pós-Graduação\s*(?:em|no|na)?\s*', 
                    '', 
                    found_program, 
                    flags=re.IGNORECASE
                )
                data['programa'] = clean_name.strip()
                if on_progress: on_progress(f"UFAM: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"UFAM: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UFAM: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url
            # Nota: No exemplo fornecido, o citation_pdf_url aponta para o handle, não para o PDF.
            # Vamos checar se termina em .pdf. Se não, tentamos outras estratégias.
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                candidate = pdf_meta.get('content')
                if candidate and candidate.lower().endswith('.pdf'):
                    pdf_url = candidate
            
            # Estratégia B: Link direto 'bitstream' na página
            if not pdf_url:
                # Procura links que contenham 'bitstream' e terminem em .pdf
                link_tag = soup.find('a', href=lambda h: h and 'bitstream' in h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            # Estratégia C: Busca genérica por links de download/texto completo
            if not pdf_url:
                # Procura links com texto "Texto completo", "Download", etc que apontem para PDF
                # No HTML de exemplo: <a href="/Busca/Download?codigoArquivo=..." class="pdf-file" ...>
                dl_link = soup.find('a', class_='pdf-file') or soup.find('a', string=re.compile(r'Texto completo|Download', re.I))
                
                if dl_link and dl_link.get('href'):
                    href = dl_link['href']
                    # Se for link do VuFind (/Busca/Download...), aceitamos
                    if 'Download' in href or href.lower().endswith('.pdf'):
                        pdf_url = href

            if pdf_url:
                # Normaliza URL
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UFAM: PDF localizado.")
            else:
                if on_progress: on_progress("UFAM: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UFAM: Erro PDF: {str(e)[:20]}")

        return data
    
    