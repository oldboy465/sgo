# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, TextAreaField, DateField, IntegerField, TimeField, SelectMultipleField, widgets
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from app.models import User, Setor, Lotacao, TipoProcesso, Oficio, Configuracao, NotaOrcamentaria

# ==============================================================================
# FORMULÁRIO DE AUTENTICAÇÃO (LOGIN)
# ==============================================================================
class LoginForm(FlaskForm):
    email = StringField('E-mail', validators=[
        DataRequired(message="O e-mail é obrigatório."),
        Email(message="Digite um e-mail válido.")
    ])
    password = PasswordField('Senha', validators=[
        DataRequired(message="A senha é obrigatória.")
    ])
    remember = BooleanField('Lembrar-me')
    submit = SubmitField('Acessar Sistema')

# ==============================================================================
# FORMULÁRIO DE GERENCIAMENTO DE USUÁRIOS (ADMIN)
# ==============================================================================
class UserForm(FlaskForm):
    nome = StringField('Nome Completo', validators=[
        DataRequired(message="O nome é obrigatório."),
        Length(min=3, max=100)
    ])

    email = StringField('E-mail Corporativo', validators=[
        DataRequired(message="O e-mail é obrigatório."),
        Email(message="Insira um e-mail válido."),
        Length(max=120)
    ])

    password = PasswordField('Senha', validators=[
        Optional(),
        Length(min=6, message="A senha deve ter no mínimo 6 caracteres.")
    ])

    confirm_password = PasswordField('Confirmar Senha', validators=[
        EqualTo('password', message='As senhas devem ser iguais.')
    ])

    # SELEÇÃO DA LOTAÇÃO OFICIAL DO USUÁRIO (ONDE O SERVIDOR TRABALHA)
    lotacao_id = SelectField('Lotação de Trabalho', coerce=int, validators=[
        DataRequired(message="Selecione a lotação do usuário.")
    ])

    perfil = SelectField('Perfil de Acesso', choices=[
        ('Usuario', 'Usuário Padrão'),
        ('Administrador', 'Administrador do Sistema')
    ], validators=[DataRequired()])

    ativo = BooleanField('Usuário Ativo', default=True)

    # SELEÇÃO MÚLTIPLA DOS SETORES QUE O USUÁRIO PODE ACOMPANHAR/TRAMITAR
    setores = SelectMultipleField(
        'Setores Autorizados para Tramitação',
        coerce=int,
        widget=widgets.ListWidget(prefix_label=False),
        option_widget=widgets.CheckboxInput()
    )

    submit = SubmitField('Salvar Usuário')

    def __init__(self, original_email=None, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.original_email = original_email

        # Preenche dinamicamente as opções de Lotações e Setores
        try:
            self.lotacao_id.choices = [(l.id, f"{l.sigla} - {l.nome}") for l in Lotacao.query.filter_by(ativo=True).order_by(Lotacao.sigla).all()]
            self.setores.choices = [(s.id, f"{s.sigla} - {s.nome}") for s in Setor.query.filter_by(ativo=True).order_by(Setor.sigla).all()]
        except Exception:
            self.lotacao_id.choices = []
            self.setores.choices = []

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Este e-mail já está cadastrado para outro usuário.')

# ==============================================================================
# FORMULÁRIO DE GERENCIAMENTO DE LOTAÇÃO (NOVO)
# ==============================================================================
class LotacaoForm(FlaskForm):
    nome = StringField('Nome da Unidade de Lotação', validators=[
        DataRequired(message="O nome da lotação é obrigatório."),
        Length(min=2, max=100)
    ])

    sigla = StringField('Sigla (Ex: PROPLAD)', validators=[
        DataRequired(message="A sigla é obrigatória."),
        Length(min=2, max=20)
    ])

    ativo = BooleanField('Lotação Ativa', default=True)

    submit = SubmitField('Salvar Lotação')

    def __init__(self, original_sigla=None, *args, **kwargs):
        super(LotacaoForm, self).__init__(*args, **kwargs)
        self.original_sigla = original_sigla

    def validate_sigla(self, sigla):
        if sigla.data != self.original_sigla:
            lotacao = Lotacao.query.filter_by(sigla=sigla.data.upper()).first()
            if lotacao:
                raise ValidationError('Já existe uma lotação cadastrada com esta sigla.')

# ==============================================================================
# FORMULÁRIO DE PERFIL (MEUS DADOS)
# ==============================================================================
class PerfilForm(FlaskForm):
    nome = StringField('Nome Completo', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Nova Senha', validators=[Optional(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Senha', validators=[
        EqualTo('password', message='As senhas devem ser iguais.')
    ])
    submit = SubmitField('Salvar Alterações')

# ==============================================================================
# FORMULÁRIO DE CONFIGURAÇÕES GERAIS
# ==============================================================================
class ConfiguracaoForm(FlaskForm):
    nome_sistema = StringField('Nome do Sistema', validators=[DataRequired()])
    sigla_orgao = StringField('Sigla do Órgão', validators=[DataRequired()])
    nome_departamento = StringField('Nome do Departamento', validators=[Optional()])
    logo_url = StringField('URL do Brasão/Logo', validators=[Optional(), Length(max=500)])
    itens_por_pagina = IntegerField('Itens por Página', validators=[DataRequired()])
    email_suporte = StringField('E-mail de Suporte', validators=[Optional(), Email()])
    modo_manutencao = BooleanField('Modo de Manutenção')
    submit = SubmitField('Salvar Configurações')

# ==============================================================================
# FORMULÁRIO DE GERENCIAMENTO DE SETORES
# ==============================================================================
class SetorForm(FlaskForm):
    nome = StringField('Nome do Setor', validators=[
        DataRequired(),
        Length(min=2, max=100)
    ])

    sigla = StringField('Sigla (Ex: ASPLAN)', validators=[
        DataRequired(),
        Length(min=2, max=20)
    ])

    ativo = BooleanField('Setor Ativo', default=True)

    submit = SubmitField('Salvar Setor')

    def __init__(self, original_sigla=None, *args, **kwargs):
        super(SetorForm, self).__init__(*args, **kwargs)
        self.original_sigla = original_sigla

    def validate_sigla(self, sigla):
        if sigla.data != self.original_sigla:
            setor = Setor.query.filter_by(sigla=sigla.data.upper()).first()
            if setor:
                raise ValidationError('Já existe um setor com esta sigla.')

# ==============================================================================
# FORMULÁRIO DE TIPO DE PROCESSO
# ==============================================================================
class TipoProcessoForm(FlaskForm):
    nome = StringField('Nome do Tipo', validators=[
        DataRequired(),
        Length(min=3, max=100)
    ])
    descricao = TextAreaField('Descrição (Opcional)', validators=[
        Optional(),
        Length(max=255)
    ])
    submit = SubmitField('Salvar Tipo')

    def __init__(self, original_nome=None, *args, **kwargs):
        super(TipoProcessoForm, self).__init__(*args, **kwargs)
        self.original_nome = original_nome

    def validate_nome(self, nome):
        if nome.data != self.original_nome:
            tipo = TipoProcesso.query.filter_by(nome=nome.data).first()
            if tipo:
                raise ValidationError('Já existe um tipo de processo com este nome.')

# ==============================================================================
# FORMULÁRIO DE OFÍCIOS (CORE BUSINESS)
# ==============================================================================
class OficioForm(FlaskForm):
    numero_oficio = StringField('Número do Ofício', validators=[
        DataRequired(message="O número é obrigatório."),
        Length(max=50)
    ])

    processo_sei = StringField('Processo SEI', validators=[
        Optional(),
        Length(max=50)
    ])

    titulo = StringField('Título / Objeto', validators=[
        DataRequired(),
        Length(max=200)
    ])

    objeto_detalhado = TextAreaField('Detalhamento do Objeto', validators=[
        Optional()
    ])

    quem_assinou = StringField('Quem Assinou (Nome)', validators=[
        DataRequired(),
        Length(max=100)
    ])

    data_envio = DateField('Data de Envio', format='%Y-%m-%d', validators=[
        DataRequired()
    ])

    tipo_processo_id = SelectField('Tipo de Processo', coerce=int, validators=[DataRequired()])
    setor_emissor_id = SelectField('Setor Emissor', coerce=int, validators=[DataRequired()])
    setor_atual_id = SelectField('Localização Atual', coerce=int, validators=[Optional()])

    data_recebimento = DateField('Data de Recebimento no Setor', format='%Y-%m-%d', validators=[Optional()])
    hora_recebimento = TimeField('Hora de Recebimento no Setor', format='%H:%M', validators=[Optional()])

    status = SelectField('Status', choices=[
        ('Em andamento', 'Em andamento'),
        ('Concluído', 'Concluído'),
        ('Atendido', 'Atendido'),
        ('Substituído', 'Substituído'),
        ('Cancelada', 'Cancelada')
    ], default='Em andamento')

    acao_tomada = TextAreaField('Ação Tomada / Despacho', validators=[Optional()])

    submit = SubmitField('Salvar Ofício')

    def __init__(self, original_numero=None, *args, **kwargs):
        super(OficioForm, self).__init__(*args, **kwargs)
        self.original_numero = original_numero

        try:
            self.tipo_processo_id.choices = [(t.id, t.nome) for t in TipoProcesso.query.order_by(TipoProcesso.nome).all()]
            self.setor_emissor_id.choices = [(s.id, f"{s.sigla} - {s.nome}") for s in Setor.query.filter_by(ativo=True).order_by(Setor.sigla).all()]
            self.setor_atual_id.choices = [(s.id, f"{s.sigla} - {s.nome}") for s in Setor.query.filter_by(ativo=True).order_by(Setor.sigla).all()]
        except Exception:
            self.tipo_processo_id.choices = []
            self.setor_emissor_id.choices = []
            self.setor_atual_id.choices = []

    def validate_numero_oficio(self, numero_oficio):
        if numero_oficio.data != self.original_numero:
            oficio = Oficio.query.filter_by(numero_oficio=numero_oficio.data).first()
            if oficio:
                raise ValidationError('Este número de ofício já existe.')

class NotaOrcamentariaForm(FlaskForm):
    data_emissao = DateField('Data de Emissão', format='%Y-%m-%d', validators=[DataRequired()])
    numero_no = StringField('Número da NO', validators=[DataRequired(), Length(max=50)])
    tipo_no = SelectField('Tipo de NO', choices=[
        ('Crédito Adicional', 'Crédito Adicional'),
        ('Alteração Sistema', 'Alteração Sistema'),
        ('Transferência', 'Transferência'),
        ('Transposição', 'Transposição'),
        ('Portaria', 'Portaria'),
        ('Outras', 'Outras')
    ], validators=[DataRequired()])
    tem_oficio = SelectField('Ofício', choices=[
        ('Sim', 'Sim'),
        ('Não', 'Não')
    ], validators=[DataRequired()])
    numero_oficio = StringField('Número do Ofício', validators=[Optional(), Length(max=50)])
    processo_sei = StringField('Processo SEI', validators=[Optional(), Length(max=50)])
    descricao_resumida = TextAreaField('Descrição Resumida', validators=[DataRequired(), Length(max=5000)])
    status = SelectField('Status', choices=[
        ('Liberada', 'Liberada'),
        ('Assinada', 'Assinada'),
        ('Associada', 'Associada'),
        ('Realizada', 'Realizada'),
        ('Cancelada', 'Cancelada')
    ], validators=[DataRequired()])
    observacoes = TextAreaField('Observações', validators=[Optional(), Length(max=5000)])
    submit = SubmitField('Salvar Nota Orçamentária')

    def __init__(self, original_numero=None, *args, **kwargs):
        super(NotaOrcamentariaForm, self).__init__(*args, **kwargs)
        self.original_numero = original_numero

    def validate_numero_no(self, numero_no):
        if numero_no.data != self.original_numero:
            no = NotaOrcamentaria.query.filter_by(numero_no=numero_no.data).first()
            if no:
                raise ValidationError('Este número de Nota Orçamentária já existe.')