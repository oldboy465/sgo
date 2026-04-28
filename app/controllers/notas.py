from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import db, NotaOrcamentaria
from app.forms import NotaOrcamentariaForm
import datetime
from sqlalchemy import func

notas_bp = Blueprint('notas', __name__, url_prefix='/notas')

@notas_bp.route('/')
@login_required
def list():
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    tipo_filter = request.args.get('tipo_no', '')
    
    query = NotaOrcamentaria.query

    # ADIÇÃO: Segurança - Usuário normal só visualiza as próprias notas
    if current_user.perfil != 'Administrador':
        query = query.filter_by(criador_id=current_user.id)

    if search:
        query = query.filter(NotaOrcamentaria.numero_no.ilike(f'%{search}%'))
    if status_filter:
        query = query.filter_by(status=status_filter)
    if tipo_filter: 
        query = query.filter(NotaOrcamentaria.tipo_no.ilike(f'%{tipo_filter}%'))

    notas = query.order_by(NotaOrcamentaria.data_emissao.desc()).all()
    return render_template('notas/list.html', notas=notas)

@notas_bp.route('/view/<int:id>', methods=['GET'])
@login_required
def view(id):
    nota = NotaOrcamentaria.query.get_or_404(id)
    # ADIÇÃO: Segurança Anti-Acesso Direto pela URL
    if current_user.perfil != 'Administrador' and nota.criador_id != current_user.id:
        flash('Acesso negado. Você só pode visualizar as suas próprias notas.', 'danger')
        return redirect(url_for('notas.list'))
    return render_template('notas/view.html', nota=nota, title='Visualizar Nota Orçamentária')

@notas_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = NotaOrcamentariaForm()
    if form.validate_on_submit():
        nova_nota = NotaOrcamentaria(
            data_emissao=form.data_emissao.data,
            numero_no=form.numero_no.data,
            tipo_no=form.tipo_no.data,
            tem_oficio=form.tem_oficio.data,
            numero_oficio=form.numero_oficio.data if form.tem_oficio.data == 'Sim' else None,
            processo_sei=form.processo_sei.data if form.tem_oficio.data == 'Sim' else None,
            descricao_resumida=form.descricao_resumida.data,
            status=form.status.data,
            observacoes=form.observacoes.data,
            criador_id=current_user.id
        )
        db.session.add(nova_nota)
        db.session.commit()
        flash('Nota Orçamentária registrada com sucesso!', 'success')
        return redirect(url_for('notas.list'))
    return render_template('notas/form.html', form=form, title='Nova Nota Orçamentária')

@notas_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    nota = NotaOrcamentaria.query.get_or_404(id)
    # ADIÇÃO: Segurança Anti-Acesso Direto pela URL
    if current_user.perfil != 'Administrador' and nota.criador_id != current_user.id:
        flash('Acesso negado. Você só pode editar as suas próprias notas.', 'danger')
        return redirect(url_for('notas.list'))
        
    form = NotaOrcamentariaForm(obj=nota, original_numero=nota.numero_no)
    if form.validate_on_submit():
        nota.data_emissao = form.data_emissao.data
        nota.numero_no = form.numero_no.data
        nota.tipo_no = form.tipo_no.data
        nota.tem_oficio = form.tem_oficio.data
        nota.numero_oficio = form.numero_oficio.data if form.tem_oficio.data == 'Sim' else None
        nota.processo_sei = form.processo_sei.data if form.tem_oficio.data == 'Sim' else None
        nota.descricao_resumida = form.descricao_resumida.data
        nota.status = form.status.data
        nota.observacoes = form.observacoes.data
        db.session.commit()
        flash('Nota Orçamentária atualizada com sucesso!', 'success')
        return redirect(url_for('notas.list'))
    return render_template('notas/form.html', form=form, title='Editar Nota Orçamentária')

@notas_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    nota = NotaOrcamentaria.query.get_or_404(id)
    # ADIÇÃO: Segurança Anti-Acesso Direto pela URL
    if current_user.perfil != 'Administrador' and nota.criador_id != current_user.id:
        flash('Acesso negado. Você só pode excluir as suas próprias notas.', 'danger')
        return redirect(url_for('notas.list'))
        
    db.session.delete(nota)
    db.session.commit()
    flash('Nota Orçamentária removida com sucesso!', 'success')
    return redirect(url_for('notas.list'))

@notas_bp.route('/relatorio')
@login_required
def relatorio():
    status_filter = request.args.get('status', '')
    tipo_filter = request.args.get('tipo_no', '')
    
    query = NotaOrcamentaria.query
    
    # ADIÇÃO: Segurança do Relatório - Usuário só tira relatório de suas próprias notas
    if current_user.perfil != 'Administrador':
        query = query.filter_by(criador_id=current_user.id)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    if tipo_filter:
        query = query.filter_by(tipo_no=tipo_filter)
        
    notas = query.order_by(NotaOrcamentaria.data_emissao.desc()).all()
    total_notas = len(notas)
    data_geracao = datetime.datetime.now()
    
    stats_query = db.session.query(
        NotaOrcamentaria.status, func.count(NotaOrcamentaria.id)
    )
    
    # ADIÇÃO: Filtrar contadores por usuário
    if current_user.perfil != 'Administrador':
        stats_query = stats_query.filter(NotaOrcamentaria.criador_id == current_user.id)
        
    if status_filter:
        stats_query = stats_query.filter_by(status=status_filter)
    if tipo_filter:
        stats_query = stats_query.filter_by(tipo_no=tipo_filter)
        
    stats_status = stats_query.group_by(NotaOrcamentaria.status).all()

    return render_template('notas/relatorio.html', notas=notas, total_notas=total_notas, data_geracao=data_geracao, stats_status=stats_status)