import re
from urllib.parse import urljoin
from parsers.dspace_jspui import DSpaceJSPUIParser

class UfrnParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UFRN", universidade="Universidade Federal do Rio Grande do Norte")

    def _find_program(self, soup):
        """
        Estratégia específica para UFRN (DSpace 7.x/Angular).
        Busca nos Breadcrumbs o item que contém "Programa de Pós-Graduação".
        Ex: Início > BDTD > Programa de Pós-Graduação em Direito > ...
        """
        # 1. Estratégia Breadcrumbs
        crumbs = soup.select('ol.breadcrumb li')
        for crumb in crumbs:
            text = crumb.get_text(strip=True)
            # Verifica se o breadcrumb é explicitamente um Programa de Pós
            if "Programa de Pós-Graduação" in text:
                return text

        # 2. Estratégia Meta Tag (DC.publisher.program) - Comum na UFRN
        program_meta = soup.find('meta', attrs={'name': 'citation_publisher'})
        # Às vezes a UFRN coloca o programa no 'publisher', mas geralmente é a universidade.
        # Vamos verificar se há algum meta específico ou confiar no breadcrumb.
        
        # 3. Fallback: Padrão da classe pai
        return super()._find_program(soup)

    def _clean_program_name(self, raw):
        """
        Limpeza específica para UFRN.
        Transforma "Programa de Pós-Graduação em Direito" em "Direito".
        """
        # Remove "Programa de Pós-Graduação em/no/na"
        clean = re.sub(r'Programa de Pós-Graduação (?:em|no|na)\s+', '', raw, flags=re.IGNORECASE)
        
        # Remove siglas de programas que às vezes aparecem nos breadcrumbs (Ex: "PPGDIR - Mestrado em Direito")
        if " - " in clean:
            # Se tiver hífen, geralmente o nome do curso está na segunda parte ou é o próprio nome limpo
            # Ex: "PPGDIR - Mestrado em Direito" -> "Mestrado em Direito" -> "Direito"
            parts = clean.split(" - ")
            # Pega a parte mais descritiva (geralmente a última ou a que tem "Mestrado/Doutorado")
            candidate = parts[-1]
            if "Mestrado" in candidate or "Doutorado" in candidate:
                clean = candidate
            else:
                # Se não tiver indicativo de grau, assume a limpeza padrão da primeira parte se for sigla
                # Mas no caso da UFRN, o breadcrumb principal é "Programa de Pós...", que já foi limpo acima.
                pass

        # Chama a limpeza padrão (remove "Mestrado em", etc.)
        return super()._clean_program_name(clean)

    def _find_pdf(self, soup, base_url):
        """
        Aprimora busca de PDF para suportar DSpace 7 Angular.
        """
        # 1. Tenta citation_pdf_url (Presente no exemplo)
        pdf = super()._find_pdf(soup, base_url)
        if pdf:
            return pdf

        # 2. Busca links de download explícitos do Angular (bitstreams/.../download)
        dl_link = soup.find('a', href=lambda h: h and '/bitstreams/' in h and '/download' in h)
        if dl_link:
            return urljoin(base_url, dl_link['href'])

        return None