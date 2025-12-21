import re
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from trata_ies import *

def configurar_driver():
    edge_options = Options()
    edge_options.add_argument("--headless=new")
    edge_options.add_argument("--disable-gpu")
    edge_options.add_argument("--no-sandbox")
    edge_options.add_argument('--ignore-certificate-errors')
    edge_options.add_argument('--ignore-ssl-errors')
    edge_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    return webdriver.Edge(options=edge_options)

def aguardar_carregamento(driver, wait, url_l):
    if "unisinos.br" in url_l:
        try:
            wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "meta[name*='dc.'], ds-item-page-fields, .ds-div-head")
            ))
            time.sleep(2) 
        except: pass
    elif any(ies in url_l for ies in ["unifor.br", "sophia.com.br", "ufop.br"]):
        time.sleep(5) 
    else:
        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        except: pass


def extrair_resumo(soup):
    # Tenta metadados
    meta_res = (soup.find('meta', attrs={'name': 'dc.description.abstract', 'xml:lang': 'pt_BR'}) or 
                soup.find('meta', attrs={'name': 'dc.description.abstract'}) or 
                soup.find('meta', attrs={'name': 'description'}))
    
    resumo = meta_res.get('content', '') if meta_res else ""
    
    # Fallback Visual
    if len(resumo) < 50:
        tag_vis = soup.find(['div', 'td'], class_=re.compile(r'DocumentoTextoResumo|abstract|description', re.I))
        if tag_vis: resumo = tag_vis.get_text(separator=' ', strip=True)
    
    return re.sub(r'\s+', ' ', resumo).strip() or "Resumo não disponível."

def extrair_pdf(soup, url_detalhe):
    # Lógica de metadados
    meta_pdf = soup.find('meta', attrs={'name': re.compile(r'citation_pdf_url|dc.identifier.uri', re.I)})
    if meta_pdf and meta_pdf.get('content') and ".pdf" in meta_pdf.get('content').lower():
        return meta_pdf.get('content')

    # Lógica de links (Fallback)
    pdf_link = soup.find('a', href=re.compile(r'bitstream|Tese_Original\.pdf|download|view|\.pdf', re.I))
    if pdf_link:
        href = pdf_link.get('href').split('?')[0]
        if not href.startswith('http'):
            base = "/".join(url_detalhe.split("/")[:3])
            return base + (href if href.startswith('/') else '/' + href)
        return href
    return "Link do PDF não encontrado"


def ler_detalhes_trabalho(url_detalhe):
    driver = configurar_driver()
    wait = WebDriverWait(driver, 25)
    url_l = url_detalhe.lower()
    
    try:
        driver.get(url_detalhe)
        aguardar_carregamento(driver, wait, url_l)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # 1. IES e Programa (usando suas funções do trata_ies.py)
        uni = identificar_ies(url_l) # Criar esta pequena lógica
        prog = obter_programa_limpo(soup, uni, driver.page_source) # Criar esta
        
        # 2. Resumo e PDF (novas funções atômicas)
        resumo = extrair_resumo(soup)
        link_pdf = extrair_pdf(soup, url_detalhe)
        
        # 3. Classificação
        is_juridico = "direito" in prog.lower() or "direito" in resumo.lower()[:200]
        
        return {
            "resumo": resumo,
            "universidade": uni,
            "programa": prog,
            "classificacao": "Jurídico" if is_juridico else "Não Jurídico",
            "link_pdf": link_pdf
        }
    except Exception as e:
        return {"resumo": f"Erro: {e}", "universidade": "Erro", "programa": "Erro", "classificacao": "N/A", "link_pdf": "N/A"}
    finally:
        driver.quit()
        
def extrair_numero_paginas(soup):
    """Extrai o número da última página do elemento aria-label."""
    botao = soup.find('a', attrs={'aria-label': 'Ir para a última página'})
    if botao:
        texto = botao.get_text(strip=True)
        numero = re.sub(r'\D', '', texto)
        return int(numero)
    return 1

def extrair_dados_da_pagina_atual(soup):
    """Extrai os trabalhos presentes no HTML atual."""
    trabalhos_detalhados = []
    blocos_trabalhos = soup.find_all('div', class_='result-body')    
    for bloco in blocos_trabalhos:
        try:
            titulo_tag = bloco.find('a', class_='title')
            titulo = titulo_tag.get_text(separator=' ', strip=True) if titulo_tag else "Sem título"
            titulo = re.sub(r'\s+', ' ', titulo)

            link_tag = bloco.find('a', class_='fulltext')
            link = link_tag['href'] if link_tag else "N/A"
            if link != "N/A" and not link.startswith('http'):
                link = f"https://bdtd.ibict.br{link}"

            autor_tag = bloco.find_all('a')[1]
            autor = autor_tag.get_text(strip=True)

            trabalhos_detalhados.append({"Título": titulo, "Autor": autor, "Link": link})
        except: continue
    return trabalhos_detalhados

def realizar_busca_recursiva(url_base, callback_status):
    """Navega por todas as páginas de uma busca específica."""
    edge_options = Options()
    edge_options.add_argument("--headless=new")
    edge_options.add_argument("--disable-gpu")
    edge_options.add_argument("--log-level=3")
    edge_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    driver = webdriver.Edge(options=edge_options)
    todos_os_trabalhos_da_url = []
    
    try:
        # 1. Acessa a primeira página para descobrir o total
        driver.get(url_base)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "result-body")))
        
        soup_inicial = BeautifulSoup(driver.page_source, 'html.parser')
        total_paginas = extrair_numero_paginas(soup_inicial)
        
        # 2. Loop de paginação
        for p in range(1, total_paginas + 1):
            callback_status(f"Lendo página {p} de {total_paginas}...")
            
            # Se não for a primeira página, navegamos para a próxima
            if p > 1:
                # Ajusta a URL para a página correspondente
                if "page=" in url_base:
                    url_paginada = re.sub(r'page=\d+', f'page={p}', url_base)
                else:
                    url_paginada = f"{url_base}&page={p}"
                
                driver.get(url_paginada)
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "result-body")))
                soup_atual = BeautifulSoup(driver.page_source, 'html.parser')
            else:
                soup_atual = soup_inicial

            # Extrai e acumula
            dados = extrair_dados_da_pagina_atual(soup_atual)
            todos_os_trabalhos_da_url.extend(dados)
            
        return todos_os_trabalhos_da_url
    finally:
        driver.quit()