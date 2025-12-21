from bs4 import BeautifulSoup
from selenium import webdriver
import re
import requests
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

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
        links = soup.select(config['seletor_paginacao'])
        numeros = [int(s.get_text()) for s in links if s.get_text().isdigit()]
        return max(numeros) if numeros else 1
    except:
        return 1

def _extrair_dados_vitrine(soup, config, meta_dados):
    resultados = []
    for item in soup.select(config['seletor_itens']):
        try:
            o_titulo = item.select_one(config['seletor_titulo'])
            o_autor = item.select_one(config['seletor_autor'])
            
            if not o_titulo or not o_autor:
                continue

            # 1. Tratamento agnóstico do link
            href = o_titulo['href']
            # Usa a base apenas se o link for relativo
            link_final = href if href.startswith('http') else config['url_base_item'] + href

            # 2. Limpeza profunda do autor
            autor_raw = o_autor.get_text().strip()
            # Remove prefixos e limpa espaços/quebras de página
            autor_limpo = re.sub(r'^(Por|Autor|Autores)[:\s]*', '', autor_raw, flags=re.IGNORECASE)
            autor_limpo = " ".join(autor_limpo.split())
            
            # 3. Montagem do objeto de dados
            trabalho = {
                'titulo': o_titulo.get_text().strip(),
                'autor': autor_limpo,
                'link': link_final, # <-- USAR A VARIÁVEL TRATADA AQUI
                'ano': meta_dados['ano'],
                'termo': meta_dados['termo'],
                'agregador': meta_dados['agregador']
            }
            resultados.append(trabalho)
        except Exception:
            continue
    return resultados

def ler_detalhes_trabalho(url_detalhe):
    edge_options = Options()
    #edge_options.add_argument("--headless=new")
    driver = webdriver.Edge(options=edge_options)

    try:
        driver.get(url_detalhe)
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        uni_tag = soup.find(['th', 'td'], string=re.compile("Instituição de defesa|Instituição", re.I))
        universidade = uni_tag.find_next('td').get_text(strip=True) if uni_tag else "Não identificada"
       
        # 2. Extrair Programa de Pós-Graduação
        prog_tag = soup.find(['th', 'td'], string=re.compile("Programa de Pós-Graduação|Programa", re.I))
        programa_raw = prog_tag.find_next('td').get_text(strip=True) if prog_tag else "Não identificado"
        programa_limpo = re.sub(r'^\d+[A-Z0-9]*\s+', '', programa_raw) # Limpa códigos CAPES

        # 3. Extrair Link do PDF
        # Procura por links que terminam em .pdf ou que contenham 'bitstream' (padrão de repositórios)
        pdf_tag = soup.find('a', href=re.compile(r'\.pdf$|bitstream|download', re.I))
        link_pdf = pdf_tag['href'] if pdf_tag else "N/A"

        if link_pdf != "N/A" and not link_pdf.startswith('http'):
            # Ajuste de URL relativa se necessário (baseado na URL atual)
            from urllib.parse import urljoin
            link_pdf = urljoin(url_detalhe, link_pdf)

        # 4. Classificação Jurídica
        classificacao = "Jurídico" if "direito" in programa_limpo.lower() else "Não Jurídico"

        # 5. Extrair Resumo
        # Tenta várias tags comuns antes de desistir
        resumo_tag = soup.find(['th', 'td'], string=re.compile("Resumo", re.I))

        if resumo_tag:
            resumo = resumo_tag.find_next('td').get_text(strip=True)
        else:
            resumo_tag = soup.find('div', class_='abstract') or soup.find('div', id='abstract')
            resumo = resumo_tag.get_text(strip=True) if resumo_tag else "Resumo não disponível."

        return {
            "resumo": resumo,
            "universidade": universidade,
            "programa": programa_limpo,
            "classificacao": classificacao,
            "link_pdf": link_pdf
        }
    finally:
        driver.quit()        