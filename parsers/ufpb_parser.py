import re
from parsers.dspace_jspui import DSpaceJSPUIParser

class UfpbParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UFPB", universidade="Universidade Federal da Paraíba")

    def _find_program(self, soup):
        """
        Estratégia específica para UFPB (DSpace JSPUI).
        Prioriza labels explícitos e faz parsing textual da coleção para lidar com hierarquias.
        """
        # 1. Tenta label explícito "Programa:" na tabela (Padrão)
        prog = self._try_metadata_table_label(soup)
        if prog:
            return prog

        # 2. Estratégia específica para "Aparece nas coleções" da UFPB
        # Muitas vezes o texto é algo como: "Centro de Ciências Jurídicas (CCJ) - Programa de Pós-Graduação em..."
        label_td = soup.find('td', class_='metadataFieldLabel', string=re.compile(r'Aparece nas coleções', re.I))
        if label_td:
            value_td = label_td.find_next_sibling('td', class_='metadataFieldValue')
            if value_td:
                text = value_td.get_text(strip=True)
                
                # Caso A: Contém "Programa de Pós-Graduação"
                if "Programa de Pós-Graduação" in text:
                    # Captura tudo após "Programa de Pós-Graduação [em/no/na]"
                    match = re.search(r'Programa de Pós-Graduação\s*(?:em|no|na)?\s+(.*)', text, re.IGNORECASE)
                    if match:
                        return match.group(1).strip()
                
                # Caso B: Hierarquia separada por hífen " - "
                parts = text.split(' - ')
                if len(parts) > 1:
                    # Retorna a última parte (geralmente é o programa)
                    return parts[-1].strip()
                
                # Caso C: Retorna o texto inteiro se não conseguiu quebrar
                return text

        return None

    # Nota: Não é necessário sobrescrever _find_pdf, pois a implementação 
    # da classe pai (DSpaceJSPUIParser) já cobre citation_pdf_url e links bitstream.