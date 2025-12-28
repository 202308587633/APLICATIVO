import re
from urllib.parse import urljoin
from parsers.dspace_jspui import DSpaceJSPUIParser

class UeaParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UEA", universidade="Universidade do Estado do Amazonas")

    def _find_program(self, soup):
        """
        Estratégia específica para UEA (DSpace 8 / Angular).
        Prioriza a seção de 'Coleções' e Breadcrumbs.
        """
        # 1. Estratégia Prioritária: Seção de Coleções (Snippet fornecido)
        # Ex: <div class="collections"><a ...><span>Mestrado em Direito ambiental</span></a></div>
        collections_div = soup.find('div', class_='collections')
        if collections_div:
            # Pega o texto do link dentro da div
            link = collections_div.find('a')
            if link:
                return link.get_text(strip=True)
            return collections_div.get_text(strip=True)

        # 2. Estratégia Breadcrumbs (Fallback para DSpace 7/8)
        # Ex: Início > ... > Mestrado em Direito ambiental > ...
        crumbs = soup.select('ol.breadcrumb li')
        for crumb in crumbs:
            text = crumb.get_text(strip=True)
            # Ignora itens genéricos de navegação
            if text in ["Início", "Comunidades e Coleções"] or "Escolas de Ensino" in text:
                continue
            
            # Se encontrar indícios de programa, retorna
            if any(term in text for term in ["Mestrado", "Doutorado", "Programa"]):
                return text

        # 3. Fallback: Estratégias padrão da classe pai
        return super()._find_program(soup)

    def _clean_program_name(self, raw):
        """
        Limpeza específica para remover prefixos de titulação comuns na UEA.
        Ex: "Mestrado em Direito ambiental" -> "Direito Ambiental"
        """
        # Remove "Mestrado em", "Doutorado em", "Mestrado Profissional em"
        clean = re.sub(
            r'^(?:Mestrado|Doutorado)(?:\s+Profissional)?\s+(?:em|no|na)\s+', 
            '', 
            raw, 
            flags=re.IGNORECASE
        )
        
        # Chama a limpeza padrão (que remove "Programa de Pós-Graduação", etc.)
        return super()._clean_program_name(clean)

    def _find_pdf(self, soup, base_url):
        """
        Sobrescreve busca de PDF para suportar links de download do DSpace 8.
        Ex: .../bitstreams/{uuid}/download
        """
        # 1. Tenta encontrar links com padrão '/bitstreams/' e '/download'
        dl_link = soup.find('a', href=lambda h: h and '/bitstreams/' in h and '/download' in h)
        if dl_link:
            return urljoin(base_url, dl_link['href'])

        # 2. Fallback: Estratégias padrão (Meta tag citation_pdf_url, etc.)
        return super()._find_pdf(soup, base_url)