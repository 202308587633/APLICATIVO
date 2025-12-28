import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UnicampParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UNICAMP", universidade="Universidade Estadual de Campinas")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UNICAMP (Sophia Biblioteca Web).
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UNICAMP: Analisando estrutura (Sophia)...")

        # --- 1. Extração do Programa ---
        found_program = self._find_program(soup)
        if found_program:
            data['programa'] = found_program
            if on_progress: on_progress(f"UNICAMP: Programa identificado: {found_program}")

        # --- 2. Extração do PDF ---
        found_pdf = self._find_pdf(soup, url)
        if found_pdf:
            data['link_pdf'] = found_pdf
            if on_progress: on_progress("UNICAMP: PDF localizado.")
        else:
            if on_progress: on_progress("UNICAMP: PDF não encontrado diretamente.")

        return data

    def _find_program(self, soup):
        """
        Busca o programa na div 'autoria-sem-funcao', padrão do sistema Sophia.
        """
        # Exemplo: <div class="box-duplo autoria-sem-funcao" ...> ... Programa de Pós-Graduação em Educação ... </div>
        author_divs = soup.find_all('div', class_='autoria-sem-funcao')
        
        for div in author_divs:
            text = div.get_text(strip=True)
            
            if "Programa de Pós-Graduação" in text:
                # Tenta capturar o que vem depois de "Programa de Pós-Graduação [em/no/na]"
                match = re.search(r'Programa de Pós-Graduação\s*(?:em|no|na)?\s+(.*)', text, re.IGNORECASE)
                
                if match:
                    # Retorna o grupo capturado limpo de pontos finais
                    return match.group(1).strip().strip('.')
                
                # Fallback: Se não conseguir limpar pelo regex, pega o texto todo após o último ponto
                parts = text.split('.')
                if len(parts) > 1:
                    return parts[-1].strip()
                
                return text # Último recurso: retorna o texto todo

        return None

    def _find_pdf(self, soup, base_url):
        """
        Busca o PDF através da classe 'pdf-file' ou links de download do Sophia.
        Trata a construção da URL absoluta considerando o domínio do repositório.
        """
        pdf_url = None

        # Estratégia A: Classe específica 'pdf-file'
        link_pdf_tag = soup.find('a', class_='pdf-file')
        if link_pdf_tag and link_pdf_tag.get('href'):
            pdf_url = link_pdf_tag['href']

        # Estratégia B: Link genérico de download (/Busca/Download)
        if not pdf_url:
            link_tag = soup.find('a', href=lambda h: h and '/Busca/Download' in h)
            if link_tag:
                pdf_url = link_tag['href']

        if pdf_url:
            return self._fix_sophia_url(base_url, pdf_url)
            
        return None

    def _fix_sophia_url(self, current_url, relative_path):
        """
        Corrige URLs relativas do Sophia.
        Se a URL atual for um handle, força o domínio 'repositorio.unicamp.br'.
        """
        target_domain = "https://repositorio.unicamp.br"
        
        if not relative_path.startswith('http'):
            # Se já estamos no domínio certo, usa urljoin normal
            if "repositorio.unicamp.br" in current_url:
                return urljoin(current_url, relative_path)
            else:
                # Se estamos vindo de um redirecionador (handle), força o domínio base
                if relative_path.startswith('/'):
                    return target_domain + relative_path
                else:
                    return target_domain + '/' + relative_path
        
        return relative_path