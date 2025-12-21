import urllib.parse

def gerar_url_por_fonte(fonte, ano, inc, exc, fontes_disponiveis):
    """Gera a URL de busca baseada na sintaxe de cada agregador."""
    query = f'"{inc}"'
    if exc:
        query += " " + " ".join([f'-"{t}"' for t in exc])
    
    query_encoded = urllib.parse.quote(query)

    if "BDTD" in fonte:
        return (f"https://bdtd.ibict.br/vufind/Search/Results?"
                f"lookfor={query_encoded}&type=AllFields&"
                f"filter%5B%5D=publishDate%3A%22%5B{ano}+TO+{ano}%5D%22")
    
    elif "SciELO" in fonte:
        return f"https://search.scielo.org/?q={query_encoded}&filter[year][]={ano}"
    
    elif "Scholar" in fonte:
        return f"https://scholar.google.com.br/scholar?q={query_encoded}+as_ylo={ano}&as_yhi={ano}"
    
    base_url = fontes_disponiveis.get(fonte, "")
    return f"{base_url}search?q={query_encoded}"