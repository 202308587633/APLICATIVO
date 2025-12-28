import re
from urllib.parse import urljoin
from parsers.dspace_jspui import DSpaceJSPUIParser

class UniforParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UNIFOR", universidade="Universidade de Fortaleza")

    def _find_program(self, soup):
        """
        Estratégia específica para UNIFOR (Sistema Sophia).
        O programa é listado como um 'autor' ou 'colaborador' com o nome da instituição.
        Ex: <a title="Universidade de Fortaleza. Programa de Pós-Graduação em Direito Constitucional">
        """
        # Busca por links que contenham "Programa de Pós-Graduação" no texto ou no título
        # O sistema Sophia coloca isso dentro de divs com class="box-duplo"
        
        # 1. Tenta pelo atributo title (comum no exemplo fornecido)
        link_title = soup.find('a', title=re.compile(r'Programa de Pós-Graduação', re.IGNORECASE))
        if link_title:
            return link_title['title']

        # 2. Tenta pelo texto do link
        link_text = soup.find('a', string=re.compile(r'Programa de Pós-Graduação', re.IGNORECASE))
        if link_text:
            return link_text.get_text(strip=True)

        # 3. Fallback para a implementação padrão
        return super()._find_program(soup)

    def _clean_program_name(self, raw):
        """
        Limpeza para UNIFOR.
        Entrada esperada: "Universidade de Fortaleza. Programa de Pós-Graduação em Direito Constitucional"
        Saída desejada: "Direito Constitucional"
        """
        # Remove o nome da universidade e pontuação
        clean = re.sub(r'^Universidade de Fortaleza[\.\s-]*', '', raw, flags=re.IGNORECASE)
        
        # Remove o prefixo do programa
        clean = re.sub(r'Programa de Pós-Graduação (?:em|no|na)\s+', '', clean, flags=re.IGNORECASE)
        
        return super()._clean_program_name(clean)

    def _find_pdf(self, soup, base_url):
        """
        No sistema Sophia, o link para o recurso muitas vezes não está nas meta tags padrão de PDF,
        mas sim numa seção de links externos (class='sites').
        """
        # Estratégia Sophia: Procurar na div/p com classe 'sites'
        sites_container = soup.find(class_='sites')
        if sites_container:
            link = sites_container.find('a', href=True)
            if link:
                return urljoin(base_url, link['href'])

        # Fallback para meta tags padrão (citation_pdf_url) se existirem
        return super()._find_pdf(soup, base_url)