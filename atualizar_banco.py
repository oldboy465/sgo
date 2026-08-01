import sqlite3
import os

# Caminho do banco local de desenvolvimento
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'sparkmanager_dev.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Iniciando atualização da estrutura do banco de dados SQLite local...")

# =========================================================================
# 1. ADIÇÃO DE COLUNAS NA TABELA DE OFÍCIOS
# =========================================================================
try:
    cursor.execute("ALTER TABLE oficios ADD COLUMN data_recebimento DATE;")
    print("✅ Coluna 'data_recebimento' adicionada com sucesso em 'oficios'.")
except sqlite3.OperationalError as e:
    print(f"⚠️ Aviso em 'oficios.data_recebimento': {e} (A coluna já pode existir)")

try:
    cursor.execute("ALTER TABLE oficios ADD COLUMN hora_recebimento TIME;")
    print("✅ Coluna 'hora_recebimento' adicionada com sucesso em 'oficios'.")
except sqlite3.OperationalError as e:
    print(f"⚠️ Aviso em 'oficios.hora_recebimento': {e} (A coluna já pode existir)")

# =========================================================================
# 2. ADIÇÃO DA TABELA DE LOTAÇÕES (UNIDADE FÍSICA DE TRABALHO)
# =========================================================================
try:
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lotacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome VARCHAR(100) NOT NULL,
        sigla VARCHAR(20) NOT NULL UNIQUE,
        ativo BOOLEAN DEFAULT 1
    );
    """)
    print("✅ Tabela 'lotacoes' verificada/criada com sucesso.")
except sqlite3.OperationalError as e:
    print(f"⚠️ Erro ao criar tabela de lotações: {e}")

# =========================================================================
# 3. VINCULAÇÃO DA LOTAÇÃO À TABELA DE USUÁRIOS (users.lotacao_id)
# =========================================================================
try:
    cursor.execute("ALTER TABLE users ADD COLUMN lotacao_id INTEGER REFERENCES lotacoes(id);")
    print("✅ Coluna 'lotacao_id' adicionada à tabela 'users' com sucesso.")
except sqlite3.OperationalError as e:
    print(f"⚠️ Aviso em 'users.lotacao_id': {e} (A coluna já pode existir)")

# =========================================================================
# 4. ADIÇÃO DA TABELA DE NOTAS ORÇAMENTÁRIAS
# =========================================================================
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
# 5. TABELA DE ASSOCIAÇÃO MUITOS-PARA-MUITOS (USUÁRIO <-> SETORES AUTORIZADOS)
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

# =========================================================================
# 6. INSERÇÃO DE LOTAÇÃO PADRÃO (FALLBACK PARA USUÁRIOS EXISTENTES)
# =========================================================================
try:
    cursor.execute("INSERT OR IGNORE INTO lotacoes (id, nome, sigla, ativo) VALUES (1, 'Gabinete / Geral', 'GABINETE', 1);")
    cursor.execute("UPDATE users SET lotacao_id = 1 WHERE lotacao_id IS NULL;")
    print("✅ Lotação padrão atribuída aos usuários pré-existentes com sucesso.")
except sqlite3.OperationalError as e:
    print(f"⚠️ Erro ao atualizar lotação padrão dos usuários: {e}")

conn.commit()
conn.close()

print("\n==================================================================")
print("🎉 ATUALIZAÇÃO CONCLUÍDA! O banco SQLite está pronto.")
print("Agora você pode rodar 'python run.py' novamente sem erros de banco.")
print("==================================================================")