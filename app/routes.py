from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func, or_, extract
from datetime import datetime, date

# ==============================================================================
# IMPORTAÇÃO DOS MODELOS E FORMULÁRIOS DA APLICAÇÃO
# ==============================================================================
from app.models import db, User, Setor, Lotacao, TipoProcesso, Oficio, Configuracao, Notificacao
from app.forms import (
    LoginForm, UserForm, PerfilForm, ConfiguracaoForm,
    SetorForm, LotacaoForm, TipoProcessoForm, OficioForm
)

# ==============================================================================
# DEFINIÇÃO DOS BLUEPRINTS PRINCIPAIS DA APLICAÇÃO
# ==============================================================================
bp_main = Blueprint('main', __name__)
bp_auth = Blueprint('auth', __name__, url_prefix='/auth')
bp_admin = Blueprint('admin', __name__, url_prefix='/admin')
bp_oficios = Blueprint('oficios', __name__, url_prefix='/oficios')

# ==============================================================================
# HELPER: CRIAR NOTIFICAÇÃO GLOBAL NO SISTEMA
# ==============================================================================
def criar_notificacao(mensagem, category='info', link=None):
    """
    Registra um evento de notificação no banco de dados para ser exibido
    no painel de alertas do usuário.
    """
    try:
        nova_notificacao = Notificacao(
            mensagem=mensagem,
            categoria=category,
            link=link,
            autor_id=current_user.id if current_user.is_authenticated else None
        )
        db.session.add(nova_notificacao)
        # O commit será executado pela rota chamadora para manter atomicidade
    except Exception as e:
        print(f"Erro ao registrar notificação no sistema: {e}")

# ==============================================================================
# CONTEXT PROCESSOR (INJEÇÃO DE VARIÁVEIS GLOBAIS EM TODOS OS TEMPLATES)
# ==============================================================================
@bp_main.app_context_processor
def inject_globals():
    """
    Injeta configurações de sistema, dados de rodapé e notificações
    em todas as requisições renderizadas por Jinja2.
    """
    # 1. Carrega configurações dinâmicas do banco de dados
    config = Configuracao.query.first()
    if not config:
        config = Configuracao(
            nome_sistema='SGO',
            sigla_orgao='UEMA',
            nome_departamento='Coordenação de Planejamento e Orçamento',
            logo_url='https://upload.wikimedia.org/wikipedia/commons/2/20/Bras%C3%A3o_UEMA.png'
        )

    # 2. Carrega notificações recentes para a barra superior
    try:
        notificacoes = Notificacao.query.order_by(Notificacao.created_at.desc()).limit(5).all()
        novas_count = len(notificacoes)
    except Exception as err_notif:
        print(f"Aviso: Não foi possível carregar notificações na navbar: {err_notif}")
        notificacoes = []
        novas_count = 0

    return dict(
        config_sistema=config,
        current_year=datetime.now().year,
        notificacoes_nav=notificacoes,
        notificacoes_count=novas_count,
        data_hora_atual=datetime.now()
    )

