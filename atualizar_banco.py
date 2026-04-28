import sqlite3

conn = sqlite3.connect('sparkmanager_dev.db')
cursor = conn.cursor()

print("Iniciando atualização do banco de dados...")

try:
    cursor.execute("ALTER TABLE oficios ADD COLUMN data_recebimento DATE;")
    print("✅ Coluna 'data_recebimento' adicionada com sucesso.")
except sqlite3.OperationalError as e:
    print(f"⚠️ Aviso: {e} (A coluna já pode existir)")

try:
    cursor.execute("ALTER TABLE oficios ADD COLUMN hora_recebimento TIME;")
    print("✅ Coluna 'hora_recebimento' adicionada com sucesso.")
except sqlite3.OperationalError as e:
    print(f"⚠️ Aviso: {e} (A coluna já pode existir)")

try:
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notas_orcamentarias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_emissao DATE NOT NULL,
        numero_no VARCHAR(50) UNIQUE NOT NULL,
        tipo_no VARCHAR(50) NOT NULL,
        tem_oficio VARCHAR(3) NOT NULL,
        numero_oficio VARCHAR(50),
        processo_sei VARCHAR(50),
        descricao_resumida TEXT NOT NULL,
        status VARCHAR(50) NOT NULL,
        observacoes TEXT,
        created_at DATETIME,
        criador_id INTEGER NOT NULL,
        FOREIGN KEY (criador_id) REFERENCES users (id)
    );
    """)
    print("✅ Tabela 'notas_orcamentarias' verificada/criada com sucesso.")
except sqlite3.OperationalError as e:
    print(f"⚠️ Erro ao criar tabela de notas: {e}")

# =========================================================================
# ADIÇÃO: CRIAÇÃO DA TABELA DE RELACIONAMENTO USUÁRIO <-> SETOR
# =========================================================================
try:
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuario_setor (
        user_id INTEGER NOT NULL,
        setor_id INTEGER NOT NULL,
        PRIMARY KEY (user_id, setor_id),
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (setor_id) REFERENCES setores (id)
    );
    """)
    print("✅ Tabela de associação 'usuario_setor' verificada/criada com sucesso.")
except sqlite3.OperationalError as e:
    print(f"⚠️ Erro ao criar tabela de associação usuario_setor: {e}")

conn.commit()
conn.close()
print("🎉 Atualização concluída! Você já pode rodar o run.py novamente.")