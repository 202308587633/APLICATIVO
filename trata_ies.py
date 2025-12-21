import re

def extrair_usp(soup):
    """Extração para Biblioteca Digital de Teses e Dissertações da USP"""
    # 1. Tenta via Meta Tag (Mais estável)
    meta_prog = soup.find('meta', attrs={'name': 'dc.publisher.program'})
    if meta_prog:
        return meta_prog.get('content', '').strip()
    
    # 2. Fallback: Busca visual no corpo da página
    label_area = soup.find('div', class_='DocumentoTituloTexto', string=re.compile(r'Área do Conhecimento', re.I))
    if label_area:
        valor = label_area.find_next_sibling('div', class_='DocumentoTexto')
        if valor:
            return valor.get_text(strip=True)
            
    return "Não Identificado"

def extrair_unicap(soup):
    """Extração para UNICAP (DSpace 4.2 / TEDE)"""
    programa = "Não Identificado"
    
    # 1. Busca pelo ID específico da célula de rótulo do Programa
    tag_label = soup.find('td', id='label.dc.publisher.program')
    if tag_label:
        valor = tag_label.find_next_sibling('td')
        if valor:
            return valor.get_text(strip=True)

    # 2. Fallback: Busca via metadados DC no cabeçalho (infalível em DSpace antigo)
    meta_prog = soup.find('meta', attrs={'name': 'DC.publisher', 'xml:lang': 'por'})
    # Nota: Em alguns casos o programa é o último metadado 'publisher' listado
    metas_pub = soup.find_all('meta', attrs={'name': 'DC.publisher'})
    for meta in metas_pub:
        conteudo = meta.get('content', '')
        if "Programa" in conteudo or "Mestrado" in conteudo or "Doutorado" in conteudo:
            return conteudo

    return programa

def extrair_pucsp(soup):
    """Extração para PUC-SP (DSpace 6.3 JSPUI)"""
    programa = "Não Identificado"
    
    # 1. Tenta encontrar na tabela de metadados pela classe específica do DSpace
    tag_programa = soup.find('td', class_='dc_publisher_program')
    if tag_programa:
        valor = tag_programa.find_next_sibling('td', class_='metadataFieldValue')
        if valor:
            return valor.get_text(strip=True)

    # 2. Fallback: Busca no Breadcrumb (ol ou div com links de navegação)
    # Na PUC-SP o programa costuma ser o último link antes do item
    breadcrumb = soup.find('ul', class_='breadcrumb')
    if breadcrumb:
        links = breadcrumb.find_all('a')
        for link in reversed(links):
            texto = link.get_text(strip=True)
            if "Programa" in texto or "Pós-Graduação" in texto:
                return texto

    # 3. Fallback: Meta tags de citação (publisher)
    meta_pub = soup.find('meta', attrs={'name': 'DC.publisher', 'xml:lang': 'pt_BR'})
    if meta_pub:
        return meta_pub.get('content')

    return programa

def extrair_ufop(soup):
    """Extração para a UFOP (DSpace 8 / Angular)"""
    # 1. Tenta encontrar em qualquer componente de metadado do Angular
    # O Angular usa wrappers ou campos genéricos
    elementos_meta = soup.find_all(['ds-metadata-field-wrapper', 'ds-generic-item-page-field', 'div'])
    
    for el in elementos_meta:
        texto = el.get_text(separator=" ", strip=True)
        # Procuramos o padrão do programa dentro do texto do bloco
        if "Programa de Pós-Graduação" in texto:
            # Regex para pegar do início de "Programa" até o fim da linha ou ponto
            match = re.search(r"(Programa de Pós-Graduação em [^.]+)", texto, re.I)
            if match:
                return match.group(1).strip()
            return texto.strip()

    # 2. Fallback: Tenta localizar pelo breadcrumb do Angular (ol.breadcrumb)
    breadcrumb = soup.find('ol', class_=re.compile('breadcrumb', re.I))
    if breadcrumb:
        itens = breadcrumb.find_all('li')
        for item in itens:
            txt = item.get_text(strip=True)
            if "Programa" in txt:
                return txt

    return "Não Identificado"

def extrair_unisinos(soup):
    """Extração robusta para o Repositório da Unisinos (DSpace 7)."""
    # 1. Tenta pelos metadados Dublin Core (Padrão OAI-PMH)
    # Na Unisinos o programa costuma vir em 'dc.publisher.program' ou 'dc.department'
    meta_tags = [
        {'name': 'dc.publisher.program'},
        {'name': 'dc.department'},
        {'name': 'citation_publisher'}
    ]
    
    for tag in meta_tags:
        meta = soup.find('meta', attrs=tag)
        if meta and meta.get('content'):
            return meta.get('content').strip()

    # 2. Fallback: Busca visual na tabela de detalhes (caso o JS oculte os metadados)
    label_prog = soup.find(['th', 'td', 'div'], string=re.compile(r'Programa', re.I))
    if label_prog:
        # Pega o conteúdo da célula vizinha
        valor = label_prog.find_next(['td', 'div', 'span'])
        if valor:
            return valor.get_text(strip=True)

    return "Não Identificado"

def extrair_unb(soup):
    """Extração para a UnB"""
    tag = soup.find('td', class_='dc_description_ppg')
    if tag:
        valor = tag.find_next_sibling('td')
        return valor.get_text(strip=True) if valor else "Não Identificado"
    return "Não Identificado"

def extrair_generico_dspace(soup):
    """Fallback para UFPR, UFV e outros DSpace clássicos"""
    bc = soup.find('ul', class_='breadcrumb')
    if bc:
        links = bc.find_all('a')
        if len(links) >= 3:
            return links[2].get_text(strip=True)
    return "Não Identificado"

def extrair_unifor(soup):
    """Extração para UNIFOR (Sistema Sophia) com tripla verificação"""
    programa = "Não Identificado"
    
    # 1. Tenta pelas Meta Tags (Caminho mais seguro na UNIFOR)
    # O Sophia preenche 'citation_keywords' ou metadados de instituição
    meta_keywords = soup.find('meta', attrs={'name': 'citation_keywords'})
    if meta_keywords:
        conteudo = meta_keywords.get('content', '')
        # Frequentemente o curso aparece nas palavras-chave ou citação
        if "Direito" in conteudo:
            # Se acharmos 'Direito' aqui, já temos uma pista forte
            pass

    # 2. Busca no bloco visual 'box-duplo' (Onde aparece o PPG)
    blocos = soup.find_all('div', class_='box-duplo')
    for bloco in blocos:
        texto = bloco.get_text(separator=" ", strip=True)
        if "Programa de Pós-Graduação" in texto:
            # Extrai o nome do programa após a preposição 'em'
            match = re.search(r"Programa de Pós-Graduação em (.+)", texto, re.I)
            if match:
                return match.group(1).strip()
            return texto

    # 3. Fallback: Se ainda não achou, procura por qualquer texto 'Direito' 
    # próximo a rótulos de curso ou instituição
    labels = soup.find_all('label')
    for label in labels:
        if "Autoria" in label.get_text() or "Publicação" in label.get_text():
            irmao = label.find_next(['p', 'div'])
            if irmao and "Direito" in irmao.get_text():
                return irmao.get_text(strip=True)

    return programa
