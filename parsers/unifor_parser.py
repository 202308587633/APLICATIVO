import re
from urllib.parse import urljoin
from parsers.dspace_jspui import DSpaceJSPUIParser

class UniforParser(DSpaceJSPUIParser):
    def __init__(self):
        super().__init__(sigla="UNIFOR", universidade="Universidade de Fortaleza")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Sobrescreve o método mestre para garantir a integridade dos dados institucionais.
        O sistema Sophia muitas vezes não retorna metadados claros sobre a instituição.
        """
        # Executa a extração padrão
        data = super().extract_pure_soup(html_content, url, on_progress)

        # FORÇA os dados institucionais corretos, ignorando o que foi (ou não) achado no HTML
        data['sigla'] = self.sigla
        data['universidade'] = self.universidade

        return data

    def _find_program(self, soup):
        """
        Estratégia Híbrida: Sophia Biblioteca Web e DSpace.
        No Sophia, o programa aparece listado como um 'autor' institucional.
        """
        # --- ESTRATÉGIA 1: Sophia Biblioteca Web (Prioritária) ---
        # Procura em blocos <div class="box-duplo" itemprop="author">
        author_boxes = soup.find_all('div', class_='box-duplo')
        for box in author_boxes:
            link = box.find('a')
            if not link:
                continue

            # O texto geralmente é: "Universidade de Fortaleza. Programa de Pós-Graduação em..."
            text = link.get_text(strip=True)
            
            # Validação: Deve conter "Programa" e "Pós-Graduação"
            if "Programa" in text and "Pós-Graduação" in text:
                return text

        # --- ESTRATÉGIA 2: DSpace (Legado) ---
        return super()._find_program(soup)

    def _clean_program_name(self, raw):
        """
        Limpeza específica para transformar:
        "Universidade de Fortaleza. Programa de Pós-Graduação em Informática Aplicada"
        em
        "Informática Aplicada"
        """
        # 1. Remove o nome da universidade e pontuação inicial
        # Ex: "Universidade de Fortaleza. " -> ""
        clean = re.sub(r'^Universidade de Fortaleza[.\s-]*', '', raw, flags=re.IGNORECASE)
        
        # 2. Remove o prefixo do programa
        # Ex: "Programa de Pós-Graduação em " -> ""
        clean = re.sub(r'Programa de Pós-Graduação (?:em|no|na)\s+', '', clean, flags=re.IGNORECASE)

        # 3. Limpeza para o sistema legado (DSpace), caso encontre "Centro de ... - Curso"
        if " - " in clean and ("Centro" in clean or "Escola" in clean):
            clean = clean.split(" - ")[-1]

        # 4. Chama a limpeza padrão (remove espaços extras, pontuação final, etc)
        return super()._clean_program_name(clean)

    def _find_pdf(self, soup, base_url):
        """
        Localiza o PDF no sistema Sophia ou DSpace.
        """
        # --- ESTRATÉGIA SOPHIA ---
        # O link costuma estar em: <p class="sites"><span><a href="...">
        sites_p = soup.find('p', class_='sites')
        if sites_p:
            link = sites_p.find('a', href=True)
            if link:
                return urljoin(base_url, link['href'])
        
        # Tenta achar link direto para o visualizador do Sophia
        sophia_view = soup.find('a', href=lambda x: x and 'auth-sophia/exibicao' in x)
        if sophia_view:
            return urljoin(base_url, sophia_view['href'])

        # --- ESTRATÉGIA DSPACE ---
        return super()._find_pdf(soup, base_url)