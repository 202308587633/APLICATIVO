import sqlite3
from contextlib import contextmanager

DB_NAME = "trabalhos_academicos.db"

@contextmanager
def abrir_conexao():
    """Gerenciador de contexto para garantir que a conexão sempre feche."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def inicializar_banco():
    """Cria a estrutura inicial e gerencia migrações de coluna."""
    with abrir_conexao() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trabalhos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT,
                autor TEXT,
                link TEXT,
                universidade TEXT,
                programa TEXT,
                classificacao TEXT,
                resumo TEXT,
                link_pdf TEXT,
                ano TEXT,
                agregador TEXT,
                termo TEXT,
                data_coleta DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(link, termo)
                )
            """)
        conn.commit()

def salvar_resultados(lista_trabalhos):
    """Insere novos trabalhos usando transação única para performance."""
    count_novos = 0
    with abrir_conexao() as conn:
        cursor = conn.cursor()
        for t in lista_trabalhos:
            cursor.execute("""
                INSERT OR IGNORE INTO trabalhos (titulo, autor, link, ano, agregador, termo)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (t.get('titulo'), t.get('autor'), t.get('link'), t.get('ano'), t.get('agregador'), t.get('termo')))
            
            if cursor.rowcount > 0:
                count_novos += 1
        conn.commit()
    return count_novos

def salvar_detalhes_completos(link, resumo, programa, uni, classe, link_pdf=None):
    """Atualiza um registro existente com os dados do scrap detalhado."""
    with abrir_conexao() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE trabalhos 
            SET resumo = ?, programa = ?, universidade = ?, classificacao = ?, link_pdf = ?
            WHERE link = ?
        """, (resumo, programa, uni, classe, link_pdf, link))
        conn.commit()

def buscar_trabalho_por_link(link):
    """Retorna um dicionário com os dados do trabalho ou None."""
    with abrir_conexao() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM trabalhos WHERE link = ?", (link,))
        row = cursor.fetchone()
        return dict(row) if row else None

def recuperar_todos():
    """Retorna todos os registros ordenados pelo ID (ordem de descoberta)."""
    with abrir_conexao() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM trabalhos ORDER BY id ASC")
        return [dict(row) for row in cursor.fetchall()]

def limpar_detalhes_trabalho(id_trabalho):
    """Reseta os detalhes de um trabalho para permitir novo scrap."""
    with abrir_conexao() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE trabalhos 
            SET resumo = NULL, programa = NULL, universidade = NULL, 
                classificacao = NULL, link_pdf = NULL 
            WHERE id = ?
        """, (id_trabalho,))
        conn.commit()