import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UFRNParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UFRN", universidade="Universidade Federal do Rio Grande do Norte")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UFRN (DSpace 7+ / Angular).
        
        Estratégia de Extração:
        - Programa: Localizado na tabela de metadados, na linha 'Coleções'.
          O parser tenta limpar o nome (ex: de 'PPGDIR - Mestrado em Direito' para 'Direito').
        - PDF: Prioriza a meta tag 'citation_pdf_url'.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UFRN: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        # Busca baseada no fragmento: <th>Coleções</th><td><a ...>PPGDIR - Mestrado em Direito</a></td>
        try:
            found_program = None
            
            # Procura pelo cabeçalho (TH) que contém "Coleções"
            collections_th = soup.find('th', string=re.compile(r'Coleções', re.I))
            
            if collections_th:
                # O valor (TD) geralmente é o irmão adjacente ao TH na estrutura de tabela padrão do DSpace
                collections_td = collections_th.find_next_sibling('td')
                
                if collections_td:
                    # Busca o link dentro do TD
                    program_link = collections_td.find('a')
                    if program_link:
                        raw_text = program_link.get_text(strip=True)
                        # Exemplo esperado: "PPGDIR - Mestrado em Direito"
                        
                        # Lógica de limpeza para extrair apenas "Direito"
                        # 1. Separa pelo hífen
                        parts = raw_text.split('-')
                        if len(parts) > 1:
                            # Pega a parte descritiva (ex: " Mestrado em Direito")
                            candidate = parts[-1].strip()
                            
                            # 2. Tenta remover "Mestrado em" ou "Doutorado em" para isolar o nome do programa
                            clean_match = re.search(r'(?:Mestrado|Doutorado|Pós-Graduação)\s+(?:em|no|na)?\s+(.+)', candidate, re.I)
                            if clean_match:
                                found_program = clean_match.group(1).strip()
                            else:
                                found_program = candidate
                        else:
                            # Se não tiver hífen, usa o texto completo (fallback)
                            found_program = raw_text

            if found_program:
                data['programa'] = found_program
                if on_progress: on_progress(f"UFRN: Programa identificado como '{found_program}'.")
            else:
                if on_progress: on_progress("UFRN: Campo 'Coleções' não encontrado ou vazio.")

        except Exception as e:
            if on_progress: on_progress(f"UFRN: Erro ao extrair programa: {str(e)}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Presente no HTML de exemplo da UFRN)
            # <meta name="citation_pdf_url" content="...">
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Busca genérica por links de bitstream/download (Fallback)
            if not pdf_url:
                # Procura links que contenham 'bitstream' E ('download' OU terminem em .pdf)
                link_tag = soup.find('a', href=lambda h: h and 'bitstreams' in h and ('download' in h or h.lower().endswith('.pdf')))
                if link_tag:
                    pdf_url = link_tag['href']

            # Estratégia C: Botão específico "Baixar" (visto no HTML da UFRN)
            if not pdf_url:
                dl_btn = soup.find('a', class_=lambda c: c and 'btn-primary' in c, string=re.compile(r'Baixar', re.I))
                if dl_btn and dl_btn.get('href'):
                    pdf_url = dl_btn['href']

            if pdf_url:
                # Garante que a URL seja absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("UFRN: PDF localizado com sucesso.")
            else:
                if on_progress: on_progress("UFRN: PDF não localizado.")

        except Exception as e:
            if on_progress: on_progress(f"UFRN: Erro ao extrair PDF: {str(e)}")

        return data