import re
from parsers.dspace_jspui import DSpaceJSPUIParser

class UepbParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UEPB", universidade="Universidade Estadual da Paraíba")

    def _find_program(self, soup):
        """
        Estratégia específica para UEPB.
        Prioriza o campo de metadados explícito 'dc.publisher.program' e links com classe 'authority program'.
        """
        # 1. Busca por link com classe específica "authority program"
        # Ex: <a class="authority program" ...>Programa de Pós-Graduação...</a>
        prog_link = soup.find('a', class_='authority program')
        if prog_link:
            return prog_link.get_text(strip=True)

        # 2. Busca pelo ID específico do label na tabela de metadados
        # Ex: <td id="label.dc.publisher.program" ...>Programa:</td>
        label_td = soup.find('td', id='label.dc.publisher.program')
        if label_td:
            value_td = label_td.find_next_sibling('td', class_='metadataFieldValue')
            if value_td:
                return value_td.get_text(strip=True)

        # 3. Fallback: Estratégias padrão da classe pai (Breadcrumbs, etc.)
        return super()._find_program(soup)

    def _clean_program_name(self, raw):
        """
        Limpeza específica para remover sufixos de sigla (comuns na UEPB)
        antes da limpeza padrão.
        """
        # Ex entrada: "Programa de Pós-Graduação em Ensino de Ciências e Educação Matemática - PPGECEM"
        
        # Remove o sufixo da sigla (tudo após o último " - ")
        if " - " in raw:
            raw = raw.rsplit(" - ", 1)[0]
        
        # Resultado intermédio: "Programa de Pós-Graduação em Ensino de Ciências e Educação Matemática"
        
        # Chama a limpeza padrão (que remove "Programa de Pós-Graduação em", etc.)
        return super()._clean_program_name(raw)