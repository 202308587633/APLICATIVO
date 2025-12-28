import re
from bs4 import BeautifulSoup
from parsers.dspace_angular import DSpaceAngularParser

class IFROParser(DSpaceAngularParser):
    def __init__(self):
        # A sigla é IFRO, mas a instituição pode variar (ex: parceiras). 
        # Mantemos o padrão, mas o parser pode detectar 'Must University' se desejado.
        super().__init__(sigla="IFRO", universidade="Instituto Federal de Educação, Ciência e Tecnologia de Rondônia")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório do IFRO (DSpace 7+ / Angular).
        Corrige a extração de programa para focar na Descrição/Citação e não no Campus.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 1. Executa a extração padrão da classe pai
        data = super().extract_pure_soup(html_content, url, on_progress)

        # 2. Refinamento do Programa:
        # Se o programa extraído for o Campus (ex: "Campus Cacoal") ou genérico, tenta melhorar.
        program_candidate = data.get('programa', '')
        
        # Lista de termos que indicam que pegamos o local errado (Campus) ou tipo de doc
        termos_evitar = ['campus', 'cacoal', 'porto velho', 'ji-paraná', 'vilhena', 'ariquemes', 'dissertação', 'tese']
        
        if any(t in program_candidate.lower() for t in termos_evitar) or len(program_candidate) < 3:
            if on_progress: on_progress("IFRO: Refinando nome do programa pela descrição...")
            
            # Tenta extrair especificamente da Descrição ou Citação
            new_program = self._find_program_in_description(soup)
            if new_program:
                data['programa'] = new_program

        return data

    def _find_program_in_description(self, soup):
        """
        Busca o programa dentro de frases como:
        'Dissertação de Mestrado em Direito Internacional...'
        Presentes em dc.description ou dc.identifier.citation
        """
        # Regex alvo: Pega o que vem depois de "Mestrado em" ou "Doutorado em"
        # até a próxima pontuação ou palavra chave "pela"
        regex_prog = r'(?:Mestrado|Doutorado)(?: Profissional)? em\s+([^,.\-]+?)(?:\s+pela|\s*[,\.]|$)'
        
        # 1. Tenta Meta Tags (Prioridade)
        # O IFRO usa 'dc.description' para descrever o título obtido
        tags_to_check = ['dc.description', 'dcterms.abstract', 'dc.identifier.citation']
        
        for tag_name in tags_to_check:
            meta = soup.find('meta', attrs={'name': tag_name})
            if meta:
                content = meta.get('content', '')
                match = re.search(regex_prog, content, re.IGNORECASE)
                if match:
                    return match.group(1).strip()

        # 2. Tenta Visualmente (Campos 'Descrição' ou 'Citação')
        try:
            # Procura cabeçalhos de metadados visuais
            headers = soup.find_all(lambda tag: tag.name in ['h2', 'h3', 'h5'] and 'simple-view-element-header' in (tag.get('class') or []))
            
            for header in headers:
                if 'descrição' in header.get_text(strip=True).lower():
                    # Pega o container pai e busca o corpo
                    container = header.find_parent('div', class_='simple-view-element')
                    if container:
                        body = container.find('div', class_='simple-view-element-body')
                        if body:
                            text = body.get_text(" ", strip=True)
                            match = re.search(regex_prog, text, re.IGNORECASE)
                            if match:
                                return match.group(1).strip()
        except Exception:
            pass

        return None

    def _clean_program_name(self, raw):
        """Limpeza final."""
        if not raw: return "-"
        # Remove prefixos remanescentes
        clean = re.sub(r'^(?:Programa de Pós-Graduação em|Mestrado em|Doutorado em)\s+', '', raw, flags=re.IGNORECASE)
        return clean.strip()