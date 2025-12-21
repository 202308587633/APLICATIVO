# Mapeamento de seletores CSS e parâmetros de URL
CONFIG_AGREGADORES = {
    "BDTD (IBICT)": {
        "param_pagina": "page",
        "seletor_itens": ".result",
        "seletor_paginacao": ".pagination li a",
        "seletor_titulo": ".title",
        "seletor_autor": ".author a",
        "url_base_item": "https://bdtd.ibict.br"
    },
    "SciELO Brasil": {
        "param_pagina": "from",  # SciELO costuma usar 'from' para offset
        "seletor_itens": ".item",
        "seletor_paginacao": ".pagination .next", # Exemplo
        "seletor_titulo": ".title",
        "seletor_autor": ".author",
        "url_base_item": ""
    }
}