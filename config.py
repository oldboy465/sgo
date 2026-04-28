import os
from datetime import timedelta

# Define o diretório raiz do projeto de forma robusta (compatível com Linux/Windows)
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """
    Configurações Base (Genéricas).
    Herda para todos os ambientes.
    """
    # ==========================================================================
    # SEGURANÇA E CRIPTOGRAFIA
    # ==========================================================================
    # A chave deve ser longa e aleatória. Em produção, JAMAIS deixe hardcoded.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'UEMA-SPARK-MANAGER-KEY-@918273-SECURE'
    
    # Proteção de Sessão
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=60) # Desloga após 60 min de inatividade
    SESSION_COOKIE_HTTPONLY = True # Impede acesso ao cookie via JavaScript (XSS Protection)
    SESSION_COOKIE_SECURE = False  # Mude para True se usar HTTPS em produção
    
    # ==========================================================================
    # DATABASE (SQLAlchemy)
    # ==========================================================================
    SQLALCHEMY_TRACK_MODIFICATIONS = False # Desativa evento de sinalização (economiza memória)
    SQLALCHEMY_RECORD_QUERIES = False
    
    # Configuração de Pool de Conexão (Vital para evitar "MySQL has gone away")
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_timeout': 20
    }

    # ==========================================================================
    # UPLOADS E ARQUIVOS
    # ==========================================================================
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Limite de upload: 16MB
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'xls', 'xlsx'}

    # ==========================================================================
    # PARÂMETROS DE NEGÓCIO (CONSTANTES GLOBAIS)
    # ==========================================================================
    SYSTEM_NAME = 'SparkManagerDocs'
    ORGANIZATION_NAME = 'Universidade Estadual do Maranhão - UEMA'
    ROWS_PER_PAGE = 15 # Paginação padrão para tabelas
    TIMEZONE = 'America/Sao_Paulo'


class DevelopmentConfig(Config):
    """
    Ambiente de Desenvolvimento (Sua máquina Windows com VS Code).
    """
    DEBUG = True
    SQLALCHEMY_ECHO = True # Exibe o SQL gerado no terminal (ótimo para debug)
    
    # SQLite local para desenvolvimento rápido
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'sparkmanager_dev.db')


class ProductionConfig(Config):
    """
    Ambiente de Produção (Hostgator Linux / Vercel).
    """
    DEBUG = False
    SQLALCHEMY_ECHO = False
    
    # Em produção, forçamos HTTPS nos cookies (O Vercel usa HTTPS por padrão)
    SESSION_COOKIE_SECURE = True 
    
    # Captura a URL do banco do Vercel Postgres ou de outra variável de ambiente
    db_url = os.environ.get('POSTGRES_URL') or os.environ.get('DATABASE_URL')
    
    if db_url:
        # SQLAlchemy 1.4+ exige 'postgresql://' em vez de 'postgres://'
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = db_url
    else:
        # Fallback para banco em MEMÓRIA para o Vercel não dar erro de leitura/escrita
        SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


class TestingConfig(Config):
    """
    Ambiente de Testes Automatizados.
    """
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:' # Banco em memória RAM (volátil)
    WTF_CSRF_ENABLED = False # Desabilita proteção de formulário para facilitar testes


# Dicionário de mapeamento para facilitar a importação no __init__.py
config_dict = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}