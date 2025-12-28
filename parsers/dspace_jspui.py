import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class DSpaceJSPUIParser(BaseParser):
    """
    Parser genérico para repositórios DSpace interface JSPUI (Clássica).
    Suporta extração via:
    1. Tabela de Metadados (IDs específicos ou Labels como 'Programa')
    2. Linha 'Aparece nas Coleções'
    3. Breadcrumbs (Trilha de navegação)
    """
    def extract_pure_soup(self, html_content, url, on_progress=None):
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress(f"{self.sigla}: Analisando (JSPUI)...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        # Tenta encontrar o programa usando a estratégia definida na classe filha ou a padrão
        raw_program = self._find_program(soup)
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

    def _find_program(self, soup):
        """Tenta localizar o nome do programa em vários locais comuns."""
        return (self._try_metadata_table_id(soup) or 
                self._try_metadata_table_label(soup) or 
                self._try_collections_row(soup) or 
                self._try_breadcrumbs(soup))

    def _try_metadata_table_id(self, soup):
        """Estratégia: IDs específicos de tabela (ex: UNIOESTE)."""
        # Ex: <td id="label.dc.publisher.program">
        row = soup.find('td', id='label.dc.publisher.program')
        if row:
            val = row.find_next_sibling('td', class_='metadataFieldValue')
            if val: return val.get_text(strip=True)
        return None

    def _try_metadata_table_label(self, soup):
        """Estratégia: Labels de texto na tabela (ex: 'Programa:')."""
        labels = [r'Programa', r'Pós-Graduação']
        for lbl in labels:
            tag = soup.find('td', class_='metadataFieldLabel', string=re.compile(lbl, re.IGNORECASE))
            if tag:
                val = tag.find_next_sibling('td', class_='metadataFieldValue')
                if val: return val.get_text(strip=True)
        return None

    def _try_collections_row(self, soup):
        """Estratégia: Linha 'Aparece nas coleções' (ex: UFMS, UTFPR)."""
        labels = ["Aparece nas coleções", "Appears in Collections", "Coleções"]
        for txt in labels:
            tag = soup.find('td', class_='metadataFieldLabel', string=re.compile(txt, re.IGNORECASE))
            if tag:
                val = tag.find_next_sibling('td', class_='metadataFieldValue')
                if val:
                    # Prioriza links que pareçam ser de programas
                    for link in val.find_all('a'):
                        t = link.get_text(strip=True)
                        if any(x in t for x in ["Programa", "Mestrado", "Doutorado"]):
                            return t
                    return val.get_text(strip=True)
        return None

    def _try_breadcrumbs(self, soup):
        """Estratégia: Breadcrumbs (ex: UFRRJ, UFN, UFOP)."""
        crumbs = soup.select('ol.breadcrumb li, ul.breadcrumb li')
        # Itera do fim para o começo para achar o nível mais específico
        for crumb in reversed(crumbs):
            t = crumb.get_text(strip=True)
            # Ignora o item ativo (geralmente o título da tese)
            if 'active' in crumb.get('class', []): continue
            
            if any(x in t for x in ["Programa", "Mestrado", "Doutorado"]):
                return t
        return None

    def _clean_program_name(self, raw):
        """Limpeza padrão de prefixos e sufixos."""
        # Remove prefixos de campus (ex: "PB - " da UTFPR)
        name = re.sub(r'^[A-Z]{2,4}\s*-\s*', '', raw)
        
        # Remove "Programa de Pós-Graduação em", "Mestrado em", etc.
        name = re.sub(
            r'^(?:Programa de |)(?:Pós-Graduação(?: Interdisciplinar)?|Mestrado|Doutorado)(?:\s+(?:Profissional|Acadêmico))?(?: em| no| na)?\s*', 
            '', 
            name, 
            flags=re.IGNORECASE
        )
        
        # Remove siglas entre parênteses no final (ex: "(PPGTE)")
        name = re.sub(r'\s*\([A-Z0-9-]+\)$', '', name)
        
        return name.strip('.,- ')

    def _find_pdf(self, soup, base_url):
        """Busca PDF em meta tags ou links de bitstream."""
        # 1. Meta Tag (Padrão Google Scholar)
        meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
        if meta: return meta.get('content')
        
        # 2. Link na tabela de arquivos
        # Procura href que tenha 'bitstream' E termine em '.pdf'
        link = soup.find('a', href=lambda h: h and ('/bitstream/' in h or 'bitstream' in h) and h.lower().endswith('.pdf'))
        if link:
            # Resolve URL relativa se necessário
            return urljoin(base_url, link['href'])
            
        return '-'