from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func, or_, extract
from datetime import datetime, date

# Importação dos objetos do app
from app.models import db, User, Setor, TipoProcesso, Oficio, Configuracao, Notificacao
from app.forms import (
    LoginForm, UserForm, PerfilForm, ConfiguracaoForm, 
    SetorForm, TipoProcessoForm, OficioForm
)

# Definição dos Blueprints
bp_main = Blueprint('main', __name__)
bp_auth = Blueprint('auth', __name__, url_prefix='/auth')
bp_admin = Blueprint('admin', __name__, url_prefix='/admin')
bp_oficios = Blueprint('oficios', __name__, url_prefix='/oficios')

# ==============================================================================
# HELPER: CRIAR NOTIFICAÇÃO
# ==============================================================================
def criar_notificacao(mensagem, category='info', link=None):
    """Cria uma notificação global no sistema."""
    try:
        nova_notificacao = Notificacao(
            mensagem=mensagem,
            categoria=category,
            link=link,
            autor_id=current_user.id if current_user.is_authenticated else None
        )
        db.session.add(nova_notificacao)
        # O commit deve ser feito pela rota que chamou esta função
    except Exception as e:
        print(f"Erro ao criar notificação: {e}")

# ==============================================================================
# CONTEXT PROCESSOR
# ==============================================================================
@bp_main.app_context_processor
def inject_globals():
    # 1. Configurações
    config = Configuracao.query.first()
    if not config:
        config = Configuracao(
            nome_sistema='SparkManagerDocs',
            sigla_orgao='UEMA',
            logo_url='https://upload.wikimedia.org/wikipedia/commons/2/20/Bras%C3%A3o_UEMA.png'
        )
    
    # 2. Notificações
    try:
        notificacoes = Notificacao.query.order_by(Notificacao.created_at.desc()).limit(5).all()
        novas_count = len(notificacoes)
    except:
        notificacoes = []
        novas_count = 0
    
    return dict(
        config_sistema=config,
        current_year=datetime.now().year,
        notificacoes_nav=notificacoes,
        notificacoes_count=novas_count
    )

# ==============================================================================
# ROTAS: AUTENTICAÇÃO (AUTH)
# ==============================================================================
@bp_auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.verify_password(form.password.data):
            if not user.ativo:
                flash('Sua conta está inativa. Contate o administrador.', 'danger')
                return render_template('auth/login.html', form=form)
            
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash('E-mail ou senha incorretos.', 'danger')
    
    return render_template('auth/login.html', form=form)

@bp_auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('auth.login'))

# ==============================================================================
# ROTAS: PRINCIPAL (MAIN / DASHBOARD)
# ==============================================================================
@bp_main.route('/')
@login_required
def index():
    # ADIÇÃO: Filtro base de segurança para o Dashboard (Restringir por Setor)
    query_base = Oficio.query
    if current_user.perfil != 'Administrador':
        allowed_ids = [s.id for s in current_user.setores_permitidos]
        query_base = query_base.filter(or_(Oficio.setor_emissor_id.in_(allowed_ids), Oficio.setor_atual_id.in_(allowed_ids)))

    # Estatísticas
    total_oficios = query_base.count()
    total_andamento = query_base.filter_by(status='Em andamento').count()
    total_concluidos = query_base.filter_by(status='Concluído').count()
    
    # Ofícios deste mês
    hoje = date.today()
    inicio_mes = hoje.replace(day=1)
    total_mes = query_base.filter(Oficio.data_envio >= inicio_mes).count()
    
    # Gráfico por Tipo
    tipos_query = db.session.query(TipoProcesso.nome, func.count(Oficio.id))\
        .join(Oficio, Oficio.tipo_processo_id == TipoProcesso.id)
    
    # Aplicar o mesmo filtro de segurança no Gráfico
    if current_user.perfil != 'Administrador':
        tipos_query = tipos_query.filter(or_(Oficio.setor_emissor_id.in_(allowed_ids), Oficio.setor_atual_id.in_(allowed_ids)))
        
    tipos = tipos_query.group_by(TipoProcesso.nome).limit(5).all()
        
    chart_tipo = {
        'labels': [t[0] for t in tipos],
        'data': [t[1] for t in tipos]
    }
    
    # Gráfico Evolução Mensal (Últimos 6 meses REAIS)
    meses_labels = []
    meses_data = []
    nomes_meses = {1:'Jan', 2:'Fev', 3:'Mar', 4:'Abr', 5:'Mai', 6:'Jun', 
                  7:'Jul', 8:'Ago', 9:'Set', 10:'Out', 11:'Nov', 12:'Dez'}

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

    return render_template('dashboard/index.html',
                           total_oficios=total_oficios,
                           total_andamento=total_andamento,
                           total_concluidos=total_concluidos,
                           total_mes=total_mes,
                           chart_tipo=chart_tipo,
                           chart_mes=chart_mes)

