import pandas as pd
import sqlite3
import os

# Nome do banco de dados da sua aplicação
DB_NAME = "resultados_scraper.db"

def importar_dados():
    # Lista dos arquivos CSV que você enviou
    arquivos_csv = [
        "programas de pós-graduação_2.csv",
        "programas de pós-graduação_1.csv"
    ]
    
    dfs = []
    
    print("--- Iniciando Importação ---")
    
    # 1. Lê cada arquivo CSV
    for arquivo in arquivos_csv:
        if os.path.exists(arquivo):
            try:
                # Lê o CSV (o separador padrão costuma ser vírgula, mas ajustamos se necessário)
                df = pd.read_csv(arquivo)
                dfs.append(df)
                print(f"Lido: {arquivo} ({len(df)} registros)")
            except Exception as e:
                print(f"Erro ao ler {arquivo}: {e}")
        else:
            print(f"Arquivo não encontrado: {arquivo}")
    
    if not dfs:
        print("Nenhum dado para importar.")
        return

    # 2. Junta todos os dados em um único DataFrame
    df_final = pd.concat(dfs, ignore_index=True)
    
    # 3. Renomeia as colunas para um padrão compatível com SQL (sem espaços/acentos)
    mapa_colunas = {
        'Código Programa': 'codigo_programa',
        'Nome do programa': 'nome_programa',
        'Sigla IES': 'sigla_ies',
        'Grau acadêmico Atual do PPG': 'grau_academico',
        'Nome Modalidade': 'modalidade',
        'Nota do Programa': 'nota',
        'Situação Programa': 'situacao',
        'Programa em Forma Associativa': 'associativo',
        'Área de Avaliação': 'area_avaliacao',
        'Área Conhecimento': 'area_conhecimento',
        'Grande área de conhecimento': 'grande_area'
    }
    
    # Verifica se as colunas existem antes de renomear para evitar erros
    cols_to_rename = {k: v for k, v in mapa_colunas.items() if k in df_final.columns}
    df_final.rename(columns=cols_to_rename, inplace=True)

    # 4. Grava no Banco de Dados
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        
        # 'if_exists="replace"' recria a tabela. Use "append" se quiser apenas adicionar.
        # Index=False evita criar uma coluna extra para o índice do pandas.
        df_final.to_sql('programas_pos_graduacao', conn, if_exists='replace', index=False)
        
        print(f"\nSucesso! {len(df_final)} registros foram gravados na tabela 'programas_pos_graduacao'.")
        
        # Cria um índice para busca rápida pelo nome do programa (útil para o seu scraper)
        cursor = conn.cursor()
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_nome_programa ON programas_pos_graduacao (nome_programa)")
        conn.commit()
        
    except Exception as e:
        print(f"Erro ao gravar no banco de dados: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    importar_dados()