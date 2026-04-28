from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import func, extract
from datetime import datetime
from werkzeug.security import generate_password_hash
from app.models import db, Oficio, TipoProcesso
from app.forms import PerfilForm

bp = Blueprint('main', __name__)

@bp.route('/')
@bp.route('/dashboard')
@login_required
def index():
    # ==========================================================================
    # 1. CARDS DE KPI (Indicadores Principais)
    # ==========================================================================
    total_oficios = Oficio.query.count()
    total_andamento = Oficio.query.filter_by(status='Em andamento').count()
    total_concluidos = Oficio.query.filter_by(status='Concluído').count()
    
    # Lógica do Mês Atual
    ano_atual = datetime.now().year
    mes_atual = datetime.now().month
    
    total_mes = Oficio.query.filter(
        extract('year', Oficio.data_envio) == ano_atual,
        extract('month', Oficio.data_envio) == mes_atual
    ).count()

    # ==========================================================================
    # 2. GRÁFICO DE EVOLUÇÃO (chart_mes)
    # ==========================================================================
    # Agrupa por mês do ano atual
    dados_mes = db.session.query(
        extract('month', Oficio.data_envio).label('mes'),
        func.count(Oficio.id).label('total')
    ).filter(
        extract('year', Oficio.data_envio) == ano_atual
    ).group_by('mes').order_by('mes').all()

    nomes_meses = {
        1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
        7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
    }

    labels_mes = []
    data_mes = []

    # Preenche com dados reais
    if not dados_mes:
        labels_mes = ['Jan', 'Fev', 'Mar'] # Placeholder se vazio
        data_mes = [0, 0, 0]
    else:
        for m, total in dados_mes:
            labels_mes.append(nomes_meses.get(int(m), str(m)))
            data_mes.append(total)

    chart_mes = {
        'labels': labels_mes,
        'data': data_mes
    }

    # ==========================================================================
    # 3. GRÁFICO DE STATUS (chart_status)
    # ==========================================================================
    dados_status = db.session.query(
        Oficio.status,
        func.count(Oficio.id)
    ).group_by(Oficio.status).all()

    labels_status = []
    data_status = []

    if not dados_status:
         labels_status = ['Sem dados']
         data_status = [1]
    else:
        for status, total in dados_status:
            labels_status.append(status)
            data_status.append(total)

    chart_status = {
        'labels': labels_status,
        'data': data_status
    }

    # ==========================================================================
    # 4. GRÁFICO DE TIPOS DE PROCESSO (chart_tipo)
    # ==========================================================================
    # Faz join com a tabela de tipos para pegar o nome
    dados_tipo = db.session.query(
        TipoProcesso.nome,
        func.count(Oficio.id)
    ).join(Oficio, Oficio.tipo_processo_id == TipoProcesso.id)\
     .group_by(TipoProcesso.nome)\
     .order_by(func.count(Oficio.id).desc())\
     .limit(5).all() # Pega apenas os top 5

    labels_tipo = []
    data_tipo = []

    if not dados_tipo:
        labels_tipo = ['Geral']
        data_tipo = [0]
    else:
        for nome, total in dados_tipo:
            labels_tipo.append(nome)
            data_tipo.append(total)
            
    chart_tipo = {
        'labels': labels_tipo,
        'data': data_tipo
    }

    # ==========================================================================
    # 5. RENDERIZAÇÃO
    # ==========================================================================
    return render_template('dashboard/index.html',
                           total_oficios=total_oficios,
                           total_andamento=total_andamento,
                           total_concluidos=total_concluidos,
                           total_mes=total_mes,
                           chart_mes=chart_mes,
                           chart_status=chart_status,
                           chart_tipo=chart_tipo)

# ==============================================================================
# ROTA DE PERFIL DO USUÁRIO (MEUS DADOS)
# ==============================================================================
@bp.route('/meus-dados', methods=['GET', 'POST'])
@login_required
def meus_dados():
    form = PerfilForm()
    
    if form.validate_on_submit():
        current_user.nome = form.nome.data
        current_user.email = form.email.data
        
        if form.password.data:
            current_user.senha_hash = generate_password_hash(form.password.data)
            
        db.session.commit()
        flash('Seus dados foram atualizados com sucesso!', 'success')
        return redirect(url_for('main.meus_dados'))
        
    elif request.method == 'GET':
        form.nome.data = current_user.nome
        form.email.data = current_user.email
        
    # ======================================================================
    # ATENÇÃO AQUI: Verifique o nome da pasta onde salvou o HTML
    # ======================================================================
    try:
        return render_template('user/meus_dados.html', form=form)
    except:
        # Tenta no plural se o singular falhar (Fallback)
        return render_template('users/meus_dados.html', form=form)

# ==============================================================================
# ROTA DO RELATÓRIO GERENCIAL (PDF / IMPRESSÃO)
# ==============================================================================
@bp.route('/relatorio/geral')
@login_required
def relatorio_geral():
    """
    Gera um relatório gerencial formatado para impressão (A4).
    """
    # 1. Dados Gerais
    total_oficios = Oficio.query.count()
    
    # 2. Estatísticas por Status
    stats_status = db.session.query(
        Oficio.status, func.count(Oficio.id)
    ).group_by(Oficio.status).all()
    
    # 3. Estatísticas por Tipo
    stats_tipo = db.session.query(
        TipoProcesso.nome, func.count(Oficio.id)
    ).join(Oficio, Oficio.tipo_processo_id == TipoProcesso.id).group_by(TipoProcesso.nome).all()
    
    # 4. Listagem Detalhada
    # O objeto 'oficios' passado para o template contém a relação 'setor_atual'
    # que será usada para exibir a nova coluna de Localização.
    oficios = Oficio.query.order_by(Oficio.data_envio.desc()).limit(50).all()
    
    # Data da geração
    data_geracao = datetime.now()

    return render_template('relatorios/geral.html',
                           oficios=oficios,
                           total_oficios=total_oficios,
                           stats_status=stats_status,
                           stats_tipo=stats_tipo,
                           data_geracao=data_geracao)