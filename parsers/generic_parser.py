import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class GenericParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="-", universidade="-")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Parser Genérico Otimizado.
        Tenta múltiplas estratégias baseadas em padrões comuns de repositórios (DSpace, EPrints, etc).
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("Genérico: Analisando página com estratégias múltiplas...")

        # --- 1. TENTATIVA DE IDENTIFICAR UNIVERSIDADE (Se não definida) ---
        if data['universidade'] == '-':
            # Tenta meta tags comuns
            meta_pub = soup.find('meta', attrs={'name': re.compile(r'publisher|institution', re.I)})
            if meta_pub and meta_pub.get('content'):
                data['universidade'] = meta_pub.get('content').strip()
            # Tenta título da página
            elif soup.title:
                title_parts = soup.title.get_text().split('|')
                if len(title_parts) > 1:
                    data['universidade'] = title_parts[-1].strip()

        # --- 2. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # ESTRATÉGIA A: Meta Tags específicas
            # Muitos repositórios colocam o programa em 'citation_technical_report_institution' ou similar
            if not found_program:
                meta_prog = soup.find('meta', attrs={'name': re.compile(r'program|department|thesis\.degree\.name', re.I)})
                if meta_prog:
                    found_program = meta_prog.get('content')

            # ESTRATÉGIA B: Breadcrumbs (Trilhas de Navegação)
            # Procura por listas ou divs com classe 'breadcrumb', 'trail', etc.
            if not found_program:
                crumbs = soup.select('.breadcrumb li a, #ds-trail a, .trail a')
                for crumb in crumbs:
                    text = crumb.get_text(strip=True)
                    if any(x in text.lower() for x in ['programa', 'pós-graduação', 'mestrado', 'doutorado']):
                        found_program = text
                        break

            # ESTRATÉGIA C: Busca Textual em Tabelas de Metadados
            # Procura por rótulos como "Programa:", "Curso:"
            if not found_program:
                labels = soup.find_all(string=re.compile(r'(Programa|Curso|Pós-Graduação):', re.I))
                for label in labels:
                    # Tenta pegar o próximo elemento ou o pai
                    container = label.find_parent(['td', 'div', 'p'])
                    if container:
                        # Tenta o próximo irmão (estrutura de tabela ou div)
                        value = container.find_next_sibling()
                        if value:
                            found_program = value.get_text(strip=True)
                            break
                        # Ou o texto dentro do próprio container
                        text = container.get_text(strip=True).replace(label, "")
                        if len(text) > 3:
                            found_program = text
                            break

            # LIMPEZA DO NOME DO PROGRAMA
            if found_program:
                # Remove prefixos comuns para deixar apenas a área (ex: "Direito")
                # Remove "Programa de Pós-Graduação em/no/na"
                clean_name = re.sub(
                    r'(Programa|Curso) de Pós-Graduação (em|no|na)?\s*', 
                    '', 
                    found_program, 
                    flags=re.IGNORECASE
                )
                # Remove "Mestrado/Doutorado em"
                clean_name = re.sub(
                    r'(Mestrado|Doutorado) (Profissional|Acadêmico)?\s*(em|no|na)?\s*', 
                    '', 
                    clean_name, 
                    flags=re.IGNORECASE
                )
                # Remove sufixos de siglas (ex: " - PPGD")
                clean_name = re.sub(r'\s*-\s*[A-Z0-9]+$', '', clean_name)
                
                data['programa'] = clean_name.strip()
                if on_progress: on_progress(f"Genérico: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"Genérico: Erro prog: {str(e)[:20]}")

        # --- 3. EXTRAÇÃO DO PDF ---
        try:
            pdf_url = None
            
            # ESTRATÉGIA A: Meta Tag citation_pdf_url (Padrão Google Scholar) - A mais confiável
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # ESTRATÉGIA B: Links com extensão .pdf
            if not pdf_url:
                # Procura qualquer link que termine em .pdf (ignorando case)
                pdf_link = soup.find('a', href=re.compile(r'\.pdf$', re.I))
                if pdf_link:
                    pdf_url = pdf_link['href']

            # ESTRATÉGIA C: Padrões de URL do DSpace (bitstream, download)
            if not pdf_url:
                # Procura links que contenham 'bitstream' E ('original' OU 'sequence=1' OU 'isAllowed=y')
                # Evita thumbnails (.jpg)
                bitstream_link = soup.find('a', href=re.compile(r'bitstream|download|arquivo', re.I))
                if bitstream_link:
                    href = bitstream_link['href']
                    if not href.endswith('.jpg') and not href.endswith('.txt'):
                        pdf_url = href

            # ESTRATÉGIA D: Texto do Link
            if not pdf_url:
                text_link = soup.find('a', string=re.compile(r'^Visualizar/Abrir|^Download|^Texto completo', re.I))
                if text_link:
                    pdf_url = text_link.get('href')

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("Genérico: PDF localizado.")
            else:
                if on_progress: on_progress("Genérico: PDF não encontrado.")

        except Exception as e:
            if on_progress: on_progress(f"Genérico: Erro PDF: {str(e)[:20]}")

        return data