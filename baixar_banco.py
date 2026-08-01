import os
import sqlite3
import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# 1. URL do Postgres na nuvem (Neon Tech)
POSTGRES_URL = "postgresql://neondb_owner:npg_juJcQVG6W7xk@ep-late-haze-an0gpqd3.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require"

# 2. Caminho do banco local SQLite
SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), "sparkmanager_dev.db")

print("🔌 Conectando ao Neon Postgres (Nuvem)...")
pg_conn = psycopg2.connect(POSTGRES_URL)
pg_cursor = pg_conn.cursor(cursor_factory=RealDictCursor)

print(f"📦 Conectando ao SQLite local ({SQLITE_DB_PATH})...")
sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
sqlite_cursor = sqlite_conn.cursor()

# Lista de tabelas do SGO (incluindo lotacoes)
tabelas = [
    "users",
    "lotacoes",
    "setores",
    "tipos_processo",
    "configuracoes",
    "oficios",
    "notificacoes",
    "notas_orcamentarias",
    "usuario_setor"
]

print("🚀 Sincronizando dados da nuvem para o SQLite local...\n")

def tratar_valor_para_sqlite(val):
    """Converte objetos de Data/Hora para string compatível com SQLite no Python 3.12+"""
    if isinstance(val, datetime.time):
        return val.strftime("%H:%M:%S")
    if isinstance(val, datetime.date) and not isinstance(val, datetime.datetime):
        return val.strftime("%Y-%m-%d")
    if isinstance(val, datetime.datetime):
        return val.strftime("%Y-%m-%d %H:%M:%S")
    return val

for tabela in tabelas:
    try:
        # Busca registros do Postgres
        pg_cursor.execute(f"SELECT * FROM {tabela};")
        rows = pg_cursor.fetchall()

        if rows:
            colunas = list(rows[0].keys())
            colunas_str = ", ".join(colunas)
            placeholders = ", ".join(["?"] * len(colunas))

            # Limpa registros antigos
            sqlite_cursor.execute(f"DELETE FROM {tabela};")

            # Insere registros tratados
            query_insert = f"INSERT INTO {tabela} ({colunas_str}) VALUES ({placeholders});"

            for row in rows:
                valores_tratados = [tratar_valor_para_sqlite(row[col]) for col in colunas]
                sqlite_cursor.execute(query_insert, valores_tratados)

            print(f"   ✅ Tabela '{tabela}': {len(rows)} registros copiados com sucesso!")
        else:
            print(f"   ⚠️ Tabela '{tabela}': Nenhum registro encontrado na nuvem.")

    except Exception as e:
        print(f"   ❌ Erro ao sincronizar tabela '{tabela}': {e}")

# Salva alterações
sqlite_conn.commit()
pg_conn.close()
sqlite_conn.close()

print("\n==================================================")
print("🎉 DADOS BAIXADOS COM SUCESSO! OFÍCIOS E LOTAÇÕES SINCRONIZADOS.")
print("Agora execute 'python run.py' para rodar o SGO localmente.")
print("==================================================")