@bp_main.route('/meus-dados', methods=['GET', 'POST'])
@login_required
def meus_dados():
    form = PerfilForm(obj=current_user)
    if form.validate_on_submit():
        current_user.nome = form.nome.data
        current_user.email = form.email.data
        if form.password.data:
            current_user.password = form.password.data
        db.session.commit()
        flash('Seus dados foram atualizados com sucesso.', 'success')
        return redirect(url_for('main.meus_dados'))
    return render_template('users/meus_dados.html', form=form)

@bp_main.route('/relatorios/geral')
@login_required
def relatorio_geral():
    # Captura os filtros da URL
    search = request.args.get('search')
    status = request.args.get('status')
    setor_atual_id = request.args.get('setor_atual_id')

    # Inicia a query base
    query = Oficio.query

    # ADIÇÃO: Segurança - Limitar escopo do relatório aos setores autorizados
    if current_user.perfil != 'Administrador':
        allowed_ids = [s.id for s in current_user.setores_permitidos]
        query = query.filter(or_(Oficio.setor_emissor_id.in_(allowed_ids), Oficio.setor_atual_id.in_(allowed_ids)))

    # Aplica os filtros
    if search:
        termo = f"%{search}%"
        query = query.filter(or_(
            Oficio.numero_oficio.ilike(termo),
            Oficio.processo_sei.ilike(termo),
            Oficio.titulo.ilike(termo)
        ))
    
    if status and status != "":
        query = query.filter_by(status=status)
    
    if setor_atual_id and setor_atual_id != "":
        query = query.filter_by(setor_atual_id=int(setor_atual_id))

    # Ordenação e Execução
    oficios = query.order_by(Oficio.data_envio.desc()).all()
    
    # Recalcula estatísticas baseadas apenas nos dados filtrados
    total_oficios = len(oficios)
    
    # Pequena lógica manual para contar status dos filtrados
    stats_dict = {}
    for o in oficios:
        stats_dict[o.status] = stats_dict.get(o.status, 0) + 1
    stats_status = [(k, v) for k, v in stats_dict.items()]

    config = Configuracao.query.first()
    
    return render_template('relatorios/geral.html', 
                           oficios=oficios, 
                           stats_status=stats_status, 
                           total_oficios=total_oficios, 
                           data_geracao=datetime.now(), 
                           config=config)

# ==============================================================================
# ROTAS: ADMINISTRAÇÃO (ADMIN)
# ==============================================================================
@bp_admin.route('/configuracoes', methods=['GET', 'POST'])
@login_required
def configuracoes():
    if current_user.perfil != 'Administrador':
        flash('Acesso não autorizado.', 'danger')
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
        flash('Configurações atualizadas!', 'success')
        return redirect(url_for('admin.configuracoes'))
    return render_template('admin/settings.html', form=form)

# --- Gestão de Usuários ---

@bp_admin.route('/usuarios')
@login_required
def users_list():
    if current_user.perfil != 'Administrador': return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(page=page, per_page=10)
    return render_template('admin/users_list.html', users=users)

@bp_admin.route('/usuarios/novo', methods=['GET', 'POST'])
@login_required
def user_create():
    if current_user.perfil != 'Administrador': return redirect(url_for('main.index'))
    form = UserForm()
    if form.validate_on_submit():
        user = User(nome=form.nome.data, email=form.email.data, 
                   password=form.password.data if form.password.data else 'mudar123',
                   perfil=form.perfil.data, ativo=form.ativo.data)
        
        # ADIÇÃO: Ligar os setores selecionados ao novo usuário
        if form.setores.data:
            user.setores_permitidos = Setor.query.filter(Setor.id.in_(form.setores.data)).all()
            
        db.session.add(user)
        criar_notificacao(f"Novo usuário: {user.nome}", "success", url_for('admin.users_list'))
        db.session.commit()
        flash('Usuário criado!', 'success')
        return redirect(url_for('admin.users_list'))
    return render_template('admin/users_form.html', form=form, title="Novo Usuário")

