import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UCBParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UCB", universidade="Universidade Católica de Brasília")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UCB (JSPUI).
        Baseado no exemplo da UFOP, mas ajustado para as tags da UCB.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UCB: Analisando HTML...")

        # --- 1. EXTRAÇÃO DO PROGRAMA (Via Breadcrumb) ---
        try:
            found_program = None
            
            # Seleciona os links dentro da lista de navegação (breadcrumb)
            # Ex: <ol class="breadcrumb btn-success"><li><a>Programa...</a></li></ol>
            crumbs = soup.select('ol.breadcrumb li a')
            
            for crumb in crumbs:
                text = crumb.get_text(strip=True)
                
                # Verifica se é o item que contém o nome do programa
                # Aceita "Programa de Pós-Graduação" e "Programa Stricto Sensu"
                if "Programa" in text and ("Pós-Graduação" in text or "Stricto Sensu" in text):
                    
                    # Regex cirúrgico para limpar o prefixo e as preposições
                    # Transforma "Programa de Pós-Graduação em Direito" -> "Direito"
                    clean_name = re.sub(
                        r'^(Programa de Pós-Graduação|Programa Stricto Sensu)\s*(em|no|na)?\s+', 
                        '', 
                        text, 
                        flags=re.IGNORECASE
                    )
                    found_program = clean_name.strip()
                    break 
            
            if found_program:
                data['programa'] = found_program
                if on_progress: on_progress(f"UCB: Programa identificado: {found_program}")
            else:
                # Fallback: Tenta meta tag se o breadcrumb falhar
                meta_prog = soup.find('meta', attrs={'name': 'DC.publisher'})
                if meta_prog:
                    content = meta_prog.get('content', '')
                    if "Programa" in content:
                         clean_name = re.sub(r'^(Programa.*?)\s*(em|no|na)?\s+', '', content, flags=re.IGNORECASE)
                         data['programa'] = clean_name.strip()

        except Exception as e:
            if on_progress: on_progress(f"UCB: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UCB: Buscando PDF...")
            
            pdf_url = None
            
            # ESTRATÉGIA A (Solicitada): Link com texto "Baixar/Abrir"
            # Varre todos os links procurando esse texto específico
            links = soup.find_all('a', href=True)
            for link in links:
                if "Baixar/Abrir" in link.get_text():
                    pdf_url = link['href']
                    break
            
            # ESTRATÉGIA B: Botão verde (btn-success) que aponta para um bitstream/pdf
            if not pdf_url:
                # Procura links com a classe específica do botão de download da UCB
                btn_link = soup.find('a', class_='btn-success', href=True)
                if btn_link:
                    href = btn_link['href']
                    if 'bitstream' in href or href.lower().endswith('.pdf'):
                        pdf_url = href

            # ESTRATÉGIA C: Meta Tag Padrão (Fallback)
            if not pdf_url:
                meta_pdf = soup.find('meta', attrs={'name': 'citation_pdf_url'})
                if meta_pdf:
                    pdf_url = meta_pdf.get('content')

            if pdf_url:
                # Garante que o link seja absoluto (adiciona https://bdtd.ucb.br...)
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UCB: PDF localizado.")
            else:
                if on_progress: on_progress("UCB: PDF não encontrado.")

        except Exception as e:
            if on_progress: on_progress(f"UCB: Erro PDF: {str(e)[:20]}")

        return data