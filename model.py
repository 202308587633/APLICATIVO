import requests
import urllib3
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ScraperModel:
    def __init__(self): pass
    
    def fetch(self, strategy, term, year, page_num, on_progress=None):
        """Retorna: (lista_itens, mensagem, html_bruto_da_pagina)"""
        try:
            url = strategy.get_url(term, year, page_num)
            if on_progress: on_progress(f"1. URL: {url}")
        except Exception as e: return [], f"Erro URL: {e}", ""
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
            if on_progress: on_progress("2. Baixando lista...")
            
            response = requests.get(url, headers=headers, timeout=30, verify=False)
            if response.status_code != 200: return [], f"Erro HTTP {response.status_code}", ""
            
            raw_html = response.text 
            from bs4 import BeautifulSoup
            if on_progress: on_progress("3. Processando HTML...")
            soup = BeautifulSoup(response.content, 'html.parser')
            
            items = strategy.parse(soup, on_progress=on_progress)
            
            # Adiciona metadados da busca em cada item
            for item in items:
                item['ano'] = year
                item['pagina'] = page_num
            
            if not items:
                return [], "Zero itens encontrados.", raw_html
                
            return items, f"Sucesso: {len(items)} itens.", raw_html

        except Exception as e: return [], f"Erro Model: {str(e)}", ""