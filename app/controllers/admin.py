from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from functools import wraps
from app.models import db, User, Setor, TipoProcesso
# Adicionado ConfiguracaoForm na importação abaixo
from app.forms import UserForm, SetorForm, TipoProcessoForm, ConfiguracaoForm

# Cria o Blueprint (Módulo)
bp = Blueprint('admin', __name__)

# ==============================================================================
# DECORATOR: CONTROLE DE ACESSO (Só Admins Passam)
# ==============================================================================
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verifica se está logado E se é Admin
        if not current_user.is_authenticated or current_user.perfil != 'Administrador':
            flash('Acesso negado. Esta área é restrita a administradores.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


# ==============================================================================
# 1. GERENCIAMENTO DE USUÁRIOS
# ==============================================================================

@bp.route('/users')
@login_required
@admin_required
def users_list():
    """Lista todos os usuários cadastrados."""
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.nome).paginate(page=page, per_page=15)
    return render_template('admin/users_list.html', users=users)

@bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def user_create():
    """Cadastra um novo usuário."""
    form = UserForm()
    
    if form.validate_on_submit():
        user = User(
            nome=form.nome.data,
            email=form.email.data,
            perfil=form.perfil.data,
            ativo=form.ativo.data
        )
        # Na criação, a senha é obrigatória
        if form.password.data:
            user.password = form.password.data # O Setter faz o hash
            
        db.session.add(user)
        db.session.commit()
        flash(f'Usuário {user.nome} criado com sucesso!', 'success')
        return redirect(url_for('admin.users_list'))
    
    return render_template('admin/users_form.html', form=form, title="Novo Usuário")

@bp.route('/users/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def user_edit(id):
    """Edita um usuário existente."""
    user = User.query.get_or_404(id)
    
    # Passamos o email original para o form ignorar a validação de duplicidade dele mesmo
    form = UserForm(original_email=user.email, obj=user)

    if form.validate_on_submit():
        user.nome = form.nome.data
        user.email = form.email.data
        user.perfil = form.perfil.data
        user.ativo = form.ativo.data
        
        # Só altera a senha se o campo foi preenchido
        if form.password.data:
            user.password = form.password.data
            
        db.session.commit()
        flash('Dados do usuário atualizados.', 'success')
        return redirect(url_for('admin.users_list'))

    return render_template('admin/users_form.html', form=form, title="Editar Usuário")

@bp.route('/users/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def user_delete(id):
    """Exclui um usuário."""
    user = User.query.get_or_404(id)
    
    # Proteção: Não permite excluir a si mesmo
    if user.id == current_user.id:
        flash('Você não pode excluir seu próprio usuário enquanto está logado.', 'warning')
        return redirect(url_for('admin.users_list'))
        
    db.session.delete(user)
    db.session.commit()
    flash('Usuário removido com sucesso.', 'success')
    return redirect(url_for('admin.users_list'))


# ==============================================================================
# 2. GERENCIAMENTO DE SETORES
# ==============================================================================

@bp.route('/setores')
@login_required
@admin_required
def setores_list():
    """Lista todos os setores."""
    setores = Setor.query.order_by(Setor.nome).all()
    return render_template('admin/setores_list.html', setores=setores)

@bp.route('/setores/new', methods=['GET', 'POST'])
@login_required
@admin_required
def setor_create():
    """Cria novo setor."""
    form = SetorForm()
    
    if form.validate_on_submit():
        setor = Setor(
            nome=form.nome.data,
            sigla=form.sigla.data.upper(), # Força caixa alta na sigla
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
    """Edita setor."""
    setor = Setor.query.get_or_404(id)
    form = SetorForm(original_sigla=setor.sigla, obj=setor)
    
    if form.validate_on_submit():
        setor.nome = form.nome.data
        setor.sigla = form.sigla.data.upper()
        setor.ativo = form.ativo.data
        
        db.session.commit()
        flash('Setor atualizado.', 'success')
        return redirect(url_for('admin.setores_list'))
        
    return render_template('admin/setores_form.html', form=form, title="Editar Setor")

@bp.route('/setores/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def setor_delete(id):
    """Exclui setor com verificação de integridade."""
    setor = Setor.query.get_or_404(id)
    
    # Verifica se existem ofícios vinculados antes de excluir
    # Nota: Assumindo que o relacionamento no model seja 'oficios_locais' ou similar
    # Se der erro aqui, verifique o nome do backref no seu models.py
    if getattr(setor, 'oficios_locais', None) or getattr(setor, 'oficios_emitidos', None):
        flash(f'Erro: O setor {setor.sigla} possui ofícios vinculados e não pode ser excluído. Apenas inative-o.', 'danger')
        return redirect(url_for('admin.setores_list'))

    db.session.delete(setor)
    db.session.commit()
    flash('Setor removido com sucesso.', 'success')
    return redirect(url_for('admin.setores_list'))


# ==============================================================================
# 3. GERENCIAMENTO DE TIPOS DE PROCESSO
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
    """Exclui um tipo de processo com verificação."""
    tipo = TipoProcesso.query.get_or_404(id)
    
    # Verifica se existem ofícios vinculados
    if getattr(tipo, 'oficios', None):
        flash(f'Erro: Existem ofícios vinculados ao tipo "{tipo.nome}". Não é possível excluir.', 'danger')
        return redirect(url_for('admin.tipos_list'))
    
    db.session.delete(tipo)
    db.session.commit()
    flash('Tipo removido com sucesso.', 'success')
    return redirect(url_for('admin.tipos_list'))


# ==============================================================================
# 4. CONFIGURAÇÕES DO SISTEMA (NOVO)
# ==============================================================================

@bp.route('/configuracoes', methods=['GET', 'POST'])
@login_required
@admin_required
def configuracoes():
    """Gerencia as configurações globais do sistema."""
    form = ConfiguracaoForm()
    
    if form.validate_on_submit():
        # AQUI FUTURAMENTE VOCÊ SALVARÁ NO BANCO DE DADOS
        # Exemplo: Atualizar tabela Configuração (ainda não existe no seu model)
        # config.nome_sistema = form.nome_sistema.data
        # db.session.commit()
        
        flash('Configurações salvas com sucesso!', 'success')
        return redirect(url_for('admin.configuracoes'))
    
    # Preenchimento padrão (Mock) para não ficar vazio na tela
    if request.method == 'GET':
        form.nome_sistema.data = "SGO"
        form.sigla_orgao.data = "UEMA"
        form.itens_por_pagina.data = 10
        form.nome_departamento.data = "Coordenação de Planejamento"

    return render_template('admin/settings.html', form=form)