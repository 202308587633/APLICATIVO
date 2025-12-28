import re
from urllib.parse import urljoin
from parsers.dspace_angular import DSpaceAngularParser

class UNIFESPParser(DSpaceAngularParser):
    def __init__(self):
        super().__init__(sigla="UNIFESP", universidade="Universidade Federal de São Paulo")

    def _find_program_fallback(self, soup):
        """
        Sobrescreve o fallback da classe pai para buscar especificamente na Citação,
        conforme o padrão da UNIFESP.
        """
        # Estratégia: Busca pelo cabeçalho "Citação" na visualização simples
        # <div class="simple-view-element"><h2>Citação</h2>...<span>... (Mestrado em Filosofia) ...</span></div>
        try:
            # Procura o H2 com o texto "Citação"
            citation_header = soup.find(lambda tag: tag.name == 'h2' and 'Citação' in tag.get_text())
            
            if citation_header:
                # O conteúdo está na div irmã ou pai próxima
                container = citation_header.find_parent('div', class_='simple-view-element')
                if container:
                    body = container.find('div', class_='simple-view-element-body')
                    if body:
                        text = body.get_text(strip=True)
                        # Regex para capturar: "(Mestrado/Doutorado em NOME)"
                        match = re.search(r'\((?:Mestrado|Doutorado)\s+(?:Profissional\s+)?em\s+([^)]+)\)', text, re.IGNORECASE)
                        if match:
                            return match.group(1).strip()
        except Exception:
            pass
            
        return None

    def _clean_program_name(self, raw):
        """
        Limpeza adicional específica da UNIFESP se vier dos Breadcrumbs.
        Ex: "PPG - Filosofia" -> "Filosofia"
        """
        # Remove o prefixo "PPG - " comum nos breadcrumbs da UNIFESP
        clean = re.sub(r'^PPG\s*-\s*', '', raw, flags=re.IGNORECASE)
        
        # Aplica a limpeza padrão da classe pai (remove "Programa de Pós-Graduação", etc)
        return super()._clean_program_name(clean)

    def _find_pdf(self, soup, base_url):
        """
        Sobrescreve a busca de PDF para corrigir o problema de URL 'localhost'
        presente na meta tag 'citation_pdf_url' da UNIFESP.
        """
        pdf_url = None

        # 1. Tenta pegar da tag <link rel="item"> (Geralmente a URL correta e absoluta em DSpace 7)
        # Ex: <link href="https://repositorio.unifesp.br/..." rel="item">
        link_item = soup.find('link', attrs={'rel': 'item', 'type': 'application/pdf'})
        if link_item and link_item.get('href'):
            pdf_url = link_item.get('href')

        # 2. Se falhar, tenta o botão de download na página
        if not pdf_url:
            # Procura links que contenham '/bitstreams/' e '/download'
            # <a href="/bitstreams/.../download">
            link_tag = soup.find('a', href=lambda h: h and '/bitstreams/' in h and '/download' in h)
            if link_tag:
                pdf_url = link_tag.get('href')

        # 3. Validação final e correção de URL
        if pdf_url:
            # Se a URL contiver localhost, descarta (erro de config do servidor)
            if 'localhost' in pdf_url:
                return None
            
            return urljoin(base_url, pdf_url)

        return None