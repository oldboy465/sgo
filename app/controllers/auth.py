from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, db
from app.forms import LoginForm

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        # Busca usuário pelo e-mail
        user = User.query.filter_by(email=form.email.data).first()
        
        # Verifica se usuário existe E se a senha bate (usando o método seguro do model)
        if user and user.verify_password(form.password.data):
            if not user.ativo:
                flash('Sua conta está inativa. Contate o administrador.', 'danger')
                return render_template('auth/login.html', form=form)

            login_user(user, remember=form.remember.data)
            
            # Redirecionamento inteligente (volta para onde o usuário tentou ir)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        
        else:
            flash('E-mail ou senha inválidos.', 'danger')
            
    return render_template('auth/login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('auth.login'))