# models.py
import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

# Instância do Banco de Dados (será inicializada no __init__.py)
db = SQLAlchemy()

# ==============================================================================
# TABELA DE ASSOCIAÇÃO: USUÁRIO <-> SETOR (NOVO)
# ==============================================================================
# Esta tabela invisível permite que um usuário pertença a vários setores 
# e que um setor tenha vários usuários (Muitos-para-Muitos).
usuario_setor = db.Table('usuario_setor',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('setor_id', db.Integer, db.ForeignKey('setores.id'), primary_key=True)
)

# ==============================================================================
# MODELO: USUÁRIOS (Autenticação e Permissões)
# ==============================================================================
class User(UserMixin, db.Model):
    """
    Tabela de Usuários com segurança de hash de senha integrada.
    Substitui a antiga classe 'Usuario'.
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)

    # Perfil: 'Administrador' ou 'Usuario'
    perfil = db.Column(db.String(20), default='Usuario', nullable=False)
    ativo = db.Column(db.Boolean, default=True)

    # Auditoria
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.datetime.now)

    # Relacionamentos
    oficios_criados = db.relationship('Oficio', backref='criador', lazy=True)
    
    # ADIÇÃO: Relacionamento Muitos-para-Muitos com Setores
    setores_permitidos = db.relationship('Setor', secondary=usuario_setor, backref=db.backref('usuarios_vinculados', lazy='dynamic'))

    @property
    def password(self):
        """Impede a leitura direta da senha."""
        raise AttributeError('A senha não é um atributo legível!')

    @password.setter
    def password(self, password):
        """Gera o hash da senha automaticamente ao atribuir valor."""
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        """Verifica se a senha informada corresponde ao hash salvo."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email} - {self.perfil}>'

# ==============================================================================
# MODELO: SETORES (Unidades Administrativas)
# ==============================================================================
class Setor(db.Model):
    """
    Unidades organizacionais (Ex: ASPLAN, PROG, REITORIA).
    """
    __tablename__ = 'setores'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    sigla = db.Column(db.String(20), nullable=False, unique=True)
    ativo = db.Column(db.Boolean, default=True)

    # Relacionamentos (Foreign Keys explícitas para evitar conflito)
    oficios_locais = db.relationship('Oficio', backref='setor_atual', lazy=True, foreign_keys='Oficio.setor_atual_id')
    oficios_emitidos = db.relationship('Oficio', backref='setor_emissor', lazy=True, foreign_keys='Oficio.setor_emissor_id')

    def __repr__(self):
        return f'<Setor {self.sigla}>'

# ==============================================================================
# MODELO: TIPOS DE PROCESSO
# ==============================================================================
class TipoProcesso(db.Model):
    """
    Categorias de Ofícios (Ex: Solicitação, Informativo, Orçamentário).
    """
    __tablename__ = 'tipos_processo'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.String(255), nullable=True)

    oficios = db.relationship('Oficio', backref='tipo_processo', lazy=True)

    def __repr__(self):
        return f'<TipoProcesso {self.nome}>'

# ==============================================================================
# MODELO: CONFIGURAÇÕES DO SISTEMA (NOVO)
# ==============================================================================
class Configuracao(db.Model):
    """
    Armazena configurações globais do sistema (Singleton pattern via DB).
    Resolve o problema de persistência do Brasão e Nomes.
    """
    __tablename__ = 'configuracoes'

    id = db.Column(db.Integer, primary_key=True)
    nome_sistema = db.Column(db.String(100), default='SparkManagerDocs')
    sigla_orgao = db.Column(db.String(20), default='UEMA')
    nome_departamento = db.Column(db.String(100), default='Coordenação de Planejamento e Orçamento')

    # Campo crucial para o Brasão funcionar dinamicamente
    logo_url = db.Column(db.String(500), nullable=True, default='https://upload.wikimedia.org/wikipedia/commons/2/20/Bras%C3%A3o_UEMA.png')

    itens_por_pagina = db.Column(db.Integer, default=10)
    email_suporte = db.Column(db.String(120), nullable=True)
    modo_manutencao = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Configuracao {self.nome_sistema}>'