# ==============================================================================
# ROTAS: AUTENTICAÇÃO E SESSÃO (AUTH)
# ==============================================================================
@bp_auth.route('/login', methods=['GET', 'POST'])
def login():
    """
    Processa a autenticação de usuários e o controle de acesso por sessão.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.verify_password(form.password.data):
            if not user.ativo:
                flash('Sua conta se encontra inativa no momento. Contate o administrador do sistema.', 'danger')
                return render_template('auth/login.html', form=form)

            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash('Credenciais inválidas. Verifique seu e-mail corporativo e senha.', 'danger')

    return render_template('auth/login.html', form=form)

@bp_auth.route('/logout')
@login_required
def logout():
    """
    Encerra a sessão do usuário ativo com segurança.
    """
    logout_user()
    flash('Você encerrou sua sessão com sucesso.', 'info')
    return redirect(url_for('auth.login'))

# ==============================================================================
# ROTAS: DASHBOARD E PRINCIPAL (MAIN / PANORAMA GERAL)
# ==============================================================================
@bp_main.route('/')
@login_required
def index():
    """
    Painel Principal / Dashboard estatístico da aplicação.
    Aplica restrição de acesso baseada nos setores autorizados do usuário logado.
    """
    query_base = Oficio.query

    # Restrição para Usuário Padrão (Filtro por Setor Autorizado)
    if current_user.perfil != 'Administrador':
        allowed_ids = [s.id for s in current_user.setores_permitidos]
        query_base = query_base.filter(
            or_(
                Oficio.setor_emissor_id.in_(allowed_ids),
                Oficio.setor_atual_id.in_(allowed_ids)
            )
        )

    # Indicadores Chave de Desempenho (KPIs)
    total_oficios = query_base.count()
    total_andamento = query_base.filter_by(status='Em andamento').count()
    total_concluidos = query_base.filter_by(status='Concluído').count()

    hoje = date.today()
    inicio_mes = hoje.replace(day=1)
    total_mes = query_base.filter(Oficio.data_envio >= inicio_mes).count()

    # Agrupamento Estatístico por Tipo de Processo
    tipos_query = db.session.query(
        TipoProcesso.nome, 
        func.count(Oficio.id)
    ).join(Oficio, Oficio.tipo_processo_id == TipoProcesso.id)

    if current_user.perfil != 'Administrador':
        tipos_query = tipos_query.filter(
            or_(
                Oficio.setor_emissor_id.in_(allowed_ids),
                Oficio.setor_atual_id.in_(allowed_ids)
            )
        )

    tipos = tipos_query.group_by(TipoProcesso.nome).limit(5).all()

    chart_tipo = {
        'labels': [t[0] for t in tipos],
        'data': [t[1] for t in tipos]
    }

    # Gráfico de Evolução dos Últimos 6 Meses
    meses_labels = []
    meses_data = []
    nomes_meses = {
        1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
        7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
    }

    for i in range(5, -1, -1):
        mes_calc = hoje.month - i
        ano_calc = hoje.year
        if mes_calc <= 0:
            mes_calc += 12
            ano_calc -= 1
        meses_labels.append(nomes_meses[mes_calc])
        qtd = query_base.filter(
            extract('year', Oficio.data_envio) == ano_calc,
            extract('month', Oficio.data_envio) == mes_calc
        ).count()
        meses_data.append(qtd)

    chart_mes = {
        'labels': meses_labels,
        'data': meses_data
    }

    return render_template(
        'dashboard/index.html',
        total_oficios=total_oficios,
        total_andamento=total_andamento,
        total_concluidos=total_concluidos,
        total_mes=total_mes,
        chart_tipo=chart_tipo,
        chart_mes=chart_mes
    )

@bp_main.route('/meus-dados', methods=['GET', 'POST'])
@login_required
def meus_dados():
    """
    Permite ao usuário consultar e atualizar seus próprios dados de cadastro/senha.
    """
    form = PerfilForm(obj=current_user)
    if form.validate_on_submit():
        current_user.nome = form.nome.data
        current_user.email = form.email.data
        if form.password.data:
            current_user.password = form.password.data
        db.session.commit()
        flash('Seus dados cadastrais foram atualizados com sucesso.', 'success')
        return redirect(url_for('main.meus_dados'))
    return render_template('users/meus_dados.html', form=form)

@bp_main.route('/relatorios/geral')
@login_required
def relatorio_geral():
    """
    Gera listagem detalhada e estatísticas dos ofícios para emissão de relatórios.
    """
    search = request.args.get('search')
    status = request.args.get('status')
    setor_atual_id = request.args.get('setor_atual_id')

    query = Oficio.query

    if current_user.perfil != 'Administrador':
        allowed_ids = [s.id for s in current_user.setores_permitidos]
        query = query.filter(
            or_(
                Oficio.setor_emissor_id.in_(allowed_ids),
                Oficio.setor_atual_id.in_(allowed_ids)
            )
        )

    if search:
        termo = f"%{search}%"
        query = query.filter(
            or_(
                Oficio.numero_oficio.ilike(termo),
                Oficio.processo_sei.ilike(termo),
                Oficio.titulo.ilike(termo)
            )
        )

    if status and status != "":
        query = query.filter_by(status=status)

    if setor_atual_id and setor_atual_id != "":
        query = query.filter_by(setor_atual_id=int(setor_atual_id))

    oficios = query.order_by(Oficio.data_envio.desc()).all()
    total_oficios = len(oficios)

    stats_dict = {}
    for o in oficios:
        stats_dict[o.status] = stats_dict.get(o.status, 0) + 1
    stats_status = [(k, v) for k, v in stats_dict.items()]

    config = Configuracao.query.first()

    return render_template(
        'relatorios/geral.html',
        oficios=oficios,
        stats_status=stats_status,
        total_oficios=total_oficios,
        data_geracao=datetime.now(),
        config=config
    )

# ==============================================================================
# ROTAS: ADMINISTRAÇÃO (GERENCIAMENTO DE USUÁRIOS, LOTAÇÃO E CONFIGURAÇÕES)
# ==============================================================================
@bp_admin.route('/configuracoes', methods=['GET', 'POST'])
@login_required
def configuracoes():
    """
    Gerencia parâmetros e variáveis globais do sistema.
    """
    if current_user.perfil != 'Administrador':
        flash('Acesso não autorizado a esta funcionalidade.', 'danger')
        return redirect(url_for('main.index'))

    config = Configuracao.query.first()
    if not config:
        config = Configuracao()
        db.session.add(config)
        db.session.commit()

    form = ConfiguracaoForm(obj=config)
    if form.validate_on_submit():
        form.populate_obj(config)
        config.modo_manutencao = form.modo_manutencao.data
        db.session.commit()
        flash('Parâmetros de configuração atualizados com sucesso!', 'success')
        return redirect(url_for('admin.configuracoes'))

    return render_template('admin/settings.html', form=form)

@bp_admin.route('/usuarios')
@login_required
def users_list():
    """
    Lista todos os usuários com suporte a paginação e exibição de lotação.
    """
    if current_user.perfil != 'Administrador':
        flash('Acesso restrito ao perfil de Administrador.', 'danger')
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.nome).paginate(page=page, per_page=10)
    return render_template('admin/users_list.html', users=users)

@bp_admin.route('/usuarios/novo', methods=['GET', 'POST'])
@login_required
def user_create():
    """
    Cadastra um novo usuário, atribuindo Lotação Oficial e Setores Autorizados.
    """
    if current_user.perfil != 'Administrador':
        return redirect(url_for('main.index'))

    form = UserForm()
    if form.validate_on_submit():
        user = User(
            nome=form.nome.data,
            email=form.email.data,
            password=form.password.data if form.password.data else 'mudar123',
            perfil=form.perfil.data,
            ativo=form.ativo.data,
            lotacao_id=form.lotacao_id.data  # Define Lotação Oficial de Trabalho
        )

        if form.setores.data:
            user.setores_permitidos = Setor.query.filter(Setor.id.in_(form.setores.data)).all()

        db.session.add(user)
        criar_notificacao(f"Novo usuário cadastrado: {user.nome}", "success", url_for('admin.users_list'))
        db.session.commit()
        flash(f'Usuário {user.nome} cadastrado com sucesso!', 'success')
        return redirect(url_for('admin.users_list'))

    return render_template('admin/users_form.html', form=form, title="Novo Usuário")

@bp_admin.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def user_edit(id):
    """
    Edita dados cadastrais, Lotação e permissões de trâmite do usuário.
    """
    if current_user.perfil != 'Administrador':
        return redirect(url_for('main.index'))

    user = User.query.get_or_404(id)
    form = UserForm(obj=user, original_email=user.email)

    if request.method == 'GET':
        form.setores.data = [s.id for s in user.setores_permitidos]
        if user.lotacao_id:
            form.lotacao_id.data = user.lotacao_id

    form.password.validators = []
    form.confirm_password.validators = []

    if form.validate_on_submit():
        user.nome = form.nome.data
        user.email = form.email.data
        user.perfil = form.perfil.data
        user.ativo = form.ativo.data
        user.lotacao_id = form.lotacao_id.data  # Atualiza Lotação Oficial de Trabalho

        user.setores_permitidos = Setor.query.filter(Setor.id.in_(form.setores.data)).all() if form.setores.data else []

        if form.password.data:
            user.password = form.password.data

        db.session.commit()
        flash('Cadastro de usuário atualizado com sucesso!', 'success')
        return redirect(url_for('admin.users_list'))

    return render_template('admin/users_form.html', form=form, title="Editar Usuário")

@bp_admin.route('/usuarios/excluir/<int:id>', methods=['POST'])
@login_required
def user_delete(id):
    """
    Remove o cadastro de um usuário com travas de segurança.
    """
    if current_user.perfil != 'Administrador':
        return redirect(url_for('main.index'))

    user = User.query.get_or_404(id)

    if user.id == current_user.id:
        flash('Operação negada: Não é possível remover sua própria conta.', 'danger')
        return redirect(url_for('admin.users_list'))

    try:
        db.session.delete(user)
        db.session.commit()
        flash(f'Usuário {user.nome} excluído do sistema.', 'success')
    except Exception as err:
        db.session.rollback()
        flash('Incapaz de excluir usuário com registros ou documentos vinculados. Recomendamos inativá-lo.', 'warning')
        print(f"Erro ao deletar usuário: {err}")

    return redirect(url_for('admin.users_list'))

# ==============================================================================
# ROTAS: OFÍCIOS (TRAMITAÇÃO DE PROCESSOS)
# ==============================================================================
@bp_oficios.route('/')
@login_required
def list():
    """
    Listagem principal de ofícios em trâmite com filtros avançados.
    """
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search')
    status = request.args.get('status')
    setor_atual_id = request.args.get('setor_atual_id')

    query = Oficio.query

    if current_user.perfil != 'Administrador':
        allowed_ids = [s.id for s in current_user.setores_permitidos]
        query = query.filter(
            or_(
                Oficio.setor_emissor_id.in_(allowed_ids),
                Oficio.setor_atual_id.in_(allowed_ids)
            )
        )

    if search:
        termo = f"%{search}%"
        query = query.filter(
            or_(
                Oficio.numero_oficio.ilike(termo),
                Oficio.processo_sei.ilike(termo),
                Oficio.titulo.ilike(termo)
            )
        )

    if status and status != "":
        query = query.filter_by(status=status)

    if setor_atual_id and setor_atual_id != "":
        query = query.filter_by(setor_atual_id=int(setor_atual_id))

    query = query.order_by(Oficio.data_envio.desc())
    oficios = query.paginate(page=page, per_page=10)
    setores = Setor.query.filter_by(ativo=True).all()

    return render_template('oficios/list.html', oficios=oficios, setores=setores)

@bp_oficios.route('/novo', methods=['GET', 'POST'])
@login_required
def create():
    """
    Registra um novo Ofício / Processo no fluxo institucional.
    """
    form = OficioForm()
    if form.validate_on_submit():
        oficio = Oficio(
            numero_oficio=form.numero_oficio.data,
            processo_sei=form.processo_sei.data,
            titulo=form.titulo.data,
            objeto_detalhado=form.objeto_detalhado.data,
            quem_assinou=form.quem_assinou.data,
            data_envio=form.data_envio.data,
            tipo_processo_id=form.tipo_processo_id.data,
            setor_emissor_id=form.setor_emissor_id.data,
            setor_atual_id=form.setor_atual_id.data,
            data_recebimento=form.data_recebimento.data,
            hora_recebimento=form.hora_recebimento.data,
            status=form.status.data,
            acao_tomada=form.acao_tomada.data,
            criador_id=current_user.id
        )
        db.session.add(oficio)
        criar_notificacao(f"Novo Ofício Cadastrado: {oficio.numero_oficio}", "info", url_for('oficios.list'))
        db.session.commit()
        flash(f'Ofício {oficio.numero_oficio} registrado com sucesso!', 'success')
        return redirect(url_for('oficios.list'))

    return render_template('oficios/form.html', form=form, oficio=None)

@bp_oficios.route('/view/<int:id>', methods=['GET'])
@login_required
def view(id):
    """
    Visualiza os detalhes do trâmite do Ofício.
    """
    oficio = Oficio.query.get_or_404(id)
    return render_template('oficios/view.html', oficio=oficio)

@bp_oficios.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    """
    Atualiza status e setor de tramitação de um ofício existente.
    """
    oficio = Oficio.query.get_or_404(id)
    if current_user.perfil != 'Administrador' and oficio.criador_id != current_user.id:
        flash('Você não tem permissão para alterar este documento.', 'danger')
        return redirect(url_for('oficios.list'))

    local_antigo = oficio.setor_atual_id
    form = OficioForm(obj=oficio, original_numero=oficio.numero_oficio)

    if form.validate_on_submit():
        form.populate_obj(oficio)
        oficio.acao_tomada = form.acao_tomada.data
        oficio.status = form.status.data
        oficio.setor_atual_id = form.setor_atual_id.data
        oficio.data_recebimento = form.data_recebimento.data
        oficio.hora_recebimento = form.hora_recebimento.data

        if local_antigo != oficio.setor_atual_id:
            setor_novo = Setor.query.get(oficio.setor_atual_id)
            sigla = setor_novo.sigla if setor_novo else 'N/A'
            criar_notificacao(f"Ofício {oficio.numero_oficio} movido para {sigla}", "warning", url_for('oficios.list'))
        else:
            criar_notificacao(f"Ofício {oficio.numero_oficio} atualizado.", "info", url_for('oficios.list'))

        db.session.commit()
        flash('Ofício atualizado com sucesso!', 'success')
        return redirect(url_for('oficios.list'))

    return render_template('oficios/form.html', form=form, oficio=oficio)

@bp_oficios.route('/excluir/<int:id>', methods=['POST'])
@login_required
def delete(id):
    """
    Exclui um registro de ofício do banco de dados.
    """
    oficio = Oficio.query.get_or_404(id)

    if current_user.perfil != 'Administrador' and oficio.criador_id != current_user.id:
        flash('Você não possui autorização para remover este documento.', 'danger')
        return redirect(url_for('oficios.list'))

    try:
        db.session.delete(oficio)
        criar_notificacao(f"Ofício {oficio.numero_oficio} removido do sistema.", "danger", url_for('oficios.list'))
        db.session.commit()
        flash('Ofício excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Falha ao tentar excluir o registro de ofício.', 'danger')

    return redirect(url_for('oficios.list'))