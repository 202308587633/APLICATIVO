import sqlite3
import csv
import os

# Configurações
DB_PATH = os.path.join('instance', 'trabalhos.db')
CSV_FILES = [
    'programas de pós-graduação_1.csv',
    'programas de pós-graduação_2.csv'
]

def criar_tabela_programas(cursor):
    """Cria a tabela para armazenar os programas de pós-graduação."""
    print("Verificando/Criando tabela 'programas_pos'...")
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

def importar_csv(arquivo, cursor):
    """Lê um arquivo CSV e insere os dados no banco."""
    if not os.path.exists(arquivo):
        print(f"ERRO: Arquivo '{arquivo}' não encontrado.")
        return

    print(f"Importando: {arquivo}...")
    
    with open(arquivo, mode='r', encoding='utf-8') as f:
        # DictReader usa a primeira linha como chave do dicionário
        reader = csv.DictReader(f)
        
        count = 0
        for row in reader:
            # Mapeamento das colunas do CSV para o Banco
            # CSV Headers: Código Programa,Nome do programa,Sigla IES,Grau acadêmico Atual do PPG,
            # Nome Modalidade,Nota do Programa,Situação Programa,Programa em Forma Associativa,
            # Área de Avaliação,Área Conhecimento,Grande área de conhecimento
            
            data = (
                row.get('Código Programa', '').strip(),
                row.get('Nome do programa', '').strip(),
                row.get('Sigla IES', '').strip(),
                row.get('Grau acadêmico Atual do PPG', '').strip(),
                row.get('Nome Modalidade', '').strip(),
                row.get('Nota do Programa', '').strip(),
                row.get('Situação Programa', '').strip(),
                row.get('Programa em Forma Associativa', '').strip(),
                row.get('Área de Avaliação', '').strip(),
                row.get('Área Conhecimento', '').strip(),
                row.get('Grande área de conhecimento', '').strip()
            )

            # Usamos INSERT OR REPLACE para evitar duplicatas se rodar o script 2x
            cursor.execute('''
                INSERT OR REPLACE INTO programas_pos (
                    codigo_programa, nome_programa, sigla_ies, grau_academico, 
                    modalidade, nota_programa, situacao_programa, forma_associativa, 
                    area_avaliacao, area_conhecimento, grande_area_conhecimento
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', data)
            count += 1
            
        print(f"-> {count} registros processados em '{arquivo}'.")

def main():
    # Garante que a pasta instance existe
    if not os.path.exists('instance'):
        os.makedirs('instance')
        
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 1. Cria a tabela
        criar_tabela_programas(cursor)

        # 2. Importa os arquivos
        for csv_file in CSV_FILES:
            importar_csv(csv_file, cursor)

        # 3. Salva e fecha
        conn.commit()
        print("\nImportação concluída com sucesso!")
        print(f"Banco de dados atualizado: {DB_PATH}")
        
    except sqlite3.Error as e:
        print(f"Erro no Banco de Dados: {e}")
    except Exception as e:
        print(f"Erro inesperado: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()