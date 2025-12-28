from parsers.dspace_jspui import DSpaceJSPUIParser

class UfgParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UFG", universidade="Universidade Federal de Goiás")

    def _find_program(self, soup):
        """
        Estratégia de busca de programa específica da UFG (DSpace 7/Bootstrap).
        """
        # 1. Tenta pela div de coleções (Estratégia mais confiável para UFG)
        # Ex: <div class="collections"><a ...><span>Mestrado em Direito...</span></a></div>
        collections_div = soup.find('div', class_='collections')
        if collections_div:
            link_tag = collections_div.find('a')
            if link_tag:
                return link_tag.get_text(strip=True)

        # 2. Tenta pelos Breadcrumbs modernos (Bootstrap class 'breadcrumb-item')
        # Diferente do JSPUI padrão, DSpace 7 costuma usar <li class="breadcrumb-item">
        crumbs = soup.select('ol.breadcrumb li.breadcrumb-item')
        for crumb in reversed(crumbs):
            text = crumb.get_text(strip=True)
            if any(term in text for term in ["Programa", "Mestrado", "Doutorado"]):
                return text

        # 3. Fallback para as estratégias padrão da classe pai (Metadados, etc)
        return super()._find_program(soup)

    def _find_pdf(self, soup, base_url):
        """
        Sobrescreve busca de PDF para adicionar suporte a tags <link> específicas.
        """
        # 1. Tenta o padrão da classe pai (Meta tags citation e links bitstream)
        pdf_link = super()._find_pdf(soup, base_url)
        
        # 2. Se falhar, tenta estratégia extra comum em DSpace mais novos:
        # <link type="application/pdf" href="...">
        if pdf_link == '-':
            link_tag = soup.find('link', attrs={'type': 'application/pdf'})
            if link_tag and link_tag.get('href'):
                return link_tag.get('href')
                
        return pdf_link