from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.models import db, Oficio, Setor, TipoProcesso
from app.forms import OficioForm
from datetime import datetime

bp = Blueprint('oficios', __name__)

@bp.route('/list')
@login_required
def list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search')
    
    # Filtros recebidos da URL (Request Args)
    status_filter = request.args.get('status')
    setor_atual_filter = request.args.get('setor_atual_id', type=int) # Novo Filtro solicitado
    
    query = Oficio.query

    # Filtro de Busca Textual
    if search:
        query = query.filter(
            (Oficio.numero_oficio.like(f'%{search}%')) |
            (Oficio.titulo.like(f'%{search}%')) |
            (Oficio.processo_sei.like(f'%{search}%'))
        )
    
    # Filtro por Status (se houver e não for vazio)
    if status_filter and status_filter != '':
        query = query.filter(Oficio.status == status_filter)

    # Filtro por Setor Atual (Solicitado)
    if setor_atual_filter:
        query = query.filter(Oficio.setor_atual_id == setor_atual_filter)
    
    # Paginação
    oficios = query.order_by(Oficio.data_envio.desc()).paginate(page=page, per_page=10)
    
    # Carrega setores para preencher o Dropdown de filtro no HTML
    setores = Setor.query.filter_by(ativo=True).order_by(Setor.sigla).all()
    
    return render_template('oficios/list.html', oficios=oficios, setores=setores)

@bp.route('/create', methods=['GET', 'POST'])
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
            setor_atual_id=form.setor_atual_id.data or form.setor_emissor_id.data,
            status=form.status.data,
            # Correção: Persistir o campo de despacho/ação tomada
            acao_tomada=form.acao_tomada.data,
            criador_id=current_user.id
        )
        
        db.session.add(oficio)
        db.session.commit()
        
        flash(f'Ofício {oficio.numero_oficio} cadastrado com sucesso!', 'success')
        return redirect(url_for('oficios.list'))
        
    return render_template('oficios/form.html', form=form, oficio=None)

# ==============================================================================
# ROTA DE VISUALIZAÇÃO (NOVA ADIÇÃO)
# ==============================================================================
@bp.route('/view/<int:id>', methods=['GET'])
@login_required
def view(id):
    oficio = Oficio.query.get_or_404(id)
    return render_template('oficios/view.html', oficio=oficio)

# ==============================================================================
# ROTA DE EDIÇÃO
# ==============================================================================
@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    oficio = Oficio.query.get_or_404(id)
    
    # Preenche o formulário com os dados existentes
    form = OficioForm(original_numero=oficio.numero_oficio, obj=oficio)
    
    if form.validate_on_submit():
        oficio.numero_oficio = form.numero_oficio.data
        oficio.processo_sei = form.processo_sei.data
        oficio.titulo = form.titulo.data
        oficio.objeto_detalhado = form.objeto_detalhado.data
        oficio.quem_assinou = form.quem_assinou.data
        oficio.data_envio = form.data_envio.data
        oficio.tipo_processo_id = form.tipo_processo_id.data
        oficio.setor_emissor_id = form.setor_emissor_id.data
        oficio.setor_atual_id = form.setor_atual_id.data
        oficio.status = form.status.data
        
        # Correção: Atualizar o campo de despacho/ação tomada
        oficio.acao_tomada = form.acao_tomada.data
        
        db.session.commit()
        flash('Ofício atualizado com sucesso.', 'success')
        return redirect(url_for('oficios.list'))
        
    return render_template('oficios/form.html', form=form, oficio=oficio)

# ==============================================================================
# ROTA DE EXCLUSÃO (OPCIONAL, MAS RECOMENDADA)
# ==============================================================================
@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    oficio = Oficio.query.get_or_404(id)
    
    # Permissão: Só Admin ou o criador pode apagar
    if current_user.perfil != 'Administrador' and current_user.id != oficio.criador_id:
        abort(403) # Proibido
        
    db.session.delete(oficio)
    db.session.commit()
    flash('Ofício removido com sucesso.', 'success')
    return redirect(url_for('oficios.list'))