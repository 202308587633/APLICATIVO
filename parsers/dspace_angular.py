import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class DSpaceAngularParser(BaseParser):
    """
    Parser genérico para repositórios DSpace interface Angular (versões 7+).
    Suporta extração via:
    1. Breadcrumbs (Trilha de navegação)
    2. Meta Tags (citation_pdf_url)
    3. Links de arquivos na página
    """
    def extract_pure_soup(self, html_content, url, on_progress=None):
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Verifica se há necessidade de ajuste dinâmico da sigla (ex: FGV/EBAPE)
        self._check_dynamic_context(soup, on_progress)

        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress(f"{self.sigla}: Analisando (Angular/DSpace 7+)...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        # Tenta encontrar o programa nos breadcrumbs
        raw_program = self._find_program_in_breadcrumbs(soup)
        
        # Se não achar, tenta fallback para meta tags ou divs específicos
        if not raw_program:
            raw_program = self._find_program_fallback(soup)

        if raw_program:
            data['programa'] = self._clean_program_name(raw_program)
            if on_progress: on_progress(f"{self.sigla}: Programa identificado: {data['programa']}")

        # --- 2. EXTRAÇÃO DO PDF ---
        data['link_pdf'] = self._find_pdf(soup, url)
        if data['link_pdf'] != '-' and on_progress:
            on_progress(f"{self.sigla}: PDF localizado.")
        elif on_progress:
            on_progress(f"{self.sigla}: PDF não encontrado diretamente.")

        return data

    def _check_dynamic_context(self, soup, on_progress):
        """Método hook para parsers que precisam alterar sigla/universidade dinamicamente (ex: FGV)."""
        pass

    def _find_program_in_breadcrumbs(self, soup):
        """Busca o programa na trilha de navegação (breadcrumbs)."""
        # Seleciona itens de lista dentro de ol/ul com classe breadcrumb
        crumbs = soup.select('ol.breadcrumb li, ul.breadcrumb li')
        
        for crumb in reversed(crumbs): # Itera do fim para o começo (mais específico)
            text = crumb.get_text(strip=True)
            
            # Ignora itens genéricos ou o título do item (geralmente 'active')
            if 'active' in crumb.get('class', []): continue
            if text in ["Início", "Home", "Página inicial", "Teses e Dissertações", "Comunidades e Coleções"]: continue
            if "Acervos" in text or "Biblioteca" in text: continue

            # Palavras-chave fortes
            if any(x in text for x in ["Programa", "Mestrado", "Doutorado", "Pós-Graduação"]):
                return text
            
            # Se não tiver palavra-chave, mas for um nível intermediário, pode ser o programa (comum na UCSAL/UNIPAMPA)
            # Retorna o primeiro candidato válido de trás pra frente
            return text
            
        return None

    def _find_program_fallback(self, soup):
        """Estratégias alternativas se breadcrumb falhar."""
        # 1. Meta Tag citation_publisher (alguns usam para o programa)
        # 2. Divs de coleção (simple-item-view-collections)
        return None # Implementado nas classes filhas se necessário

    def _clean_program_name(self, raw):
        """Limpeza padrão de prefixos e sufixos."""
        name = re.sub(
            r'^(?:Programa de |)(?:Pós-Graduação(?: Interdisciplinar)?(?: em)? |)(?:Mestrado|Doutorado)(?:\s+(?:Profissional|Acadêmico))?(?: em| no| na)?\s*', 
            '', 
            raw, 
            flags=re.IGNORECASE
        )
        # Remove códigos de curso no início (ex: "PPGHis - ")
        name = re.sub(r'^[A-Z0-9-]+\s+-\s+', '', name)
        return name.strip('.,- ')

    def _find_pdf(self, soup, base_url):
        """Busca PDF em meta tags ou links de bitstream."""
        # 1. Meta Tag (Padrão Google Scholar)
        meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
        if meta: return meta.get('content')
        
        # 2. Links na página
        # Procura href que tenha 'bitstream' ou 'download' E termine em '.pdf' ou tenha formato de download
        # DSpace 7 muitas vezes usa /download no final
        link = soup.find('a', href=lambda h: h and ('/bitstream/' in h or '/download' in h))
        if link:
            # Verifica se é PDF ou download genérico
            href = link['href']
            if href.lower().endswith('.pdf') or '/download' in href:
                return urljoin(base_url, href)
            
        return '-'
    
