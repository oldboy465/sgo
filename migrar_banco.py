import os

# ========================================================================
# 1. INJETA AS VARIÁVEIS ANTES DE QUALQUER IMPORT DO FLASK
# ========================================================================
POSTGRES_URL = "postgresql://neondb_owner:npg_juJcQVG6W7xk@ep-late-haze-an0gpqd3.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require"

os.environ['POSTGRES_URL'] = POSTGRES_URL
os.environ['DATABASE_URL'] = POSTGRES_URL
os.environ['VERCEL'] = '1' # Força o config.py a entrar no modo production

# Agora sim, podemos importar o Flask e o SQLAlchemy!
from sqlalchemy import create_engine, MetaData, text
from app import create_app
from app.models import db

basedir = os.path.abspath(os.path.dirname(__file__))
sqlite_url = 'sqlite:///' + os.path.join(basedir, 'sparkmanager_dev.db')

print("🔌 Conectando aos bancos de dados...")
engine_sqlite = create_engine(sqlite_url)
engine_postgres = create_engine(POSTGRES_URL)

# Cria a aplicação. Agora ele VAI ler o Postgres corretamente.
app = create_app('production')

with app.app_context():
    print("🏗️  1/3 Criando tabelas oficiais no Neon Postgres...")
    db.create_all() 
    
    print("📖 2/3 Lendo dados do SQLite local...")
    metadata = MetaData()
    metadata.reflect(bind=engine_sqlite)
    
    print("🚀 3/3 Iniciando transferência de dados...")
    with engine_sqlite.connect() as conn_sqlite:
        with engine_postgres.begin() as conn_postgres:
            for table in metadata.sorted_tables:
                print(f"   -> Copiando dados da tabela: {table.name}...")
                
                # Limpa a tabela destino caso rode o script de novo
                conn_postgres.execute(table.delete())
                
                # Extrai dados do SQLite
                records = conn_sqlite.execute(table.select()).mappings().all()
                
                if records:
                    # Converte para inserção massiva
                    dados = [dict(row) for row in records]
                    conn_postgres.execute(table.insert(), dados)
                    
                    # Correção Crítica do Auto-Increment
                    if 'id' in table.columns.keys():
                        try:
                            sql_seq = f"SELECT setval('{table.name}_id_seq', (SELECT MAX(id) FROM {table.name}));"
                            conn_postgres.execute(text(sql_seq))
                        except Exception:
                            pass
                            
                print(f"      OK! {len(records)} registros migrados.")

print("==================================================================")
print("✅ MIGRAÇÃO DEFINITIVA CONCLUÍDA! SEUS DADOS ESTÃO NA NUVEM!")
print("==================================================================")