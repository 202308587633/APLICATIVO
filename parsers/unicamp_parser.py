import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UNICAMPParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UNICAMP", universidade="Universidade Estadual de Campinas")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UNICAMP (Sophia Biblioteca Web).
        Foca na div 'autoria-sem-funcao' para o Programa e na classe 'pdf-file' para o arquivo.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UNICAMP: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # O sistema Sophia coloca a afiliação institucional em uma div com classe 'autoria-sem-funcao'
            # Exemplo: <div class="box-duplo autoria-sem-funcao" ...> ... <a ...>Universidade ... Programa ...</a> ... </div>
            author_divs = soup.find_all('div', class_='autoria-sem-funcao')
            
            for div in author_divs:
                text = div.get_text(strip=True)
                
                # Procura pela palavra chave "Programa de Pós-Graduação"
                if "Programa de Pós-Graduação" in text:
                    # O texto geralmente vem no formato: 
                    # "Universidade Estadual de Campinas (UNICAMP). Faculdade de Educação. Programa de Pós-Graduação em Educação"
                    
                    # Tenta capturar o que vem depois de "Programa de Pós-Graduação [em/no/na]"
                    match = re.search(r'Programa de Pós-Graduação\s*(?:em|no|na)?\s+(.*)', text, re.IGNORECASE)
                    
                    if match:
                        # Pega o grupo capturado e limpa espaços ou pontos finais
                        raw_prog = match.group(1).strip().strip('.')
                        found_program = raw_prog
                        break
                    else:
                        # Fallback: Se não conseguir limpar pelo regex, pega o texto todo após o último ponto (se houver)
                        parts = text.split('.')
                        if len(parts) > 1:
                            found_program = parts[-1].strip()
                        else:
                            found_program = text

            if found_program:
                data['programa'] = found_program
                if on_progress: on_progress(f"UNICAMP: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"UNICAMP: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UNICAMP: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Classe específica do Sophia 'pdf-file'
            # <a href="/Busca/Download?codigoArquivo=..." class="pdf-file" ...>
            link_pdf_tag = soup.find('a', class_='pdf-file')
            
            if link_pdf_tag and link_pdf_tag.get('href'):
                pdf_url = link_pdf_tag['href']
            
            # Estratégia B: Procura link genérico de download se a classe falhar
            if not pdf_url:
                # Procura links que contenham '/Busca/Download' e a extensão 'pdf' no texto ou href
                link_tag = soup.find('a', href=lambda h: h and '/Busca/Download' in h)
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # O Sophia usa links relativos (ex: /Busca/Download...), precisamos completar com o domínio
                # Nota: A URL original pode ser um handle, então precisamos do domínio base real do repositório
                base_domain = "https://repositorio.unicamp.br" 
                
                if not pdf_url.startswith('http'):
                    # Verifica se a URL passada já é do repositório (não o handle) para usar urljoin
                    if "repositorio.unicamp.br" in url:
                        data['link_pdf'] = urljoin(url, pdf_url)
                    else:
                        # Se estivermos vindo de um handle e o redirect não foi resolvido na string 'url',
                        # forçamos o domínio base conhecido
                        if pdf_url.startswith('/'):
                            data['link_pdf'] = base_domain + pdf_url
                        else:
                            data['link_pdf'] = base_domain + '/' + pdf_url
                else:
                    data['link_pdf'] = pdf_url

                if on_progress: on_progress("UNICAMP: PDF localizado.")
            else:
                if on_progress: on_progress("UNICAMP: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UNICAMP: Erro PDF: {str(e)[:20]}")

        return data
    
    
    