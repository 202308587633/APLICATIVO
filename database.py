import sqlite3
import os

class ScraperDB:
    def __init__(self, db_name="resultados_scraper.db"):
        # Define o caminho do banco na RAIZ do projeto
        self.db_path = os.path.join(os.getcwd(), db_name)
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def execute_query(self, query, params=()):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabela de Trabalhos (Scraper)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trabalhos (
                    link_bdtd TEXT,
                    termo TEXT,
                    ano TEXT,
                    pagina INTEGER,
                    titulo TEXT,
                    autor TEXT,
                    sigla TEXT,
                    universidade TEXT,
                    programa TEXT,
                    link_pdf TEXT,
                    link_repo TEXT,
                    html_bdtd TEXT, 
                    html_repo TEXT,
                    extracted_data TEXT,
                    data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (link_bdtd, termo)
                )
            ''')

            # Tabela de Páginas de Busca
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

            # Tabela de Programas de Pós-Graduação (Nome correto: programas_pos)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS programas_pos (
                    codigo_programa TEXT PRIMARY KEY,
                    nome_programa TEXT,
                    sigla_ies TEXT,
                    grau_academico TEXT,
                    modalidade TEXT,
                    nota_programa TEXT,
                    situacao_programa TEXT,
                    forma_associativa TEXT,
                    area_avaliacao TEXT,
                    area_conhecimento TEXT,
                    grande_area_conhecimento TEXT
                )
            ''')
            
            conn.commit()

    def save(self, data):
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
        self.execute_query(query, params)
        return 0

    def fetch_all(self):
        query = "SELECT rowid, termo, ano, titulo, autor, sigla, universidade, programa, link_pdf, link_repo, link_bdtd FROM trabalhos"
        with self._get_connection() as conn:
            return conn.execute(query).fetchall()

    def check_html_exists(self, db_id, target_type):
        col = f"html_{target_type}"
        query = f"SELECT 1 FROM trabalhos WHERE rowid = ? AND length({col}) > 0"
        with self._get_connection() as conn:
            return conn.execute(query, (db_id,)).fetchone() is not None

    def get_specific_html(self, db_id, target_type):
        col = f"html_{target_type}"
        query = f"SELECT {col} FROM trabalhos WHERE rowid = ?"
        with self._get_connection() as conn:
            res = conn.execute(query, (db_id,)).fetchone()
            return res[0] if res else None

    def save_search_page(self, engine, termo, ano, pagina, html):
        query = '''
            INSERT OR REPLACE INTO paginas_busca (engine, termo, ano, pagina, html_source)
            VALUES (?, ?, ?, ?, ?)
        '''
        self.execute_query(query, (engine, termo, str(ano), pagina, html))

    def get_search_page(self, termo, ano, pagina):
        query = "SELECT html_source FROM paginas_busca WHERE termo=? AND ano=? AND pagina=?"
        with self._get_connection() as conn:
            res = conn.execute(query, (termo, str(ano), pagina)).fetchone()
            return res[0] if res else None
            
    def update_specific_html(self, db_id, target_type, html_content, url_repo=None):
        col_html = f"html_{target_type}"
        if target_type == 'repo' and url_repo:
            query = f"UPDATE trabalhos SET {col_html} = ?, link_repo = ? WHERE rowid = ?"
            self.execute_query(query, (html_content, url_repo, db_id))
        else:
            query = f"UPDATE trabalhos SET {col_html} = ? WHERE rowid = ?"
            self.execute_query(query, (html_content, db_id))

    def update_record_details(self, db_id, data):
        fields = []
        values = []
        if 'sigla' in data: fields.append("sigla=?"); values.append(data['sigla'])
        if 'universidade' in data: fields.append("universidade=?"); values.append(data['universidade'])
        if 'programa' in data: fields.append("programa=?"); values.append(data['programa'])
        if 'link_pdf' in data: fields.append("link_pdf=?"); values.append(data['link_pdf'])
        if 'link_repo' in data: fields.append("link_repo=?"); values.append(data['link_repo'])
        
        if fields:
            values.append(db_id)
            query = f"UPDATE trabalhos SET {', '.join(fields)} WHERE rowid = ?"
            self.execute_query(query, tuple(values))

    def clear_field(self, db_id, field_type):
        map_fields = {
            'link_pdf': 'link_pdf',
            'link_repo': 'link_repo',
            'html_repo': 'html_repo',
            'html_bdtd': 'html_bdtd',
            'extracted_data': 'extracted_data'
        }
        if field_type == 'extracted_data':
            query = "UPDATE trabalhos SET sigla='', universidade='', programa='', link_repo='', extracted_data='' WHERE rowid=?"
            self.execute_query(query, (db_id,))
            return

        if field_type in map_fields:
            val = '-' if 'link' in field_type else ''
            self.execute_query(f"UPDATE trabalhos SET {map_fields[field_type]} = ? WHERE rowid = ?", (val, db_id))
            
    def delete_search_page(self, termo, ano, pagina):
        query = "UPDATE paginas_busca SET html_source = '' WHERE termo=? AND ano=? AND pagina=?"
        self.execute_query(query, (termo, str(ano), pagina))
                     
    def fetch_one_per_university(self):
        query = '''
            SELECT rowid, termo, ano, titulo, autor, sigla, universidade, programa, link_pdf, link_repo, link_bdtd 
            FROM trabalhos 
            GROUP BY sigla 
            ORDER BY sigla ASC
        '''
        with self._get_connection() as conn:
            return conn.execute(query).fetchall()

    def get_all_programs(self):
        """Retorna todos os programas de pós-graduação cadastrados."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Busca da tabela correta: programas_pos
                cursor.execute("SELECT * FROM programas_pos ORDER BY nome_programa ASC")
                return cursor.fetchall()
        except Exception as e:
            print(f"Erro ao buscar programas: {e}")
            return []

    def save_program(self, data_tuple):
        """Salva ou atualiza um programa de pós-graduação."""
        query = '''
            INSERT OR REPLACE INTO programas_pos (
                codigo_programa, nome_programa, sigla_ies, grau_academico, 
                modalidade, nota_programa, situacao_programa, forma_associativa, 
                area_avaliacao, area_conhecimento, grande_area_conhecimento
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        self.execute_query(query, data_tuple)