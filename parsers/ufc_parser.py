import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UFCParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UFC", universidade="Universidade Federal do Ceará")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UFC (DSpace 6.3).
        Lógica específica para identificar 'Direito' via sigla FADIR.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UFC: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia 1: Análise das Coleções (Solicitado: FADIR -> Direito)
            # Procura pela linha da tabela: "Aparece nas coleções:"
            # <td class="metadataFieldLabel">Aparece nas coleções:</td><td class="metadataFieldValue">...</td>
            collection_labels = soup.find_all('td', class_='metadataFieldLabel')
            
            for label in collection_labels:
                if "Aparece nas coleções" in label.get_text():
                    value_td = label.find_next_sibling('td', class_='metadataFieldValue')
                    if value_td:
                        coll_text = value_td.get_text(strip=True)
                        
                        # Regras específicas solicitadas (Siglas -> Nome do Programa)
                        if "FADIR" in coll_text:
                            found_program = "Direito"
                            break
                        elif "POLEDUC" in coll_text:
                            found_program = "Políticas Públicas e Gestão da Educação"
                            break                        
                        # Outros programas na UFC geralmente seguem o padrão "Programa de Pós-Graduação em X"
                        if "Programa de Pós-Graduação" in coll_text:
                            match = re.search(r'Programa de Pós-Graduação\s*(em|no|na)?\s*([^-]+)', coll_text, re.IGNORECASE)
                            if match:
                                found_program = match.group(2).strip()
                                break

            # Estratégia 2: Citação Bibliográfica (Fallback robusto)
            # <meta name="DCTERMS.bibliographicCitation" content="... Programa de Pós-Graduação em Direito ...">
            if not found_program:
                citation_meta = soup.find('meta', attrs={'name': 'DCTERMS.bibliographicCitation'})
                if citation_meta:
                    content = citation_meta.get('content', '')
                    # Tenta extrair o nome do programa da citação
                    match = re.search(r'Programa de Pós-Graduação\s*(em|no|na)?\s*([^,]+)', content, re.IGNORECASE)
                    if match:
                        found_program = match.group(2).strip()

            if found_program:
                data['programa'] = found_program
                if on_progress: on_progress(f"UFC: Programa identificado: {found_program}")

        except Exception as e:
            if on_progress: on_progress(f"UFC: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UFC: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Presente no HTML fornecido)
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link "Visualizar/Abrir" na tabela de arquivos
            if not pdf_url:
                # Procura links dentro da tabela 'panel-body' que terminem em pdf
                link_tag = soup.find('a', href=lambda h: h and 'bitstream' in h and h.lower().endswith('.pdf'))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UFC: PDF localizado.")
            else:
                if on_progress: on_progress("UFC: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UFC: Erro PDF: {str(e)[:20]}")

        return data