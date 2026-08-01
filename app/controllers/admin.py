from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from functools import wraps
from app.models import db, User, Setor, Lotacao, TipoProcesso
from app.forms import UserForm, SetorForm, LotacaoForm, TipoProcessoForm, ConfiguracaoForm

# Cria o Blueprint (Módulo Administrativo)
bp = Blueprint('admin', __name__)

# ==============================================================================
# DECORATOR: CONTROLE DE ACESSO (Só Administradores Passam)
# ==============================================================================
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verifica se está logado E se possui perfil de Administrador
        if not current_user.is_authenticated or current_user.perfil != 'Administrador':
            flash('Acesso negado. Esta área é restrita a administradores do sistema.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

# ==============================================================================
# 1. GERENCIAMENTO DE USUÁRIOS (COM SEPARAÇÃO DE LOTAÇÃO E SETORES)
# ==============================================================================

@bp.route('/users')
@login_required
@admin_required
def users_list():
    """Lista todos os usuários cadastrados com suas respectivas lotações."""
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.nome).paginate(page=page, per_page=15)
    return render_template('admin/users_list.html', users=users)

@bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def user_create():
    """Cadastra um novo usuário, atribuindo lotação física e setores de trâmite."""
    form = UserForm()

    if form.validate_on_submit():
        user = User(
            nome=form.nome.data,
            email=form.email.data,
            perfil=form.perfil.data,
            ativo=form.ativo.data,
            lotacao_id=form.lotacao_id.data  # Associação da Lotação
        )
        
        # Na criação, a senha é tratada via setter (hash automático)
        if form.password.data:
            user.password = form.password.data

        # Associa os setores autorizados para tramitação
        if form.setores.data:
            user.setores_permitidos = Setor.query.filter(Setor.id.in_(form.setores.data)).all()

        db.session.add(user)
        db.session.commit()
        flash(f'Usuário {user.nome} criado com sucesso!', 'success')
        return redirect(url_for('admin.users_list'))

    return render_template('admin/users_form.html', form=form, title="Novo Usuário")

