import re
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from trata_ies import extrair_unisinos, extrair_ufop, extrair_unb, extrair_generico_dspace

def ler_detalhes_trabalho(url_detalhe):
    edge_options = Options()
    edge_options.add_argument("--headless=new")
    edge_options.add_argument("--disable-gpu")
    edge_options.add_argument("--no-sandbox")
    edge_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    driver = webdriver.Edge(options=edge_options)
    wait = WebDriverWait(driver, 20)
    
    try:
        driver.get(url_detalhe)
        
        # --- ESPERA INTELIGENTE MULTI-SISTEMA ---
        try:
            # Espera até que QUALQUER um desses elementos apareça:
            # .simple-item-view-description (DSpace clássico/Unisinos)
            # ds-item-page (UFOP/DSpace Angular)
            # .dc_description_ppg (UnB)
            wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, "ds-item-page, .simple-item-view-description, .dc_description_ppg, #ds-content"
            )))
        except:
            # Se nenhum aparecer em 20s, espera um pouco mais por segurança
            time.sleep(3) 

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # 1. Identificar Universidade e extrair programa
        if "ufop.br" in url_detalhe:
            uni = "UFOP"
            # Pequeno fôlego extra para o Angular renderizar os textos internos
            time.sleep(2) 
            # Re-processa o soup para garantir que pegamos o HTML final renderizado
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            prog = extrair_ufop(soup)
        elif "unisinos.br" in url_detalhe or "jesuita.org.br" in url_detalhe:
            uni = "UNISINOS"
            prog = extrair_unisinos(soup)
        elif "unb.br" in url_detalhe:
            uni = "UnB"
            prog = extrair_unb(soup)
        else:
            uni = "Outra"
            prog = extrair_generico_dspace(soup)

        # 2. Limpeza e Classificação
        prog_limpo = re.sub(r'^\d+[A-Z0-9]*\s+', '', prog)
        # Classificação baseada no PPG
        classificacao = "Jurídico" if "direito" in prog_limpo.lower() else "Não Jurídico"

        # 3. Extração do Resumo (A Unisinos usa classes 'simple-item-view-description')
        resumo = "Resumo não disponível."
        # Procura em meta tags primeiro (mais estável)
        meta_resumo = soup.find('meta', attrs={'name': 'DC.description', 'xml:lang': 'pt_BR'}) or \
                      soup.find('meta', attrs={'name': 'DCTERMS.abstract'})
        
        if meta_resumo:
            resumo = meta_resumo.get('content', resumo)
        else:
            # Fallback visual
            resumo_tag = soup.find('div', class_='simple-item-view-description')
            if resumo_tag:
                resumo = resumo_tag.get_text(strip=True).replace("Resumo:", "").strip()

        return {
            "resumo": resumo,
            "universidade": uni,
            "programa": prog_limpo,
            "classificacao": classificacao
        }
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

def ler_detalhes_trabalho(url_detalhe):
    edge_options = Options()
    edge_options.add_argument("--headless=new")
    driver = webdriver.Edge(options=edge_options)

    try:
        driver.get(url_detalhe)
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # 1. Identificar Universidade
        universidade = "UFPR" if "ufpr.br" in url_detalhe else "Outra/IBICT"
       
        # 2. Extrair o Programa (Estratégia específica para UFPR vs Geral)
        programa_encontrado = "Não Identificado"
        
        if universidade == "UFPR":
            # Busca a lista de breadcrumb que você informou
            breadcrumb = soup.find('ul', class_='breadcrumb')
            if breadcrumb:
                # Pegamos todos os itens da lista
                itens = breadcrumb.find_all('li')
                # No DSpace da UFPR, o programa geralmente é o 3º item (índice 2)
                # ou o antepenúltimo antes de "Ver item"
                if len(itens) >= 3:
                    # Tentamos o índice 2, mas validamos se não é um dos termos genéricos
                    texto_candidato = itens[2].get_text(strip=True)
                    if "Página inicial" not in texto_candidato and "BIBLIOTECA" not in texto_candidato:
                        programa_encontrado = texto_candidato
                    elif len(itens) >= 4:
                        programa_encontrado = itens[3].get_text(strip=True)
        
        # Se não for UFPR ou se a busca anterior falhou, usa a busca genérica por rótulos
        if programa_encontrado == "Não Identificado":
            rotulos_alvo = ["Programa", "Unidade", "Departamento", "Curso", "Publisher"]
            for rotulo in rotulos_alvo:
                celula_rotulo = soup.find(['th', 'td', 'dt'], string=re.compile(rotulo, re.I))
                if celula_rotulo:
                    valor = celula_rotulo.find_next(['td', 'dd'])
                    if valor:
                        programa_encontrado = valor.get_text(strip=True)
                        break

        # 3. Classificação Jurídica
        # Removemos códigos numéricos que às vezes aparecem no início (ex: 40001016071P8)
        # para a classificação não se confundir
        nome_limpo = re.sub(r'^\d+[A-Z0-9]*\s+', '', programa_encontrado)
        
        if "direito" in nome_limpo.lower():
            classificacao = "Jurídico"
        else:
            classificacao = "Não Jurídico"

        # 4. Extrair Resumo
        resumo_tag = soup.find('div', class_='abstract') or \
                     soup.find('div', class_='simple-item-view-description') or \
                     soup.find('div', class_='item-view-field-value')
        resumo = resumo_tag.get_text(strip=True) if resumo_tag else "Resumo não disponível."

        return {
            "resumo": resumo,
            "universidade": universidade,
            "programa": nome_limpo, # Retornamos o nome sem o código Capes
            "classificacao": classificacao
        }
    finally:
        driver.quit()