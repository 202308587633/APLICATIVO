import re
from parsers.dspace_jspui import DSpaceJSPUIParser

class UfcParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UFC", universidade="Universidade Federal do Ceará")

    def _find_program(self, soup):
        """
        Estratégia específica para UFC.
        Mapeia siglas de coleções (FADIR -> Direito) e verifica citação bibliográfica.
        """
        # 1. Estratégia: Siglas específicas na linha "Aparece nas coleções"
        # A UFC usa siglas internas para definir as coleções, que precisamos traduzir.
        collection_labels = soup.find_all('td', class_='metadataFieldLabel')
        for label in collection_labels:
            if "Aparece nas coleções" in label.get_text():
                value_td = label.find_next_sibling('td', class_='metadataFieldValue')
                if value_td:
                    coll_text = value_td.get_text(strip=True)
                    
                    # Regras de negócio específicas da UFC
                    if "FADIR" in coll_text:
                        return "Direito"
                    elif "POLEDUC" in coll_text:
                        return "Políticas Públicas e Gestão da Educação"
                    
                    # Se não for sigla, tenta extrair o padrão "Programa de Pós-Graduação em X"
                    match = re.search(r'Programa de Pós-Graduação\s*(?:em|no|na)?\s*([^-]+)', coll_text, re.IGNORECASE)
                    if match:
                        return match.group(1).strip()

        # 2. Estratégia: Citação Bibliográfica (DCTERMS.bibliographicCitation)
        # Muito comum na UFC conter o nome completo do programa
        citation_meta = soup.find('meta', attrs={'name': 'DCTERMS.bibliographicCitation'})
        if citation_meta:
            content = citation_meta.get('content', '')
            match = re.search(r'Programa de Pós-Graduação\s*(?:em|no|na)?\s*([^,]+)', content, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # 3. Fallback: Estratégias padrão da classe pai
        return super()._find_program(soup)

    # Nota: A extração de PDF é delegada para a classe pai (DSpaceJSPUIParser),
    # que já suporta citation_pdf_url e links de bitstream.