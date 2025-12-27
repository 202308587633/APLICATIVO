import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from parsers.base_parser import BaseParser

class FGVParser(BaseParser):
    def __init__(self):
        # Configura o nome padrão (Geralmente Direito SP, mas será verificado dinamicamente)
        super().__init__(
            sigla="FGV", 
            universidade="Escola de Direito de São Paulo da Fundação Getulio Vargas"
        )

    def extract_pure_soup(self, html_content, url, on_progress=None):
        """
        Extrai dados do repositório da FGV (DSpace 7/Angular).
        Verifica contexto EBAPE (RJ) vs Direito (SP).
        Foca nas meta tags para o PDF e nos breadcrumbs para o Programa.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # --- 1. VERIFICAÇÃO DE CONTEXTO (EBAPE vs PADRÃO) ---
        # Define os valores iniciais com base no padrão da classe
        sigla_atual = self.sigla
        universidade_atual = self.universidade
        
        # Verifica se a sigla EBAPE está presente no texto da página
        # Isso cobre breadcrumbs, títulos, rodapés ou metadados visíveis
        if "EBAPE" in soup.get_text().upper():
            sigla_atual = "FGV-RJ"
            universidade_atual = "Escola Brasileira de Administração Pública e de Empresas da Fundação Getúlio Vargas"
            if on_progress: on_progress("FGV: Contexto EBAPE identificado. Ajustando dados da universidade.")

        data = {
            'sigla': sigla_atual,
            'universidade': universidade_atual,
            'programa': '-',
            'link_pdf': '-'
        }

        if on_progress: on_progress("FGV: Analisando estrutura da página...")

        # --- 2. EXTRAÇÃO DO PROGRAMA (Via Breadcrumb) ---
        try:
            found_program = None
            
            # O HTML mostra: <ol class="breadcrumb"> ... <li> ... <a ...>Texto</a>
            # Texto exemplo: "FGV DIREITO SP - Dissertações, Mestrado Profissional em Direito"
            crumbs = soup.select('ol.breadcrumb li a')
            
            for crumb in crumbs:
                text = crumb.get_text(strip=True)
                
                # Verifica palavras-chave comuns em hierarquias de repositório
                if "Mestrado" in text or "Doutorado" in text or "Programa de" in text:
                    # Limpeza específica para o padrão da FGV
                    match = re.search(r'(Mestrado|Doutorado|Programa).*?\s+(em|no|na)\s+(.*)', text, re.IGNORECASE)
                    
                    if match:
                        found_program = match.group(3).strip() # Pega o que vem depois do "em"
                    elif "Direito" in text:
                        # Fallback simples
                        found_program = "Direito"
                    else:
                        found_program = text.strip()
                    
                    break

            if found_program:
                data['programa'] = found_program
                if on_progress: on_progress(f"FGV: Programa identificado: {found_program}")

        except Exception as e:
            if on_progress: on_progress(f"FGV: Erro ao extrair programa: {str(e)[:20]}")

        # --- 3. EXTRAÇÃO DO PDF ---
        try:
            if on_progress: on_progress("FGV: Buscando arquivo PDF...")
            
            pdf_url = None
            
            # Estratégia A: Meta Tag citation_pdf_url (Padrão)
            pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
            if pdf_meta:
                pdf_url = pdf_meta.get('content')
            
            # Estratégia B: Busca Específica na Seção "Arquivos" (Baseado no HTML fornecido)
            # Estrutura: h5 "Arquivos" -> div body -> div file-section -> a href
            if not pdf_url:
                # Procura todos os cabeçalhos h5 que possam ser o título da seção
                headers = soup.find_all('h5', class_='simple-view-element-header')
                for header in headers:
                    if 'Arquivos' in header.get_text():
                        # Encontra o corpo da seção logo após o cabeçalho
                        body = header.find_next_sibling('div', class_='simple-view-element-body')
                        if body:
                            # Busca o primeiro link válido dentro dessa seção
                            link_tag = body.find('a', href=True)
                            if link_tag:
                                pdf_url = link_tag['href']
                                break

            # Estratégia C: Link Genérico (Fallback)
            if not pdf_url:
                link_tag = soup.find('a', href=lambda h: h and ('/bitstreams/' in h or 'request-a-copy' in h))
                if link_tag:
                    pdf_url = link_tag['href']

            if pdf_url:
                # Garante URL absoluta
                data['link_pdf'] = urljoin(url, pdf_url)
                if on_progress: on_progress("FGV: PDF localizado.")
            else:
                if on_progress: on_progress("FGV: PDF não encontrado diretamente.")

        except Exception as e:
            if on_progress: on_progress(f"FGV: Erro PDF: {str(e)[:20]}")

        return data
    
    