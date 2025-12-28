import pandas as pd
import sqlite3
import os

# 1. AJUSTE: Caminho correto do banco usado pela aplicação
# Garante que salva dentro da pasta 'instance'
if not os.path.exists('instance'):
    os.makedirs('instance')
    
DB_NAME = os.path.join("instance", "trabalhos.db")

def importar_dados():
    # Lista dos arquivos CSV
    arquivos_csv = [
        "programas de pós-graduação_1.csv",
        "programas de pós-graduação_2.csv"
    ]
    
    dfs = []
    
    print(f"--- Conectando ao banco: {DB_NAME} ---")
    
    # 1. Lê cada arquivo CSV
    for arquivo in arquivos_csv:
        if os.path.exists(arquivo):
            try:
                # Lê o CSV
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

    # 2. Junta todos os dados
    df_final = pd.concat(dfs, ignore_index=True)
    
    # 3. AJUSTE: Renomeia para as colunas exatas esperadas pelo database.py e view.py
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
    
    # Filtra apenas as colunas que existem no CSV e renomeia
    cols_to_rename = {k: v for k, v in mapa_colunas.items() if k in df_final.columns}
    df_final.rename(columns=cols_to_rename, inplace=True)

    # Mantém apenas as colunas que interessam ao banco para evitar sujeira
    colunas_finais = list(mapa_colunas.values())
    # Garante que só tentamos salvar colunas que realmente existem após o rename
    colunas_para_salvar = [c for c in colunas_finais if c in df_final.columns]
    df_final = df_final[colunas_para_salvar]

    # 4. Grava no Banco de Dados
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME)
        
        # AJUSTE: Nome da tabela deve ser 'programas_pos'
        df_final.to_sql('programas_pos', conn, if_exists='replace', index=False)
        
        print(f"\nSucesso! {len(df_final)} registros importados para a tabela 'programas_pos'.")
        
    except Exception as e:
        print(f"\nErro ao gravar no banco: {e}")
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    importar_dados()