# ==============================================================================
# MODELO: OFÍCIOS (Tabela Principal)
# ==============================================================================
class Oficio(db.Model):
    """
    O Core do Sistema: Armazena os dados dos ofícios tramitados.
    """
    __tablename__ = 'oficios'

    id = db.Column(db.Integer, primary_key=True)
    numero_oficio = db.Column(db.String(50), unique=True, nullable=False)
    processo_sei = db.Column(db.String(50), nullable=True)

    # Conteúdo
    titulo = db.Column(db.String(200), nullable=False)
    objeto_detalhado = db.Column(db.Text, nullable=True)
    quem_assinou = db.Column(db.String(100), nullable=False)

    # Metadados de Tempo
    data_envio = db.Column(db.Date, default=datetime.date.today, nullable=False)
    data_recebimento = db.Column(db.Date, nullable=True)
    hora_recebimento = db.Column(db.Time, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

    # Workflow
    status = db.Column(db.String(50), default='Em andamento')

    # Campo para o Despacho/Solução (já existia, mas vamos garantir que o Routes use ele)
    acao_tomada = db.Column(db.Text, nullable=True)

    # Chaves Estrangeiras
    criador_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tipo_processo_id = db.Column(db.Integer, db.ForeignKey('tipos_processo.id'), nullable=True)

    setor_emissor_id = db.Column(db.Integer, db.ForeignKey('setores.id'), nullable=False)
    setor_atual_id = db.Column(db.Integer, db.ForeignKey('setores.id'), nullable=True)

    # Lógica de Substituição (Auto-Relacionamento)
    substituido_por_id = db.Column(db.Integer, db.ForeignKey('oficios.id'), nullable=True)
    substituido_por = db.relationship('Oficio', remote_side=[id], backref='substituiu_anterior')

    @property
    def tempo_no_setor(self):
        if self.data_recebimento and self.hora_recebimento:
            dt_recebimento = datetime.datetime.combine(self.data_recebimento, self.hora_recebimento)
            diff = datetime.datetime.now() - dt_recebimento
            dias = diff.days
            horas = diff.seconds // 3600
            if dias > 0:
                return f"{dias} dia(s) e {horas} hora(s)"
            return f"{horas} hora(s)"
        return "N/D"

    def to_dict(self):
        return {
            'id': self.id,
            'numero': self.numero_oficio,
            'titulo': self.titulo,
            'status': self.status,
            'data': self.data_envio.strftime('%d/%m/%Y'),
            'local_atual': self.setor_atual.sigla if self.setor_atual else 'N/A',
            'ultimo_despacho': self.acao_tomada
        }

    def __repr__(self):
        return f'<Oficio {self.numero_oficio}>'

# ==============================================================================
# MODELO: NOTIFICAÇÕES (NOVO)
# ==============================================================================
class Notificacao(db.Model):
    """
    Registra eventos do sistema para exibir no sininho de notificações.
    """
    __tablename__ = 'notificacoes'

    id = db.Column(db.Integer, primary_key=True)
    mensagem = db.Column(db.String(255), nullable=False)
    categoria = db.Column(db.String(20), default='info') # info, success, warning
    link = db.Column(db.String(200), nullable=True) # Para onde vai ao clicar
    lida = db.Column(db.Boolean, default=False) # Opcional, para controle futuro
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

    # Quem gerou a notificação (opcional, mas bom para saber quem fez)
    autor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    autor = db.relationship('User', foreign_keys=[autor_id])

    def tempo_atras(self):
        """Retorna string amigável: 'Há 5 minutos', 'Agora mesmo'"""
        diff = datetime.datetime.now() - self.created_at
        segundos = diff.total_seconds()

        if segundos < 60:
            return "Agora mesmo"
        elif segundos < 3600:
            minutos = int(segundos / 60)
            return f"Há {minutos} min"
        elif segundos < 86400:
            horas = int(segundos / 3600)
            return f"Há {horas} h"
        else:
            dias = int(segundos / 86400)
            return f"Há {dias} dias"

class NotaOrcamentaria(db.Model):
    __tablename__ = 'notas_orcamentarias'

    id = db.Column(db.Integer, primary_key=True)
    data_emissao = db.Column(db.Date, default=datetime.date.today, nullable=False)
    numero_no = db.Column(db.String(50), unique=True, nullable=False)
    tipo_no = db.Column(db.String(50), nullable=False)
    tem_oficio = db.Column(db.String(3), default='Não', nullable=False)
    numero_oficio = db.Column(db.String(50), nullable=True)
    processo_sei = db.Column(db.String(50), nullable=True)
    descricao_resumida = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    observacoes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    criador_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    criador = db.relationship('User', foreign_keys=[criador_id])

    def __repr__(self):
        return f'<NotaOrcamentaria {self.numero_no}>'