import sqlite3

def conectar():
    conn = sqlite3.connect("trabalhos_academicos.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Criamos a tabela com a estrutura completa
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trabalhos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT,
            autor TEXT,
            link TEXT UNIQUE,
            universidade TEXT,
            programa TEXT,
            classificacao TEXT,
            resumo TEXT,
            data_coleta DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tenta adicionar as colunas uma por uma, caso a tabela já exista
    colunas_novas = ["universidade", "programa", "classificacao", "resumo"]
    for coluna in colunas_novas:
        try:
            cursor.execute(f"ALTER TABLE trabalhos ADD COLUMN {coluna} TEXT")
        except sqlite3.OperationalError:
            # Se cair aqui, é porque a coluna já existe, então ignoramos o erro
            pass
            
    conn.commit()
    return conn

def salvar_detalhes_completos(link, resumo, programa, uni, classe):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE trabalhos 
        SET resumo = ?, programa = ?, universidade = ?, classificacao = ? 
        WHERE link = ?
    """, (resumo, programa, uni, classe, link))
    conn.commit()
    conn.close()

def salvar_resultados(lista_trabalhos):
    """Recebe a lista de dicionários e salva no banco de dados."""
    conn = conectar()
    cursor = conn.cursor()
    
    count_novos = 0
    for t in lista_trabalhos:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO trabalhos (titulo, autor, link)
                VALUES (?, ?, ?)
            """, (t['Título'], t['Autor'], t['Link']))
            
            if cursor.rowcount > 0:
                count_novos += 1
        except sqlite3.Error as e:
            print(f"Erro ao inserir: {e}")
            
    conn.commit()
    conn.close()
    return count_novos

def buscar_trabalho_por_link(link):
    """Busca todos os dados de um trabalho específico no banco."""
    conn = conectar()
    cursor = conn.cursor()
    # Selecionamos todas as colunas para o link informado
    cursor.execute("SELECT * FROM trabalhos WHERE link = ?", (link,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado

def recuperar_todos():
    """Retorna todos os trabalhos salvos no banco."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT titulo, autor, link FROM trabalhos ORDER BY data_coleta DESC")
    dados = cursor.fetchall()
    conn.close()
    return dados