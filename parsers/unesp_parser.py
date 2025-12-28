import re
from urllib.parse import urljoin
from parsers.dspace_jspui import DSpaceJSPUIParser

class UnespParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UNESP", universidade="Universidade Estadual Paulista")

    def _find_program(self, soup):
        """
        Estratégia híbrida para UNESP (Suporta DSpace 9.x Angular e DSpace JSPUI antigo).
        """
        # --- ESTRATÉGIAS DSPACE 9.x (Angular/Novo Repositório) ---

        # 1. Busca pelo campo explícito "Pós-graduação" (Metadado específico da UNESP)
        # Estrutura: <h2 ...>Pós-graduação</h2> ... <div class="simple-view-element-body">História - FCHS</div>
        headers = soup.find_all('h2', class_='simple-view-element-header')
        for header in headers:
            if "Pós-graduação" in header.get_text(strip=True):
                # O corpo está na div irmã ou próxima dentro do wrapper
                parent = header.find_parent('div', class_='simple-view-element')
                if parent:
                    body = parent.find('div', class_='simple-view-element-body')
                    if body:
                        return body.get_text(strip=True)

        # 2. Busca dentro da Citação (Fallback comum na UNESP)
        # Ex: "... Dissertação (Mestrado em História) - Faculdade ..."
        # Pode estar em <ds-unesp-citation-field> ou genericamente em "Citação"
        citation_div = soup.find('ds-unesp-citation-field')
        if not citation_div:
            # Tenta achar pelo header se o componente específico não for achado
            for header in headers:
                if "Citação" in header.get_text(strip=True):
                    parent = header.find_parent('div', class_='simple-view-element')
                    if parent:
                        citation_div = parent.find('div', class_='simple-view-element-body')
                        break
        
        if citation_div:
            text = citation_div.get_text(strip=True)
            # Regex para capturar: (Mestrado/Doutorado em XXXXX)
            match = re.search(r'\((?:Mestrado|Doutorado)(?:\s+Profissional|\s+Acadêmico)?\s+em\s+([^)]+)\)', text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # --- ESTRATÉGIAS DSPACE JSPUI (Legado) ---

        # 3. Busca pela classe CSS específica antiga
        prog_td = soup.find('td', class_='dc_publisher_program')
        if prog_td:
            return prog_td.get_text(strip=True)

        # 4. Busca por label explícito na tabela antiga
        prog = self._try_metadata_table_label(soup, label_pattern=r'^Programa:?$')
        if prog:
            return prog

        # 5. Fallback: Estratégias padrão da classe pai
        return super()._find_program(soup)

    def _clean_program_name(self, raw):
        """
        Limpeza específica para UNESP.
        """
        # Remove prefixos institucionais "Programa de Pós-Graduação em"
        clean = re.sub(r'Programa de Pós-Graduação (?:em|no|na)\s+', '', raw, flags=re.IGNORECASE)
        
        # Remove sufixos de campus/unidade comuns no novo layout
        # Ex: "História - FCHS" -> "História"
        # Ex: "Educação - Marília" -> "Educação"
        if " - " in clean:
            parts = clean.split(" - ")
            # Geralmente o nome do curso é a primeira parte no novo layout, 
            # mas no antigo as vezes era "Campus - Curso".
            # Heurística: Se a primeira parte for curta e conhecida (História, Educação, Física), é ela.
            # Caso contrário, verifica se a segunda parte parece o curso.
            
            # No novo layout (DSpace 9), parece ser "Nome do Programa - Sigla/Unidade"
            # Vamos assumir a primeira parte como prioritária se não contiver "Campus"
            if "Campus" not in parts[0]:
                clean = parts[0]
            else:
                clean = parts[-1]

        # Limpeza padrão
        return super()._clean_program_name(clean)

    def _find_pdf(self, soup, base_url):
        """
        Aprimora busca de PDF para suportar DSpace 9.x e links relativos.
        """
        # 1. Tenta Meta Tag citation_pdf_url (Geralmente funciona bem no DSpace 9)
        # O HTML fornecido mostra: <meta name="citation_pdf_url" content="...">
        pdf_url = super()._find_pdf(soup, base_url)
        if pdf_url:
            return pdf_url

        # 2. Busca por links de download específicos do Angular/Bootstrap
        # href="/bitstreams/.../download"
        dl_link = soup.find('a', href=lambda h: h and '/bitstreams/' in h and '/download' in h)
        if dl_link:
            return urljoin(base_url, dl_link['href'])

        return None