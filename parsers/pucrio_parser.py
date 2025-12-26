import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class PUCRioParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="PUC-Rio", universidade="Pontifícia Universidade Católica do Rio de Janeiro")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório Maxwell da PUC-Rio.
        Foca na estrutura específica de 'colecao_tematicas' para o Programa e no select de arquivos para o PDF.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("PUC-Rio: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia 1: Busca dentro dos detalhes do autor (Div oculta 'colecao_tematicas')
            # <div id="autor_..." class="colecao_tematicas"> ... Programa de Pós-Graduação em Direito ... </div>
            author_divs = soup.find_all('div', class_='colecao_tematicas')
            
            for div in author_divs:
                text = div.get_text(separator=' ', strip=True)
                
                if "Programa de Pós-Graduação" in text:
                    # Regex para capturar o nome do programa
                    match = re.search(r'Programa de Pós-Graduação (em|no|na)?\s*([^-<]+)', text, re.IGNORECASE)
                    if match:
                        found_program = match.group(2).strip()
                        # Limpa sufixos como "PUC-Rio" se vier junto
                        found_program = found_program.replace("PUC-Rio", "").strip()
                        break

            # Estratégia 2: Busca por texto direto (caso o HTML mude)
            if not found_program:
                prog_span = soup.find('span', string=re.compile(r'Programa de Pós-Graduação', re.I))
                if prog_span:
                    text = prog_span.get_text(strip=True)
                    match = re.search(r'Programa de Pós-Graduação (em|no|na)?\s*(.*)', text, re.IGNORECASE)
                    if match:
                        found_program = match.group(2).strip()

            if found_program:
                data['programa'] = found_program
                if on_progress: on_progress(f"PUC-Rio: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"PUC-Rio: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("PUC-Rio: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Select de Arquivos (Específico do Maxwell)
            # <select id="file" ...> <option value="64244.PDF">NA ÍNTEGRA - PDF</option> </select>
            select_file = soup.find('select', id='file')
            if select_file:
                for option in select_file.find_all('option'):
                    val = option.get('value', '')
                    if val.lower().endswith('.pdf'):
                        # A URL base no Maxwell geralmente é https://www.maxwell.vrac.puc-rio.br/NR_SEQ/ARQUIVO
                        # O nrSeq está na URL original ou em inputs hidden, mas aqui vamos tentar construir
                        # Ou pegar de links já formados na página
                        
                        # Tenta achar o link na tabela que corresponde a esse arquivo
                        link_table = soup.find('a', href=re.compile(re.escape(val), re.I))
                        if link_table:
                            pdf_url = link_table['href']
                        else:
                            # Tenta extrair o ID da URL atual para montar o link
                            # Ex: .../colecao.php?strSecao=resultado&nrSeq=64244...
                            match_id = re.search(r'nrSeq=(\d+)', url)
                            if match_id:
                                nr_seq = match_id.group(1)
                                pdf_url = f"https://www.maxwell.vrac.puc-rio.br/{nr_seq}/{val}"
                        break

            # Estratégia B: Link na tabela de descrição
            if not pdf_url:
                # <td><a href="...">NA ÍNTEGRA</a></td> <td>...<a href="...">PDF</a>...</td>
                link_pdf = soup.find('a', href=re.compile(r'\.pdf$', re.I))
                if link_pdf:
                    pdf_url = link_pdf['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin("https://www.maxwell.vrac.puc-rio.br/", pdf_url)
                if on_progress: on_progress("PUC-Rio: PDF localizado.")
            else:
                if on_progress: on_progress("PUC-Rio: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"PUC-Rio: Erro PDF: {str(e)[:20]}")

        return data