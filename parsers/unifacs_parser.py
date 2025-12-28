import re
from bs4 import BeautifulSoup
from parsers.dspace_angular import DSpaceAngularParser

class UNIFACSParser(DSpaceAngularParser):
    def __init__(self):
        # Inicializa com valores genéricos, pois o 'Deposita' é compartilhado
        super().__init__(sigla="UNIFACS", universidade="Universidade Salvador")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório Deposita (IBICT).
        Corrige o problema de identificar o tipo de documento (Dissertação) como Programa.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 1. Executa a extração padrão
        data = super().extract_pure_soup(html_content, url, on_progress)

        # 2. Correção de Programa:
        # Se o programa extraído for genérico (ex: "Dissertação", "Tese", "Trabalho de Conclusão"),
        # forçamos uma nova busca mais profunda na citação.
        termos_genericos = ['dissertação', 'tese', 'masterthesis', 'doctoralthesis', 'trabalho de conclusão']
        
        programa_atual = str(data.get('programa', '')).lower()
        if any(t in programa_atual for t in termos_genericos) or data['programa'] in ['-', '']:
            if on_progress: on_progress("UNIFACS: Programa genérico detectado. Buscando na citação...")
            
            programa_citacao = self._find_program_in_citation(soup)
            if programa_citacao:
                data['programa'] = programa_citacao

        # 3. Atualização Dinâmica da Instituição (para diferenciar UNIFACS de outras no mesmo repo)
        publisher_meta = soup.find('meta', attrs={'name': 'citation_publisher'})
        if publisher_meta:
            nome_inst = publisher_meta.get('content', '').strip()
            data['universidade'] = nome_inst
            
            if "Universidade Salvador" in nome_inst:
                data['sigla'] = "UNIFACS"
            else:
                # Tenta criar uma sigla baseada nas maiúsculas (Ex: "Universidade de Brasília" -> UB)
                data['sigla'] = ''.join([c for c in nome_inst if c.isupper() and c.isalpha()])

        return data

    def _find_program_in_citation(self, soup):
        """
        Busca específica no texto da citação bibliográfica.
        Padrão alvo: "Dissertação (Nome do Programa) - Instituição"
        """
        try:
            # Procura pelo cabeçalho visual "Citação" (comum no DSpace 7/Angular)
            # Pode ser um h2, h3 ou h5 dependendo do tema
            citation_header = soup.find(lambda tag: tag.name in ['h2', 'h3', 'h5'] and 'Citação' in tag.get_text())
            
            citation_text = ""
            
            # Se achou o cabeçalho visual, pega o texto do container
            if citation_header:
                container = citation_header.find_parent('div', class_='simple-view-element')
                if container:
                    body = container.find('div', class_='simple-view-element-body')
                    if body:
                        citation_text = body.get_text(" ", strip=True)

            # Fallback: Tenta pegar da meta tag se o visual falhar
            if not citation_text:
                meta_cit = soup.find('meta', attrs={'name': 'DCTERMS.bibliographicCitation'})
                if meta_cit:
                    citation_text = meta_cit.get('content', '')

            if citation_text:
                # REGEX APRIMORADO:
                # Procura por: "Dissertação" ou "Tese", seguido de espaço opcional,
                # seguido de parênteses com o conteúdo (O PROGRAMA),
                # seguido de " - " (hífen).
                # Ex: "Dissertação (Desenvolvimento Regional e Urbano) - UNIFACS"
                match = re.search(r'(?:Dissertação|Tese)\s*\(([^)]+)\)\s*-\s*', citation_text, re.IGNORECASE)
                
                if match:
                    return match.group(1).strip()
                
                # Tentativa secundária: Se não tiver o "Dissertação" antes, tenta pegar o que está entre parênteses antes do traço da instituição
                # Ex: "... [2023]. (Desenvolvimento Regional e Urbano) - UNIFACS..."
                match_gen = re.search(r'\(([^)]+)\)\s*-\s*(?:UNIFACS|Universidade|Faculdade)', citation_text, re.IGNORECASE)
                if match_gen:
                    return match_gen.group(1).strip()

        except Exception:
            pass
            
        return None

    def _clean_program_name(self, raw):
        """Limpeza final do nome."""
        if not raw: return "-"
        # Remove prefixos comuns de titulação
        clean = re.sub(r'^(?:Mestrado|Doutorado)(?: Profissional)? em\s+', '', raw, flags=re.IGNORECASE)
        return super()._clean_program_name(clean)