from bs4 import BeautifulSoup
from selenium import webdriver
import re
import requests
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from urllib.parse import urljoin

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

            # Captura o Título e o Link da página de metadados
            titulo_tag = bloco.find('a', class_='title')
            titulo = titulo_tag.get_text(strip=True) if titulo_tag else "Sem título"
            
            # O link da página de detalhes é essencial para o scraper de PDF funcionar depois
            href = titulo_tag['href'] if titulo_tag else "N/A"
            link = f"https://bdtd.ibict.br{href}" if href != "N/A" and not href.startswith('http') else href

            # Captura o Autor (Geralmente o segundo link no bloco)
            # Usamos o re.sub para limpar o "Por " que você mencionou antes
            autor_tag = bloco.find_all('a')[1]
            autor_raw = autor_tag.get_text(strip=True) if autor_tag else "N/A"
            autor = re.sub(r'^(Por|Autor)[:\s]*', '', autor_raw, flags=re.IGNORECASE).strip()

            trabalhos_detalhados.append({
                "Título": titulo, 
                "Autor": autor, 
                "Link": link
            })
        except Exception:
            continue
    return trabalhos_detalhados

def realizar_busca_recursiva(url_inicial, config, meta_dados, callback_status):   
    todos_resultados = []
    pagina_atual = 1
    total_paginas = 1

    while pagina_atual <= total_paginas:
        # Monta URL: alguns sites usam 'page=2', outros 'from=21' (offset)
        ajuste_pag = pagina_atual if config['param_pagina'] == "page" else (pagina_atual - 1) * 20
        url_com_pagina = f"{url_inicial}&{config['param_pagina']}={ajuste_pag}"
        
        callback_status(f"Coletando página {pagina_atual} de {total_paginas}...")
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.get(url_com_pagina, headers=headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Na primeira página, descobre o limite de navegação
            if pagina_atual == 1:
                total_paginas = _extrair_limite_paginacao(soup, config)

            # Chama a extração de dados da vitrine, que lida com os links específicos
            itens_pagina = _extrair_dados_vitrine(soup, config, meta_dados)
            todos_resultados.extend(itens_pagina)

            pagina_atual += 1
            time.sleep(1.5) 

        except Exception as e:
            callback_status(f"Erro na página {pagina_atual}: {e}")
            break

    return todos_resultados

def _extrair_limite_paginacao(soup, config):
    """Extrai o número da última página usando o seletor genérico."""
    try:
        links = soup.select(".pagination li a")
        numeros = [int(re.sub(r'\D', '', s.get_text())) for s in links if re.sub(r'\D', '', s.get_text()).isdigit()]
        return max(numeros) if numeros else 1
    except:
        return 1

def _extrair_dados_vitrine(soup, config, meta_dados):
    resultados = []
    blocos = soup.find_all('div', class_='result-body')
    for bloco in blocos:
        try:
            titulo_tag = bloco.find('a', class_='title')
            autor_tag = bloco.find('div', class_='author')
            # O link da universidade está na div 'link' com classe 'fulltext'
            link_uni_tag = bloco.find('a', class_='fulltext')

            if not titulo_tag: continue

            # Link do BDTD (para detalhes)
            href_bdtd = titulo_tag['href']
            link_bdtd = urljoin("https://bdtd.ibict.br", href_bdtd)

            # Link da Universidade (Alvo solicitado)
            link_universidade = link_uni_tag['href'] if link_uni_tag else "N/A"

            autor_raw = autor_tag.get_text(strip=True) if autor_tag else "N/A"
            autor = re.sub(r'^(Por|Autor)[:\s]*', '', autor_raw, flags=re.IGNORECASE).strip()

            resultados.append({
                'titulo': titulo_tag.get_text(" ", strip=True),
                'autor': autor,
                'link': link_bdtd,
                'link_universidade': link_universidade, # Novo campo
                'ano': meta_dados['ano'],
                'termo': meta_dados['termo'],
                'agregador': meta_dados['agregador']
            })
        except Exception:
            continue
    return resultados

    def ler_detalhes_trabalho(url_uni, callback_status):
        """Navega para a universidade e extrai dados específicos."""
        callback_status("🚀 A abrir navegador (Edge)...")
        options = Options()
        options.add_argument("--headless=new")
        driver = webdriver.Edge(options=options)
        
        try:
            callback_status(f"🌐 A aceder: {url_uni[:30]}...")
            driver.get(url_uni)
            time.sleep(4) # Tempo para carregar scripts do repositório
            
            callback_status("🔍 A extrair metadados da universidade...")
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Exemplo de extração (deve ser adaptado por universidade)
            resumo = soup.find('meta', attrs={'name': 'DC.description'})
            resumo = resumo.get('content') if resumo else "Resumo não encontrado"
            
            # Retorne o dicionário com os campos solicitados
            return {
                "resumo": resumo,
                "universidade": "Identificada via Link", # Pode extrair via soup
                "programa": "Pós-Graduação Exemplo",
                "classificacao": "Jurídica" if "direito" in url_uni.lower() else "Não Jurídica",
                "link_pdf": url_uni
            }
        finally:
            driver.quit()
    edge_options = Options()
    edge_options.add_argument("--headless=new")
    driver = webdriver.Edge(options=edge_options)
    
    try:
        callback_progresso("Acessando repositório da universidade...")
        driver.get(url_uni)
        time.sleep(3)
        
        callback_progresso("Analisando estrutura da página...")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Identifica e executa o scrap específico
        if "unisinos.br" in url_uni:
            res = _scrap_unisinos(soup)
        else:
            res = _scrap_generico(soup) # Implementar lógica básica para outros
        
        return res
    finally:
        driver.quit()
        
def coletar_dados_por_agregador(url, fonte, meta_dados, callback_status):
    """Direciona a execução para o código de raspagem específico de cada agregador."""
    
    if "BDTD" in fonte:
        return _raspar_bdtd(url, meta_dados, callback_status)
    
    elif "SciELO" in fonte:
        return _raspar_scielo(url, meta_dados, callback_status)
    
    elif "Google Scholar" in fonte:
        return
        # return _raspar_google_scholar(url, meta_dados, callback_status)
    
    else:
        raise ValueError(f"Agregador '{fonte}' não possui um código de raspagem implementado.")
   
# --- CÓDIGOS ESPECÍFICOS ---

def _raspar_bdtd(url, meta_dados, callback):
    """Executa a busca recursiva em todas as páginas do BDTD."""
    todos_resultados = []
    pagina_atual = 1
    total_paginas = 1

    while pagina_atual <= total_paginas:
        callback(f"Lendo página {pagina_atual} de {total_paginas}...")
        
        # O BDTD usa o parâmetro &page= para navegação
        url_com_pagina = f"{url}&page={pagina_atual}"
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(url_com_pagina, headers=headers, timeout=15)
            soup = BeautifulSoup(res.text, 'html.parser')

            # Na primeira página, identifica qual é a última página disponível
            if pagina_atual == 1:
                total_paginas = _extrair_limite_paginacao(soup, None)

            # Extrai os dados da página atual (incluindo link_universidade)
            itens = _extrair_dados_vitrine(soup, None, meta_dados)
            todos_resultados.extend(itens)
            
            pagina_atual += 1
            time.sleep(1) # Delay para evitar bloqueio do servidor
        except Exception as e:
            callback(f"Erro na página {pagina_atual}: {e}")
            break

    return todos_resultados

def _buscar_link_original_no_bdtd(url_detalhe_bdtd):
    """Navega no BDTD para achar o botão 'Visualizar no registro original'."""
    try:
        res = requests.get(url_detalhe_bdtd, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        # No BDTD, o link para a universidade geralmente está em um botão ou metadado específico
        tag_link = soup.find('a', string=re.compile("Ver registro original|Acesso online", re.I))
        return tag_link['href'] if tag_link else None
    except:
        return None

def _raspar_scielo(url, meta_dados, callback):
    """Lógica específica para SciELO com paginação por offset 'from'."""
    # SciELO geralmente exige tratamento de cookies ou headers específicos
    callback("Processando SciELO...")
    # ... (seu código específico para SciELO)
    return []

def scrap_universidade_especifico_mestre(url_uni):
    """Navega até a universidade e decide qual scraper usar."""
    edge_options = Options()
    edge_options.add_argument("--headless=new")
    driver = webdriver.Edge(options=edge_options)
    
    try:
        driver.get(url_uni)
        time.sleep(4) # Espera carregamento de scripts do repositório
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Lógica de decisão baseada na URL
        if "unisinos.br" in url_uni:
            return _scrap_unisinos(soup)
        elif "usp.br" in url_uni:
            # return _scrap_usp(soup)
            pass
        
        # Se não for uma conhecida, usa o genérico
        return _scrap_generico_repo(soup, url_uni)
        
    finally:
        driver.quit()

def _task_scrap_detalhado(self, link, id_db):
    try:
        def atualizar_status(texto):
            self.root.after(0, lambda: self.view.lbl_status.config(text=texto, fg="orange"))

        # Executa o scrap passando a função de progresso
        res = leitor_de_paginas.ler_detalhes_trabalho(link, atualizar_status)
       
        # Salva usando o ID único do banco
        database.salvar_detalhes_completos_por_id(
            id_db, res['resumo'], res['programa'], 
            res['universidade'], res['classificacao'], res['link_pdf']
        )
        
        # Formata exibição final
        info_painel = f"UNI: {res['universidade']}\nPROG: {res['programa']}\n\nRESUMO: {res['resumo']}"
        
        self.root.after(0, self.carregar_do_banco)
        self.root.after(0, lambda: self.view.exibir_resumo(info_painel))
        self.root.after(0, lambda: self.view.lbl_status.config(text="✅ Detalhes atualizados!", fg="green"))
        
    except Exception as e:
        self.root.after(0, lambda: self.view.lbl_status.config(text=f"❌ Erro: {str(e)}", fg="red"))

def _scrap_generico_repo(soup, url):
    """Tenta extrair dados de repositórios DSpace/OJS comuns."""
    # Exemplo simples de extração genérica
    resumo = "Não encontrado"
    resumo_tag = soup.find('meta', attrs={'name': 'DC.description'}) or soup.find('div', class_='abstract')
    if resumo_tag:
        resumo = resumo_tag.get('content') if resumo_tag.name == 'meta' else resumo_tag.get_text(strip=True)

    programa = "Não identificado"
    prog_tag = soup.find('meta', attrs={'name': 'DC.publisher'})
    if prog_tag:
        programa = prog_tag.get('content')

    return {
        "resumo": resumo,
        "universidade": "Verificar manual",
        "programa": programa,
        "classificacao": "Jurídico" if "direito" in programa.lower() else "Não Jurídico",
        "link_pdf": url
    }

def scrap_universidade_especifico(url_uni, soup):
    """
    Identifica a universidade pela URL ou conteúdo e executa a rotina correta.
    """
    if "unisinos.br" in url_uni or "jesuita.org.br" in url_uni:
        return _scrap_unisinos(soup)
    elif "usp.br" in url_uni:
        return _scrap_usp(url_uni)
    # ... outras condições
    else:
        return _scrap_generico(url_uni)

def _scrap_unisinos(soup):
    """
    Extrai dados específicos do repositório Unisinos (DSpace).
    Captura Sigla, Nome, Programa, Classificação e Link do PDF.
    """
    # 1. Extração do Nome e Sigla da Universidade
    # O DSpace costuma colocar o nome em meta tags DC.publisher
    publisher_tags = soup.find_all('meta', attrs={'name': 'DC.publisher'})
    nome_completo = "Universidade do Vale do Rio dos Sinos" # Fallback
    for tag in publisher_tags:
        content = tag.get('content', '')
        if "Universidade" in content:
            nome_completo = content
            break
            
    # Extração da Sigla (geralmente 'Unisinos')
    sigla_tag = soup.find('meta', attrs={'name': 'DC.publisher', 'content': 'Unisinos'})
    sigla = sigla_tag.get('content') if sigla_tag else "UNISINOS"

    # 2. Extração do Programa de Pós-Graduação
    # Na Unisinos, este dado está em uma meta tag DC.publisher específica
    # ou na trilha de navegação (breadcrumb)
    programa = "Não identificado"
    breadcrumb_links = soup.select('#ds-trail li.ds-trail-link a')
    # Geralmente o último link antes de 'Ver item' é o PPG
    if len(breadcrumb_links) >= 1:
        programa = breadcrumb_links[-1].get_text(strip=True)
    
    # Alternativa via meta tag (mais precisa se disponível)
    prog_meta = soup.find('meta', attrs={'name': 'DC.publisher', 'xml:lang': 'pt_BR'})
    # Verifica se o conteúdo parece um programa (ex: contém 'Programa de Pós-Graduação')
    for tag in publisher_tags:
        if "Programa" in tag.get('content', ''):
            programa = tag.get('content')

    # 3. Classificação Jurídica/Não Jurídica
    # Lógica: Verifica se 'Direito' está no nome do programa ou na trilha
    classificacao = "Não Jurídica"
    if "direito" in programa.lower() or any("direito" in l.get_text().lower() for l in breadcrumb_links):
        classificacao = "Jurídica"

    # 4. Link Direto para o PDF
    # No DSpace 4.1, o link está na meta tag 'citation_pdf_url'
    pdf_tag = soup.find('meta', attrs={'name': 'citation_pdf_url'})
    link_pdf = pdf_tag.get('content') if pdf_tag else "N/A"

    return {
        "sigla": sigla,
        "universidade": nome_completo,
        "programa": programa,
        "classificacao": classificacao,
        "link_pdf": link_pdf
    }

def _scrap_usp(url):
    """Lógica customizada para a estrutura do repositório da USP."""
    # O código aqui usaria seletores específicos da USP (ex: id="documentTitle")
    return {"autor": "...", "titulo": "...", "link_pdf": "..."}

def _scrap_ufrj(url):
    """Lógica customizada para a estrutura da UFRJ (geralmente DSpace)."""
    # O código aqui usaria seletores do DSpace (ex: .ds-div-head)
    return {"autor": "...", "titulo": "...", "link_pdf": "..."}

def _scrap_generico(url):
    return

