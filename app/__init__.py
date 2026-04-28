import os
from flask import Flask, render_template, request, abort
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from datetime import datetime

# --- IMPORTAÇÃO DOS MODELOS E DB ---
from app.models import db, User, Configuracao, Notificacao
from config import config_dict # IMPORTAÇÃO ADICIONADA PARA GERENCIAR CONFIGURAÇÕES

# Inicialização das outras extensões
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Acesso restrito. Por favor, faça login para continuar.'
login_manager.login_message_category = 'warning'

def create_app(config_name='default'):
    """
    Factory Function que cria e configura a aplicação Flask.
    """
    app = Flask(__name__)

    # ==========================================================================
    # 1. CONFIGURAÇÃO DINÂMICA (SUPORTE A VERCEL E POSTGRES)
    # ==========================================================================
    # Se a variável VERCEL existir no ambiente, força o modo produção
    if os.environ.get('VERCEL'):
        config_name = 'production'

    # Carrega as configurações do arquivo config.py com base no ambiente
    app.config.from_object(config_dict[config_name])
    
    print(f"--- MODO DE CONFIGURAÇÃO: {config_name.upper()} ---")
    print(f"--- CONECTANDO AO BANCO DE DADOS: {app.config.get('SQLALCHEMY_DATABASE_URI')} ---")

    # 2. Inicializa as Extensões com a App
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # 3. Configuração do Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ==========================================================================
    # --- ADIÇÃO: BARREIRA DO MODO DE MANUTENÇÃO ---
    # ==========================================================================
    @app.before_request
    def check_maintenance():
        # Ignora as rotas de arquivos estáticos e de autenticação para evitar loop de redirecionamento
        if request.endpoint in ['auth.login', 'auth.logout', 'static']:
            return
        
        try:
            config = Configuracao.query.first()
            # Verifica se a manutenção está ativa no banco de dados
            if config and config.modo_manutencao:
                # Se o usuário logado NÃO for Administrador, bloqueia o acesso
                if current_user.is_authenticated and current_user.perfil != 'Administrador':
                    # Retorna uma página de manutenção simples e amigável direto do backend
                    html_manutencao = """
                    <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100vh; font-family:sans-serif; background-color:#f9fafb;">
                        <h1 style="color:#dc2626; font-size: 2.5rem; margin-bottom: 10px;">🛠️ Sistema em Manutenção</h1>
                        <p style="color:#4b5563; font-size: 1.2rem; text-align:center; max-width: 600px; margin-bottom: 30px;">
                            O sistema está passando por melhorias e atualizações essenciais. Por favor, tente acessar novamente mais tarde.
                        </p>
                        <a href="/auth/logout" style="padding: 12px 24px; background-color:#4b5563; color:white; text-decoration:none; border-radius:5px; font-weight: bold;">Sair com Segurança</a>
                    </div>
                    """
                    return html_manutencao, 503
        except Exception as e:
            pass # Se o banco ainda não existir na primeira rodada, ele apenas segue a vida

    # 4. Context Processor (Notificações Globais)
    @app.context_processor
    def inject_globals():
        try:
            config = Configuracao.query.first()
            if not config:
                try:
                    config = Configuracao(nome_sistema='SparkManagerDocs', sigla_orgao='UEMA')
                except:
                    config = None
            
            notificacoes = Notificacao.query.order_by(Notificacao.created_at.desc()).limit(5).all()
            novas_count = len(notificacoes)
        except:
            config = None
            notificacoes = []
            novas_count = 0
        
        return dict(
            config_sistema=config,
            current_year=datetime.now().year,
            notificacoes_nav=notificacoes,
            notificacoes_count=novas_count,
            now=datetime.now()
        )

    # 5. Registro de Rotas (Blueprints)
    from app.routes import bp_main, bp_auth, bp_admin, bp_oficios
    
    app.register_blueprint(bp_main)
    app.register_blueprint(bp_auth)
    app.register_blueprint(bp_admin)
    app.register_blueprint(bp_oficios)

    # 6. Tratamento de Erros
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        # Fallback de segurança para caso o arquivo errors/500.html não exista ainda!
        try:
            return render_template('errors/500.html'), 500
        except:
            erro_html = """
            <div style="text-align:center; font-family:sans-serif; margin-top:10vh;">
                <h1 style="color:red;">Erro 500</h1>
                <p>Ocorreu um erro interno de processamento ou dependência no servidor.</p>
                <a href="/">Voltar ao início</a>
            </div>
            """
            return erro_html, 500

    # 7. Inicialização do Banco
    # Apenas garante que as tabelas existem, não apaga dados
    with app.app_context():
        db.create_all()
        create_default_admin()

    return app

def create_default_admin():
    """Cria admin padrão se não existir."""
    try:
        # Verifica se já existe o admin no seu banco
        if not User.query.filter_by(email='admin@spark.com').first():
            print("--- Criando Admin Padrão ---")
            admin = User(
                nome='Administrador Sistema',
                email='admin@spark.com',
                password='admin',
                perfil='Administrador',
                ativo=True
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin criado.")
    except Exception as e:
        # Se der erro de tabela inexistente, o db.create_all() acima resolverá na próxima
        pass