import re
import time
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def buscar_id_instituicao(sigla):
    edge_options = Options()
    edge_options.add_argument("--headless=new") # Pode mudar para headless=false se quiser ver o navegador
    edge_options.add_argument("--disable-gpu")
    edge_options.add_argument("--no-sandbox")
    
    driver = webdriver.Edge(options=edge_options)
    wait = WebDriverWait(driver, 20)
    
    try:
        # Acessa a página de busca com a sigla informada
        url_busca = f"https://sucupira.capes.gov.br/observatorio/geral?search={sigla.strip()}"
        driver.get(url_busca)
        
        # Espera o carregamento dos links de instituições (conforme o HTML enviado)
        # O seletor busca o link que contém 'detalhamento/instituicoes/' e o texto da sigla
        xpath_link = f"//a[contains(@href, 'detalhamento/instituicoes/') and contains(text(), '{sigla.upper()}')]"
        
        try:
            elemento_link = wait.until(EC.presence_of_element_located((By.XPATH, xpath_link)))
            href = elemento_link.get_attribute("href")
            
            # Extração do ID: Captura os dígitos entre 'instituicoes/' e o '?'
            match = re.search(r'instituicoes/(\d+)\?', href)
            
            if match:
                id_encontrado = match.group(1)
                
                # Monta a nova URL de redirecionamento direto
                url_detalhe = f"https://sucupira.capes.gov.br/observatorio/detalhamento/instituicoes/{id_encontrado}"
                ### https://sucupira.capes.gov.br/observatorio/programas-de-pos-graduacao?ano-base=2020&id-ies=2317&search=direito&size=20&page=0
                
                # Redireciona o navegador para a página final
                driver.get(url_detalhe)
                time.sleep(2) # Pequena pausa para garantir o carregamento visual
                
                return id_encontrado
        except:
            return None

    except Exception as e:
        print(f"Erro na extração Sucupira: {e}")
        return None
    finally:
        driver.quit()