import sqlite3
import os

class ScraperDB:
    def __init__(self, db_name="resultados_scraper.db"):
        self.db_name = db_name
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_name)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabela de Trabalhos (Atualizada com colunas 'ano' e 'pagina')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trabalhos (
                    link_bdtd TEXT,
                    termo TEXT,
                    ano TEXT,          -- Novo: Para vincular à página de busca
                    pagina INTEGER,    -- Novo: Para vincular à página de busca
                    titulo TEXT,
                    autor TEXT,
                    sigla TEXT,
                    universidade TEXT,
                    programa TEXT,
                    link_pdf TEXT,
                    link_repo TEXT,
                    html_bdtd TEXT, 
                    html_repo TEXT,
                    data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (link_bdtd, termo)
                )
            ''')

            # NOVA TABELA: Páginas de Busca (Listagens)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS paginas_busca (
                    engine TEXT,
                    termo TEXT,
                    ano TEXT,
                    pagina INTEGER,
                    html_source TEXT,
                    data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (engine, termo, ano, pagina)
                )
            ''')
            conn.commit()



    def execute_query(self, query, params=()):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()

    def save(self, data):
        """Salva um trabalho individual com referência à página de origem."""
        query = '''
            INSERT OR REPLACE INTO trabalhos 
            (link_bdtd, termo, ano, pagina, titulo, autor, sigla, universidade, programa, link_pdf, link_repo, html_bdtd, html_repo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        params = (
            data.get('link_bdtd'), data.get('termo'), data.get('ano'), data.get('pagina'),
            data.get('titulo'), data.get('autor'), data.get('sigla'), data.get('universidade'),
            data.get('programa'), data.get('link_pdf'), data.get('link_repo', ''), 
            data.get('html_bdtd', ''), data.get('html_repo', '')
        )
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.lastrowid



    # --- Métodos para Página de Busca ---
    def save_search_page(self, engine, termo, ano, pagina, html_content):
        """Salva o HTML da lista de resultados."""
        query = '''
            INSERT OR REPLACE INTO paginas_busca (engine, termo, ano, pagina, html_source)
            VALUES (?, ?, ?, ?, ?)
        '''
        self.execute_query(query, (engine, termo, str(ano), pagina, html_content))

    def get_search_page(self, termo, ano, pagina):
        """Recupera HTML da listagem de busca."""
        query = "SELECT html_source FROM paginas_busca WHERE termo=? AND ano=? AND pagina=?"
        with self._get_connection() as conn:
            res = conn.execute(query, (termo, str(ano), pagina)).fetchone()
            return res[0] if res else None


    # --- Métodos de Status e Recuperação ---    
    def check_html_exists(self, db_id):
        """Verifica quais HTMLs existem e retorna os Links (incluindo PDF) para o menu."""
        # ALTERADO: Adicionado 'link_pdf' (índice 7) na consulta
        query = "SELECT html_bdtd, html_repo, termo, ano, pagina, link_bdtd, link_repo, link_pdf FROM trabalhos WHERE rowid = ?"
        with self._get_connection() as conn:
            row = conn.execute(query, (db_id,)).fetchone()
            if not row: return None
            
            # Verifica se os campos de texto têm conteúdo relevante (> 10 chars)
            has_bdtd = bool(row[0] and len(str(row[0])) > 10)
            has_repo = bool(row[1] and len(str(row[1])) > 10)
            
            # Verifica se existe a página de busca salva na tabela de páginas
            termo, ano, pagina = row[2], row[3], row[4]
            has_search = False
            if termo and ano and pagina:
                try:
                    s_row = conn.execute(
                        "SELECT html_source FROM paginas_busca WHERE termo=? AND ano=? AND pagina=?", 
                        (termo, str(ano), pagina)
                    ).fetchone()
                    has_search = bool(s_row and len(str(s_row[0])) > 10)
                except sqlite3.OperationalError:
                    has_search = False

            return {
                'has_bdtd': has_bdtd,
                'has_repo': has_repo,
                'has_search': has_search,
                'meta': {
                    'termo': termo, 'ano': ano, 'pagina': pagina, 
                    'link_bdtd': row[5], 'link_repo': row[6], 'link_pdf': row[7]
                }
            }
 
    # Métodos Utilitários (Mantidos/Adaptados)
    def update_record_details(self, db_id, data):
        query = '''UPDATE trabalhos SET sigla=?, universidade=?, programa=?, link_pdf=? WHERE rowid=?'''
        self.execute_query(query, (data.get('sigla'), data.get('universidade'), data.get('programa'), data.get('link_pdf'), db_id))

    def fetch_all(self):
        query = '''SELECT rowid, termo, ano, titulo, autor, sigla, universidade, programa, link_pdf, link_repo, link_bdtd FROM trabalhos ORDER BY rowid ASC'''
        with self._get_connection() as conn:
            return conn.execute(query).fetchall()

    def get_specific_html(self, db_id, target='repo'):
        column = 'html_bdtd' if target == 'bdtd' else 'html_repo'
        with self._get_connection() as conn:
            res = conn.execute(f'SELECT {column} FROM trabalhos WHERE rowid = ?', (db_id,)).fetchone()
            return res[0] if res else None
        
    def update_specific_html(self, db_id, target, content, url=None):
        if target == 'bdtd':
            self.execute_query("UPDATE trabalhos SET html_bdtd = ? WHERE rowid = ?", (content, db_id))
        else:
            self.execute_query("UPDATE trabalhos SET html_repo = ?, link_repo = ? WHERE rowid = ?", (content, url, db_id))

    def clear_field(self, db_id, field_type):
        """Limpa campos específicos baseados no tipo solicitado."""
        map_fields = {
            'html_bdtd': 'html_bdtd',
            'html_repo': 'html_repo',
            'link_pdf': 'link_pdf',
            'link_repo': 'link_repo'
        }
        
        # NOVO: Limpeza em lote dos dados extraídos (Sigla, Universidade, Programa)
        if field_type == 'extracted_data':
            query = "UPDATE trabalhos SET sigla = '-', universidade = '-', programa = '-' WHERE rowid = ?"
            self.execute_query(query, (db_id,))
            return

        if field_type in map_fields:
            val = '-' if 'link' in field_type else ''
            self.execute_query(f"UPDATE trabalhos SET {map_fields[field_type]} = ? WHERE rowid = ?", (val, db_id))
            
    def delete_search_page(self, termo, ano, pagina):
        """Apaga o conteúdo HTML da página de busca (mantendo o registro)."""
        query = "UPDATE paginas_busca SET html_source = '' WHERE termo=? AND ano=? AND pagina=?"
        self.execute_query(query, (termo, str(ano), pagina))
                     
    def fetch_one_per_university(self):
        """
        Retorna apenas uma linha de cada universidade encontrada (GROUP BY sigla).
        Útil para validar se os parsers de diferentes universidades estão funcionando.
        """
        # Seleciona as mesmas colunas que o fetch_all para manter compatibilidade com a View
        query = '''
            SELECT rowid, termo, ano, titulo, autor, sigla, universidade, programa, link_pdf, link_repo, link_bdtd 
            FROM trabalhos 
            GROUP BY sigla 
            ORDER BY sigla ASC
        '''
        try:
            # CORREÇÃO: Abre a conexão corretamente usando o método auxiliar da classe
            with self._get_connection() as conn:
                return conn.execute(query).fetchall()
        except Exception as e:
            print(f"Erro ao buscar amostra: {e}")
            return []