@bp_admin.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def user_edit(id):
    if current_user.perfil != 'Administrador': return redirect(url_for('main.index'))
    user = User.query.get_or_404(id)
    form = UserForm(obj=user, original_email=user.email)
    
    # ADIÇÃO: Preencher os checkboxes no carregamento da página com os setores que ele já tem
    if request.method == 'GET':
        form.setores.data = [s.id for s in user.setores_permitidos]
    
    # Remove validação de senha obrigatória na edição
    form.password.validators = [] 
    form.confirm_password.validators = []

    if form.validate_on_submit():
        user.nome = form.nome.data
        user.email = form.email.data
        user.perfil = form.perfil.data
        user.ativo = form.ativo.data
        
        # ADIÇÃO: Atualizar a lista de setores permitidos do usuário
        user.setores_permitidos = Setor.query.filter(Setor.id.in_(form.setores.data)).all() if form.setores.data else []
        
        if form.password.data:
            user.password = form.password.data
        
        db.session.commit()
        flash('Usuário atualizado!', 'success')
        return redirect(url_for('admin.users_list'))
    return render_template('admin/users_form.html', form=form, title="Editar Usuário")

# --- CORREÇÃO SOLICITADA: EXCLUSÃO DE USUÁRIOS COM SEGURANÇA ---
@bp_admin.route('/usuarios/excluir/<int:id>', methods=['POST'])
@login_required
def user_delete(id):
    # Verificação de poder: Apenas Administradores podem excluir
    if current_user.perfil != 'Administrador': 
        return redirect(url_for('main.index'))
        
    user = User.query.get_or_404(id)
    
    # Trava de Segurança: Administrador não pode excluir a si próprio
    if user.id == current_user.id:
        flash('Você não pode excluir sua própria conta por segurança.', 'danger')
        return redirect(url_for('admin.users_list'))
    
    try:
        # Tenta deletar fisicamente o usuário
        db.session.delete(user)
        db.session.commit()
        flash(f'Usuário {user.nome} removido com sucesso.', 'success')
    except Exception as e:
        # Tratamento do erro de integridade (ofícios ou notas vinculadas)
        db.session.rollback()
        flash('Não é possível excluir este usuário pois ele possui documentos vinculados (Ofícios ou Notas). Sugerimos apenas DESATIVAR o usuário.', 'warning')
        print(f"Erro ao excluir usuário: {e}")
        
    return redirect(url_for('admin.users_list'))

# --- Gestão de Setores ---

@bp_admin.route('/setores')
@login_required
def setores_list():
    setores = Setor.query.all()
    return render_template('admin/setores_list.html', setores=setores)

@bp_admin.route('/setores/novo', methods=['GET', 'POST'])
@login_required
def setor_create():
    form = SetorForm()
    if form.validate_on_submit():
        setor = Setor(nome=form.nome.data, sigla=form.sigla.data.upper(), ativo=form.ativo.data)
        db.session.add(setor)
        db.session.commit()
        flash('Setor cadastrado!', 'success')
        return redirect(url_for('admin.setores_list'))
    return render_template('admin/setores_form.html', form=form, title="Novo Setor")

