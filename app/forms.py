# forms.py
from flask_wtf import FlaskForm
# ADIÇÃO: Importamos SelectMultipleField e widgets para usar caixas de seleção
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, TextAreaField, DateField, IntegerField, TimeField, SelectMultipleField, widgets
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from app.models import User, Setor, TipoProcesso, Oficio, Configuracao, NotaOrcamentaria

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
        DataRequired(),
        Length(min=3, max=100)
    ])

    email = StringField('E-mail Corporativo', validators=[
        DataRequired(),
        Email(),
        Length(max=120)
    ])

    password = PasswordField('Senha', validators=[
        Optional(),
        Length(min=6, message="A senha deve ter no mínimo 6 caracteres.")
    ])

    confirm_password = PasswordField('Confirmar Senha', validators=[
        EqualTo('password', message='As senhas devem ser iguais.')
    ])

    perfil = SelectField('Perfil de Acesso', choices=[
        ('Usuario', 'Usuário Padrão'),
        ('Administrador', 'Administrador do Sistema')
    ], validators=[DataRequired()])

    ativo = BooleanField('Usuário Ativo', default=True)
    
    # ADIÇÃO: Campo de seleção múltipla transformado em lista de Checkboxes
    setores = SelectMultipleField(
        'Setores Autorizados',
        coerce=int,
        widget=widgets.ListWidget(prefix_label=False),
        option_widget=widgets.CheckboxInput()
    )

    submit = SubmitField('Salvar Usuário')

    def __init__(self, original_email=None, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.original_email = original_email
        
        # ADIÇÃO: Preenche dinamicamente as opções de setores
        try:
            self.setores.choices = [(s.id, f"{s.sigla} - {s.nome}") for s in Setor.query.filter_by(ativo=True).order_by(Setor.sigla).all()]
        except:
            self.setores.choices = []

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Este e-mail já está cadastrado para outro usuário.')

# ==============================================================================
# FORMULÁRIO DE PERFIL (MEUS DADOS) - NOVO
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
# FORMULÁRIO DE CONFIGURAÇÕES GERAIS - NOVO
# ==============================================================================
class ConfiguracaoForm(FlaskForm):
    nome_sistema = StringField('Nome do Sistema', validators=[DataRequired()])
    sigla_orgao = StringField('Sigla do Órgão', validators=[DataRequired()])
    nome_departamento = StringField('Nome do Departamento', validators=[Optional()])

    # Campo Novo para URL do Brasão
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
            setor = Setor.query.filter_by(sigla=sigla.data).first()
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

    # SelectFields com coerce=int para garantir IDs inteiros
    tipo_processo_id = SelectField('Tipo de Processo', coerce=int, validators=[DataRequired()])
    setor_emissor_id = SelectField('Setor Emissor', coerce=int, validators=[DataRequired()])
    setor_atual_id = SelectField('Localização Atual', coerce=int, validators=[Optional()])

    data_recebimento = DateField('Data de Recebimento no Setor', format='%Y-%m-%d', validators=[Optional()])
    hora_recebimento = TimeField('Hora de Recebimento no Setor', format='%H:%M', validators=[Optional()])

    status = SelectField('Status', choices=[
        ('Em andamento', 'Em andamento'),
        ('Concluído', 'Concluído'),
        ('Atendido', 'Atendido'),
        ('Substituído', 'Substituído')
    ], default='Em andamento')

    # Campo de Ação Tomada / Despacho
    # Mantendo como TextAreaField para garantir que o formulário processe o campo corretamente
    acao_tomada = TextAreaField('Ação Tomada / Despacho', validators=[Optional()])

    submit = SubmitField('Salvar Ofício')

    def __init__(self, original_numero=None, *args, **kwargs):
        super(OficioForm, self).__init__(*args, **kwargs)
        self.original_numero = original_numero

        # População dinâmica dos selects
        # Nota: Filtramos apenas setores ativos e ordenamos para melhor UX
        try:
            self.tipo_processo_id.choices = [(t.id, t.nome) for t in TipoProcesso.query.order_by(TipoProcesso.nome).all()]
            self.setor_emissor_id.choices = [(s.id, f"{s.sigla} - {s.nome}") for s in Setor.query.filter_by(ativo=True).order_by(Setor.sigla).all()]
            self.setor_atual_id.choices = [(s.id, f"{s.sigla} - {s.nome}") for s in Setor.query.filter_by(ativo=True).order_by(Setor.sigla).all()]
        except:
            # Fallback caso o banco ainda não tenha sido criado ou esteja sem tabelas
            self.tipo_processo_id.choices = []
            self.setor_emissor_id.choices = []
            self.setor_atual_id.choices = []

    def validate_numero_oficio(self, numero_oficio):
        """
        Valida unicidade do número do ofício.
        """
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
        ('Realizada', 'Realizada')
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