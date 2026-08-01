import os
from flask import Flask, render_template, request, abort
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from datetime import datetime

# --- IMPORTAÇÃO DOS MODELOS E DB ---
from app.models import db, User, Configuracao, Notificacao
from config import config_dict

# Inicialização das extensões Flask
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
    if os.environ.get('VERCEL'):
        config_name = 'production'

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
    # --- BARREIRA DO MODO DE MANUTENÇÃO ---
    # ==========================================================================
    @app.before_request
    def check_maintenance():
        if request.endpoint in ['auth.login', 'auth.logout', 'static']:
            return

        try:
            config = Configuracao.query.first()
            if config and config.modo_manutencao:
                if current_user.is_authenticated and current_user.perfil != 'Administrador':
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
        except Exception:
            pass

    # 4. Context Processor (Notificações Globais)
    @app.context_processor
    def inject_globals():
        try:
            config = Configuracao.query.first()
            if not config:
                try:
                    config = Configuracao(nome_sistema='SGO', sigla_orgao='UEMA')
                except Exception:
                    config = None

            notificacoes = Notificacao.query.order_by(Notificacao.created_at.desc()).limit(5).all()
            novas_count = len(notificacoes)
        except Exception:
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

    # ==========================================================================
    # 5. REGISTRO DE ROTAS E BLUEPRINTS
    # Nota: O blueprint 'admin' é importado diretamente de app.controllers.admin
    # para garantir o registro completo das rotas de lotações (/admin/lotacoes)
    # ==========================================================================
    from app.routes import bp_main, bp_auth, bp_oficios
    from app.controllers.admin import bp as bp_admin

    app.register_blueprint(bp_main)
    app.register_blueprint(bp_auth)
    app.register_blueprint(bp_admin, url_prefix='/admin')
    app.register_blueprint(bp_oficios)

    # 6. Tratamento de Erros HTTP
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        try:
            return render_template('errors/500.html'), 500
        except Exception:
            erro_html = """
            <div style="text-align:center; font-family:sans-serif; margin-top:10vh;">
                <h1 style="color:red;">Erro 500</h1>
                <p>Ocorreu um erro interno de processamento no servidor.</p>
                <a href="/">Voltar ao início</a>
            </div>
            """
            return erro_html, 500

    # 7. Inicialização Básica do Banco de Dados
    with app.app_context():
        try:
            db.create_all()
            create_default_admin()
        except Exception as e:
            print(f"Aviso ao inicializar tabelas: {e}")

    return app

def create_default_admin():
    """Cria o administrador padrão do sistema se não existir."""
    try:
        if not User.query.filter_by(email='admin@spark.com').first():
            print("--- Criando Administrador Padrão ---")
            admin = User(
                nome='Administrador Sistema',
                email='admin@spark.com',
                password='admin',
                perfil='Administrador',
                ativo=True
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Usuário Admin Padrão registrado.")
    except Exception as e:
        print(f"Aviso ao criar admin padrão: {e}")