@bp_admin.route('/setores/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def setor_edit(id):
    setor = Setor.query.get_or_404(id)
    form = SetorForm(obj=setor, original_sigla=setor.sigla)
    if form.validate_on_submit():
        setor.nome = form.nome.data
        setor.sigla = form.sigla.data.upper()
        setor.ativo = form.ativo.data
        db.session.commit()
        flash('Setor atualizado!', 'success')
        return redirect(url_for('admin.setores_list'))
    return render_template('admin/setores_form.html', form=form, title="Editar Setor")

@bp_admin.route('/setores/excluir/<int:id>', methods=['POST'])
@login_required
def setor_delete(id):
    if current_user.perfil != 'Administrador': return redirect(url_for('main.index'))
    setor = Setor.query.get_or_404(id)
    try:
        db.session.delete(setor)
        db.session.commit()
        flash('Setor excluído.', 'success')
    except:
        db.session.rollback()
        flash('Erro: Não é possível excluir setor com ofícios vinculados.', 'danger')
    return redirect(url_for('admin.setores_list'))

# --- Gestão de Tipos de Processo ---

@bp_admin.route('/tipos')
@login_required
def tipos_list():
    tipos = TipoProcesso.query.all()
    return render_template('admin/tipos_list.html', tipos=tipos)

@bp_admin.route('/tipos/novo', methods=['GET', 'POST'])
@login_required
def tipo_create():
    form = TipoProcessoForm()
    if form.validate_on_submit():
        tipo = TipoProcesso(nome=form.nome.data, descricao=form.descricao.data)
        db.session.add(tipo)
        db.session.commit()
        flash('Tipo cadastrado!', 'success')
        return redirect(url_for('admin.tipos_list'))
    return render_template('admin/tipos_form.html', form=form, title="Novo Tipo")

@bp_admin.route('/tipos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def tipo_edit(id):
    tipo = TipoProcesso.query.get_or_404(id)
    form = TipoProcessoForm(obj=tipo, original_nome=tipo.nome)
    if form.validate_on_submit():
        tipo.nome = form.nome.data
        tipo.descricao = form.descricao.data
        db.session.commit()
        flash('Tipo atualizado!', 'success')
        return redirect(url_for('admin.tipos_list'))
    return render_template('admin/tipos_form.html', form=form, title="Editar Tipo")

@bp_admin.route('/tipos/excluir/<int:id>', methods=['POST'])
@login_required
def tipo_delete(id):
    if current_user.perfil != 'Administrador': return redirect(url_for('main.index'))
    tipo = TipoProcesso.query.get_or_404(id)
    try:
        db.session.delete(tipo)
        db.session.commit()
        flash('Tipo de processo excluído.', 'success')
    except:
        db.session.rollback()
        flash('Erro: Existem ofícios vinculados a este tipo.', 'danger')
    return redirect(url_for('admin.tipos_list'))

# ==============================================================================
# ROTAS: OFÍCIOS (CORE)
# ==============================================================================
@bp_oficios.route('/')
@login_required
def list():
    # 1. Capturar parâmetros da URL
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search')
    status = request.args.get('status')
    setor_atual_id = request.args.get('setor_atual_id')

    # 2. Iniciar Query
    query = Oficio.query

    # ADIÇÃO: Segurança - Limitar a lista de ofícios na tabela principal
    if current_user.perfil != 'Administrador':
        allowed_ids = [s.id for s in current_user.setores_permitidos]
        query = query.filter(or_(Oficio.setor_emissor_id.in_(allowed_ids), Oficio.setor_atual_id.in_(allowed_ids)))

    # 3. Aplicar Filtros
    if search:
        termo = f"%{search}%"
        query = query.filter(or_(
            Oficio.numero_oficio.ilike(termo),
            Oficio.processo_sei.ilike(termo),
            Oficio.titulo.ilike(termo)
        ))
    
    if status and status != "":
        query = query.filter_by(status=status)
    
    if setor_atual_id and setor_atual_id != "":
        query = query.filter_by(setor_atual_id=int(setor_atual_id))

    # 4. Ordenação
    query = query.order_by(Oficio.data_envio.desc())

    # 5. Paginação
    oficios = query.paginate(page=page, per_page=10)
    setores = Setor.query.filter_by(ativo=True).all()
    
    return render_template('oficios/list.html', oficios=oficios, setores=setores)

@bp_oficios.route('/novo', methods=['GET', 'POST'])
@login_required
def create():
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
        criar_notificacao(f"Novo Ofício: {oficio.numero_oficio}", "info", url_for('oficios.list'))
        db.session.commit()
        flash(f'Ofício {oficio.numero_oficio} cadastrado!', 'success')
        return redirect(url_for('oficios.list'))
    return render_template('oficios/form.html', form=form, oficio=None)

# --- ROTA DE VISUALIZAÇÃO DE OFÍCIO ---
@bp_oficios.route('/view/<int:id>', methods=['GET'])
@login_required
def view(id):
    oficio = Oficio.query.get_or_404(id)
    return render_template('oficios/view.html', oficio=oficio)

@bp_oficios.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    oficio = Oficio.query.get_or_404(id)
    if current_user.perfil != 'Administrador' and oficio.criador_id != current_user.id:
        flash('Permissão negada.', 'danger')
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
            criar_notificacao(f"Ofício {oficio.numero_oficio} movido p/ {sigla}", "warning", url_for('oficios.list'))
        else:
            criar_notificacao(f"Ofício {oficio.numero_oficio} atualizado.", "info", url_for('oficios.list'))
        
        db.session.commit()
        flash('Ofício atualizado!', 'success')
        return redirect(url_for('oficios.list'))
    return render_template('oficios/form.html', form=form, oficio=oficio)

# --- ROTA DE EXCLUSÃO DE OFÍCIO (ADICIONADA) ---
@bp_oficios.route('/excluir/<int:id>', methods=['POST'])
@login_required
def delete(id):
    oficio = Oficio.query.get_or_404(id)
    
    # Segurança: Apenas o criador ou Administradores podem excluir
    if current_user.perfil != 'Administrador' and oficio.criador_id != current_user.id:
        flash('Você não tem permissão para excluir este ofício.', 'danger')
        return redirect(url_for('oficios.list'))
    
    try:
        db.session.delete(oficio)
        criar_notificacao(f"Ofício {oficio.numero_oficio} excluído.", "danger", url_for('oficios.list'))
        db.session.commit()
        flash('Ofício excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao tentar excluir o ofício.', 'danger')
        print(f"Erro ao excluir: {e}")
        
    return redirect(url_for('oficios.list'))