@bp.route('/users/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def user_edit(id):
    """Edita dados do usuário, sua lotação e seus setores autorizados."""
    user = User.query.get_or_404(id)
    form = UserForm(original_email=user.email, obj=user)

    if request.method == 'GET':
        form.setores.data = [s.id for s in user.setores_permitidos]
        if user.lotacao_id:
            form.lotacao_id.data = user.lotacao_id

    if form.validate_on_submit():
        user.nome = form.nome.data
        user.email = form.email.data
        user.perfil = form.perfil.data
        user.ativo = form.ativo.data
        user.lotacao_id = form.lotacao_id.data  # Atualiza Lotação de trabalho

        # Atualiza a lista de setores permitidos para tramitação
        user.setores_permitidos = Setor.query.filter(Setor.id.in_(form.setores.data)).all() if form.setores.data else []

        # Só altera a senha se o campo foi preenchido
        if form.password.data:
            user.password = form.password.data

        db.session.commit()
        flash('Dados do usuário atualizados com sucesso.', 'success')
        return redirect(url_for('admin.users_list'))

    return render_template('admin/users_form.html', form=form, title="Editar Usuário")

@bp.route('/users/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def user_delete(id):
    """Exclui um usuário com verificação de segurança."""
    user = User.query.get_or_404(id)

    # Proteção: Não permite excluir a si próprio
    if user.id == current_user.id:
        flash('Você não pode excluir seu próprio usuário enquanto está logado.', 'warning')
        return redirect(url_for('admin.users_list'))

    try:
        db.session.delete(user)
        db.session.commit()
        flash('Usuário removido com sucesso.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Não foi possível excluir o usuário pois ele possui históricos ou documentos vinculados.', 'danger')

    return redirect(url_for('admin.users_list'))

# ==============================================================================
# 2. GERENCIAMENTO DE LOTAÇÕES (NOVO MÓDULO)
# ==============================================================================

@bp.route('/lotacoes')
@login_required
@admin_required
def lotacoes_list():
    """Lista todas as Unidades de Lotação cadastradas."""
    lotacoes = Lotacao.query.order_by(Lotacao.sigla).all()
    return render_template('admin/lotacoes_list.html', lotacoes=lotacoes)

@bp.route('/lotacoes/new', methods=['GET', 'POST'])
@login_required
@admin_required
def lotacao_create():
    """Cadastra uma nova Lotação."""
    form = LotacaoForm()

    if form.validate_on_submit():
        lotacao = Lotacao(
            nome=form.nome.data,
            sigla=form.sigla.data.upper(),
            ativo=form.ativo.data
        )
        db.session.add(lotacao)
        db.session.commit()
        flash(f'Lotação {lotacao.sigla} cadastrada com sucesso!', 'success')
        return redirect(url_for('admin.lotacoes_list'))

    return render_template('admin/lotacoes_form.html', form=form, title="Nova Lotação")

@bp.route('/lotacoes/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def lotacao_edit(id):
    """Edita uma Lotação existente."""
    lotacao = Lotacao.query.get_or_404(id)
    form = LotacaoForm(original_sigla=lotacao.sigla, obj=lotacao)

    if form.validate_on_submit():
        lotacao.nome = form.nome.data
        lotacao.sigla = form.sigla.data.upper()
        lotacao.ativo = form.ativo.data

        db.session.commit()
        flash('Unidade de Lotação atualizada com sucesso.', 'success')
        return redirect(url_for('admin.lotacoes_list'))

    return render_template('admin/lotacoes_form.html', form=form, title="Editar Lotação")

@bp.route('/lotacoes/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def lotacao_delete(id):
    """Exclui uma Lotação se não houver servidores vinculados."""
    lotacao = Lotacao.query.get_or_404(id)

    if lotacao.servidores:
        flash(f'Erro: A lotação {lotacao.sigla} possui servidores vinculados. Realoque-os antes de excluir.', 'danger')
        return redirect(url_for('admin.lotacoes_list'))

    db.session.delete(lotacao)
    db.session.commit()
    flash('Lotação removida com sucesso.', 'success')
    return redirect(url_for('admin.lotacoes_list'))

# ==============================================================================
# 3. GERENCIAMENTO DE SETORES (TRAMITAÇÃO DE PROCESSOS)
# ==============================================================================

@bp.route('/setores')
@login_required
@admin_required
def setores_list():
    """Lista todos os setores por onde os processos tramitam."""
    setores = Setor.query.order_by(Setor.sigla).all()
    return render_template('admin/setores_list.html', setores=setores)

@bp.route('/setores/new', methods=['GET', 'POST'])
@login_required
@admin_required
def setor_create():
    """Cria novo setor de trâmite."""
    form = SetorForm()

    if form.validate_on_submit():
        setor = Setor(
            nome=form.nome.data,
            sigla=form.sigla.data.upper(),
            ativo=form.ativo.data
        )
        db.session.add(setor)
        db.session.commit()
        flash(f'Setor {setor.sigla} criado com sucesso!', 'success')
        return redirect(url_for('admin.setores_list'))

    return render_template('admin/setores_form.html', form=form, title="Novo Setor")

@bp.route('/setores/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def setor_edit(id):
    """Edita setor de trâmite."""
    setor = Setor.query.get_or_404(id)
    form = SetorForm(original_sigla=setor.sigla, obj=setor)

    if form.validate_on_submit():
        setor.nome = form.nome.data
        setor.sigla = form.sigla.data.upper()
        setor.ativo = form.ativo.data

        db.session.commit()
        flash('Setor atualizado com sucesso.', 'success')
        return redirect(url_for('admin.setores_list'))

    return render_template('admin/setores_form.html', form=form, title="Editar Setor")

@bp.route('/setores/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def setor_delete(id):
    """Exclui setor com verificação de integridade."""
    setor = Setor.query.get_or_404(id)

    if getattr(setor, 'oficios_locais', None) or getattr(setor, 'oficios_emitidos', None):
        flash(f'Erro: O setor {setor.sigla} possui ofícios vinculados e não pode ser excluído.', 'danger')
        return redirect(url_for('admin.setores_list'))

    db.session.delete(setor)
    db.session.commit()
    flash('Setor removido com sucesso.', 'success')
    return redirect(url_for('admin.setores_list'))

# ==============================================================================
# 4. GERENCIAMENTO DE TIPOS DE PROCESSO
# ==============================================================================

@bp.route('/tipos')
@login_required
@admin_required
def tipos_list():
    """Lista todos os tipos de processo."""
    tipos = TipoProcesso.query.order_by(TipoProcesso.nome).all()
    return render_template('admin/tipos_list.html', tipos=tipos)

@bp.route('/tipos/new', methods=['GET', 'POST'])
@login_required
@admin_required
def tipo_create():
    """Cria novo tipo de processo."""
    form = TipoProcessoForm()

    if form.validate_on_submit():
        tipo = TipoProcesso(
            nome=form.nome.data,
            descricao=form.descricao.data
        )
        db.session.add(tipo)
        db.session.commit()
        flash(f'Tipo "{tipo.nome}" criado com sucesso!', 'success')
        return redirect(url_for('admin.tipos_list'))

    return render_template('admin/tipos_form.html', form=form, title="Novo Tipo de Processo")

@bp.route('/tipos/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def tipo_edit(id):
    """Edita um tipo de processo."""
    tipo = TipoProcesso.query.get_or_404(id)
    form = TipoProcessoForm(original_nome=tipo.nome, obj=tipo)

    if form.validate_on_submit():
        tipo.nome = form.nome.data
        tipo.descricao = form.descricao.data

        db.session.commit()
        flash('Tipo atualizado com sucesso.', 'success')
        return redirect(url_for('admin.tipos_list'))

    return render_template('admin/tipos_form.html', form=form, title="Editar Tipo")

@bp.route('/tipos/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def tipo_delete(id):
    """Exclui um tipo de processo."""
    tipo = TipoProcesso.query.get_or_404(id)

    if getattr(tipo, 'oficios', None):
        flash(f'Erro: Existem ofícios vinculados ao tipo "{tipo.nome}". Não é possível excluir.', 'danger')
        return redirect(url_for('admin.tipos_list'))

    db.session.delete(tipo)
    db.session.commit()
    flash('Tipo removido com sucesso.', 'success')
    return redirect(url_for('admin.tipos_list'))

# ==============================================================================
# 5. CONFIGURAÇÕES DO SISTEMA
# ==============================================================================

@bp.route('/configuracoes', methods=['GET', 'POST'])
@login_required
@admin_required
def configuracoes():
    """Gerencia as configurações globais do sistema."""
    form = ConfiguracaoForm()

    if form.validate_on_submit():
        flash('Configurações salvas com sucesso!', 'success')
        return redirect(url_for('admin.configuracoes'))

    if request.method == 'GET':
        form.nome_sistema.data = "SGO"
        form.sigla_orgao.data = "UEMA"
        form.itens_por_pagina.data = 10
        form.nome_departamento.data = "Coordenação de Planejamento e Orçamento"

    return render_template('admin/settings.html', form=form)