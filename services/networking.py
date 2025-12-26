import requests
import random

class NetworkingService:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) Firefox/121.0'
        ]

    def get(self, url, timeout=15, on_progress=None):
        """Centraliza a requisição e reporta o início do download."""
        if on_progress: 
            # Reporta o domínio que está sendo acessado
            dominio = url.split('/')[2]
            on_progress(f"Conectando a {dominio}...")
            
        headers = {'User-Agent': random.choice(self.user_agents)}
        return requests.get(url, headers=headers, timeout=timeout)