import pandas as pd
import sqlite3
import os

# Configura o caminho para a raiz
DB_NAME = "resultados_scraper.db"

def importar_dados():
    arquivos_csv = [
        "programas de pós-graduação_1.csv",
        "programas de pós-graduação_2.csv"
    ]
    
    dfs = []
    print(f"--- Conectando ao banco na raiz: {DB_NAME} ---")
    
    for arquivo in arquivos_csv:
        if os.path.exists(arquivo):
            try:
                # O separador dos seus CSVs parece ser vírgula
                df = pd.read_csv(arquivo, sep=',', encoding='utf-8')
                dfs.append(df)
                print(f"Lido: {arquivo} ({len(df)} registros)")
            except Exception as e:
                print(f"Erro ao ler {arquivo}: {e}")
        else:
            print(f"Arquivo não encontrado: {arquivo}")
    
    if not dfs:
        print("Nenhum dado para importar.")
        return

    # Junta os dados
    df_final = pd.concat(dfs, ignore_index=True)
    
    # Mapeamento exato das colunas do CSV para a tabela 'programas_pos'
    mapa_colunas = {
        'Código Programa': 'codigo_programa',
        'Nome do programa': 'nome_programa',
        'Sigla IES': 'sigla_ies',
        'Grau acadêmico Atual do PPG': 'grau_academico',
        'Nome Modalidade': 'modalidade',
        'Nota do Programa': 'nota_programa',
        'Situação Programa': 'situacao_programa',
        'Programa em Forma Associativa': 'forma_associativa',
        'Área de Avaliação': 'area_avaliacao',
        'Área Conhecimento': 'area_conhecimento',
        'Grande área de conhecimento': 'grande_area_conhecimento'
    }
    
    # Renomeia as colunas
    cols_to_rename = {k: v for k, v in mapa_colunas.items() if k in df_final.columns}
    df_final.rename(columns=cols_to_rename, inplace=True)
    
    # Seleciona apenas as colunas que interessam ao banco
    colunas_banco = list(mapa_colunas.values())
    df_final = df_final[[c for c in colunas_banco if c in df_final.columns]]

    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        
        # IMPORTANTE: Usa 'programas_pos' (mesmo nome que database.py usa)
        df_final.to_sql('programas_pos', conn, if_exists='replace', index=False)
        
        print(f"\nSucesso! {len(df_final)} registros salvos na tabela 'programas_pos' em '{DB_NAME}'.")
        
    except Exception as e:
        print(f"\nErro ao gravar no banco: {e}")
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    importar_dados()