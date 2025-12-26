import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class UNIVATESParser(BaseParser):
    def __init__(self):
        super().__init__(sigla="UNIVATES", universidade="Universidade do Vale do Taquari")

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da UNIVATES (DSpace 7/Angular).
        Foca nos breadcrumbs e na seção 'Coleções' para o Programa, e meta tags para o PDF.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'sigla': self.sigla,
            'universidade': self.universidade,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("UNIVATES: Analisando estrutura da página...")

        # --- 1. EXTRAÇÃO DO PROGRAMA ---
        try:
            found_program = None
            
            # Estratégia 1: Breadcrumbs (Baseado no exemplo fornecido)
            # Estrutura: Início > ... > Mestrado > Ensino > Título
            # A lógica é pegar o item que vem IMEDIATAMENTE DEPOIS de "Mestrado" ou "Doutorado"
            crumbs = soup.select('ol.breadcrumb li')
            
            for i, li in enumerate(crumbs):
                text = li.get_text(strip=True)
                
                # Se achou o nível do grau, o próximo item costuma ser o Programa
                if "Mestrado" in text or "Doutorado" in text:
                    # Verifica se existe um próximo item na lista
                    if i + 1 < len(crumbs):
                        next_li = crumbs[i+1]
                        # Garante que não é o próprio título do trabalho (que geralmente é 'active')
                        if 'active' not in next_li.get('class', []):
                            found_program = next_li.get_text(strip=True)
                            break

            # Estratégia 2: Seção "Coleções" (Metadados DSpace 7)
            # <div class="simple-view-element"><h5>Coleções</h5>...<a ...>Ensino</a>...</div>
            if not found_program:
                headers = soup.find_all('h5', class_='simple-view-element-header')
                for header in headers:
                    if "Coleções" in header.get_text(strip=True):
                        body = header.find_next_sibling('div', class_='simple-view-element-body')
                        if body:
                            # Pega o texto do primeiro link dentro do corpo
                            link_coll = body.find('a')
                            if link_coll:
                                found_program = link_coll.get_text(strip=True)
                                break

            if found_program:
                # Limpeza: remove "Programa de Pós-Graduação em" se houver, embora no exemplo seja apenas "Ensino"
                clean_name = re.sub(
                    r'^Programa de Pós-Graduação\s*(em|no|na)?\s*', 
                    '', 
                    found_program, 
                    flags=re.IGNORECASE
                )
                data['programa'] = clean_name.strip()
                if on_progress: on_progress(f"UNIVATES: Programa identificado: {data['programa']}")

        except Exception as e:
            if on_progress: on_progress(f"UNIVATES: Erro ao extrair programa: {str(e)[:20]}")

        # --- 2. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("UNIVATES: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Presente no HTML fornecido)
            # <meta name="citation_pdf_url" content="...">
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Link na seção "Arquivos"
            if not pdf_url:
                # Procura links que contenham '/bitstreams/' e '/download'
                # Exemplo: href="/bdu/bitstreams/8f6c67d4.../download"
                link_tag = soup.find('a', href=lambda h: h and '/bitstreams/' in h and '/download' in h)
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta (o HTML tem <base href="/bdu/">, então cuidado com URLs relativas)
                if not pdf_url.startswith('http'):
                    # Se a URL baseada na meta tag falhar, ou se pegou do link relativo
                    # Constrói com o domínio base da UNIVATES
                    base_domain = "https://www.univates.br"
                    if pdf_url.startswith('/'):
                        pdf_url = base_domain + pdf_url
                    elif pdf_url.startswith('bdu/'):
                        pdf_url = base_domain + '/' + pdf_url
                    else:
                        pdf_url = urljoin(url, pdf_url)

                data['link_pdf'] = pdf_url
                if on_progress: on_progress("UNIVATES: PDF localizado.")
            else:
                if on_progress: on_progress("UNIVATES: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"UNIVATES: Erro PDF: {str(e)[:20]}")

        return data