import sqlite3
from contextlib import contextmanager

# Constante global para facilitar manutenção
DB_NAME = "trabalhos_academicos.db"

@contextmanager
def obter_conexao():
    """Gerenciador de contexto para conexões SQLite. 
    Garante commit e fechamento automático."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Erro na transação do banco: {e}")
        raise
    finally:
        conn.close()

def inicializar_banco():
    """Cria tabelas e realiza migrações de colunas necessárias."""
    with obter_conexao() as conn:
        cursor = conn.cursor()
        
        # Tabela Principal
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trabalhos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT,
                autor TEXT,
                data TEXT,
                link TEXT UNIQUE,
                resumo TEXT,
                programa TEXT,
                universidade TEXT,
                classificacao TEXT,
                link_pdf TEXT,
                data_coleta TEXT
            )
        """)
        
        # Tabela Instituições
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS instituicoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sigla TEXT UNIQUE,
                id_sucupira TEXT
            )
        """)

        # Tabela Instituições para Sucupira
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS instituicoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sigla TEXT UNIQUE,
                id_sucupira TEXT
            )
        """)

def salvar_id_sucupira(sigla: str, id_sucupira: str):
    with obter_conexao() as conn:
        conn.cursor().execute(
            "INSERT OR REPLACE INTO instituicoes (sigla, id_sucupira) VALUES (?, ?)", 
            (sigla.upper(), id_sucupira)
        )

def limpar_detalhes_trabalho(id_trabalho: int):
    with obter_conexao() as conn:
        conn.cursor().execute("""
            UPDATE trabalhos 
            SET resumo = NULL, 
                universidade = NULL, 
                programa = NULL, 
                classificacao = 'Não Analisado' 
            WHERE id = ?
        """, (id_trabalho,))

def salvar_detalhes_completos(link, resumo, programa, universidade, classificacao, link_pdf):
    with obter_conexao() as conn:
        conn.cursor().execute("""
            UPDATE trabalhos 
            SET resumo = ?, programa = ?, universidade = ?, 
                classificacao = ?, link_pdf = ?
            WHERE link = ?
        """, (resumo, programa, universidade, classificacao, link_pdf, link))

def salvar_resultados(lista_trabalhos):
    """Insere títulos e autores da busca inicial."""
    count_novos = 0
    with obter_conexao() as conn:
        cursor = conn.cursor()
        for t in lista_trabalhos:
            cursor.execute("""
                INSERT OR IGNORE INTO trabalhos (titulo, autor, link)
                VALUES (?, ?, ?)
            """, (t['Título'], t['Autor'], t['Link']))
            if cursor.rowcount > 0:
                count_novos += 1
    return count_novos

def buscar_trabalho_por_link(link: str):
    with obter_conexao() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM trabalhos WHERE link = ?", (link,))
        row = cursor.fetchone()
        return dict(row) if row else None

def recuperar_todos():
    with obter_conexao() as conn:
        cursor = conn.cursor()
        # Ajustado para usar o nome correto da coluna de ordenação
        cursor.execute("""
            SELECT id, titulo, autor, universidade, programa, classificacao, link 
            FROM trabalhos 
            ORDER BY id ASC
        """)
        return cursor.fetchall()

def editar_banco_manualmente(query_sql: str):
    """Executa comando SQL livre. Use com cautela."""
    with obter_conexao() as conn:
        try:
            conn.cursor().execute(query_sql)
        except sqlite3.Error as e:
            print(f"Falha na execução manual: {e}")