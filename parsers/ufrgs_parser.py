import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UFRGSParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UFRGS", universidade="Universidade Federal do Rio Grande do Sul")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UFRGS (Lume - DSpace 5.8 / Mirage2).
        Foca na seção 'Instituição' e em links de Coleção para identificar o Programa.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UFRGS: Analisando estrutura da página (Lume)...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia 1: Busca na seção "Instituição" (Específico do Lume)
            # <div class="simple-view-authors ..."><h5>Instituição</h5><div>...</div></div>
            inst_divs = soup.find_all('div', class_='simple-item-view-authors')
            for div in inst_divs:
                h5 = div.find('h5')
                if h5 and "Instituição" in h5.get_text():
                    value_div = div.find('div')
                    if value_div:
                        text = value_div.get_text(strip=True)
                        # O texto geralmente é: "Universidade ... Faculdade ... Programa de Pós-Graduação em Direito."
                        if "Programa de Pós-Graduação" in text:
                            match = re.search(r'Programa de Pós-Graduação\s*(?:em|no|na)?\s+(.*?)[\.$]', text, re.IGNORECASE)
                            if match:
                                found_program = match.group(1).strip().rstrip('.')
                            else:
                                # Tenta pegar a última parte se não casar o regex
                                parts = text.split('.')
                                if len(parts) > 1:
                                    # Pega a parte que contém "Programa" e limpa
                                    for part in parts:
                                        if "Programa" in part:
                                            found_program = part.replace("Programa de Pós-Graduação em", "").strip()
                                            break

            # Estratégia 2: Busca na lista de Coleções (Fallback padrão DSpace)
            # <div class="itemCommunityOthersCollections"><a ...>Direito</a></div>
            if not found_program:
                coll_divs = soup.find_all('div', class_='itemCommunityOthersCollections')
                # Às vezes a coleção específica está numa div irmã ou dentro
                # No exemplo: <div style="margin-left: 30px;"><a ...>Direito</a> (870)</div>
                if not coll_divs:
                     # Procura links dentro da lista de coleções
                     collection_list = soup.find('ul', class_='ds-referenceSet-list')
                     if collection_list:
                         links = collection_list.find_all('a')
                         for link in links:
                             text = link.get_text(strip=True)
                             # Ignora coleções muito genéricas se houver outras
                             if text not in ["Teses e Dissertações", "Ciências Sociais Aplicadas"]:
                                 found_program = text
                                 # Geralmente o último link é o mais específico (o programa)
            
            if found_program:
                # Limpeza final
                clean_name = re.sub(
                    r'^(?:Programa de Pós-Graduação|Mestrado|Doutorado|Curso)(?:\s+(?:Profissional|Acadêmico))?(?: em| no| na)?\s*', 
                    '', 
                    found_program, 
                    flags=re.IGNORECASE
                )
                data['programa'] = clean_name.strip()
                if on_progress: on_progress(f"UFRGS: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"UFRGS: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UFRGS: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Padrão e presente no HTML)
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link na seção "Visualizar/abrir"
            if not pdf_url:
                # Procura links que contenham '/bitstream/' e terminem em .pdf
                link_tag = soup.find('a', href=lambda h: h and '/bitstream/' in h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UFRGS: PDF localizado.")
            else:
                if on_progress: on_progress("UFRGS: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UFRGS: Erro PDF: {str(e)[:20]}")

        return data
    
    