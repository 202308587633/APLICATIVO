from database import editar_banco_manualmente

# editar_banco_manualmente("UPDATE trabalhos SET classificacao = NULL, resumo = NULL, universidade = NULL, programa = NULL")

editar_banco_manualmente("ALTER TABLE trabalhos ADD COLUMN link_pdf TEXT;")