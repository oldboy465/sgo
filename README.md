Segue o conteúdo completo do ficheiro `README.md`, pronto a guardar e sem quaisquer marcas de citação:

# 🏛️ SGO — Sistema de Gerenciamento de Ofícios e Notas Orçamentárias

> Plataforma Institucional para Controlo de Tramitação de Processos, Lotações e Execução Orçamental.
> 
> 

---

### Badges e Tecnologias

---

## 🧭 Visão Geral

O **SGO (Sistema de Gestão e Operações)** é uma aplicação web de governança administrativa desenvolvida com arquitetura **MVC (Model-View-Controller)** em Python/Flask. O sistema atende à procura institucional de rastreabilidade documental, auditabilidade de movimentações entre departamentos e acompanhamento de créditos e notas orçamentais.

Possui isolamento estrito de permissões: os utilizadores comuns interagem apenas com processos vinculados à sua **Lotação** ou aos seus **Setores de Tramitação Autorizados**, enquanto o perfil **Administrador** detém visão executiva global, parametrizações e controlo de manutenção.

---

## ⚡ Principais Módulos do Sistema

| 📄 GESTÃO DE OFÍCIOS | 💰 NOTAS ORÇAMENTÁRIAS | 🔒 ADMIN & ACESSO |
| --- | --- | --- |
| Tramitação física de documentos

 | Créditos adicionais e transferências

 | Lotação oficial de trabalho

 |
| Vinculação a processos SEI

 | Portarias, transposições e alterações

 | Setores autorizados para trâmite

 |
| Cálculo do tempo no setor

 | Registo de despachos e observações

 | Modo de manutenção centralizado

 |
| Exportação A4 e relatórios

 | Relatórios sintéticos individuais

 | Painel de notificações do sistema

 |

### 1. Núcleo de Ofícios e Processos Administrativos

* Registo com identificador do ofício, processo SEI, responsável pela assinatura, setor emissor e setor recetor.


* Cálculo dinâmico do tempo de permanência no setor com base na data e hora do recebimento.


* Workflow de estados: *Em andamento*, *Concluído*, *Atendido*, *Substituído* ou *Cancelada*.



### 2. Módulo de Notas Orçamentárias (`NO`)

* Acompanhamento de alterações orçamentais: *Créditos Adicionais*, *Transposições*, *Transferências*, *Portarias* e *Alterações de Sistema*.


* Correlação direta ou independente com números de ofício e processos SEI.


* Segurança estrita: o utilizador comum visualiza, edita e gera relatórios apenas das suas próprias notas registadas.



### 3. Painel Administrativo e Governança

* Distinção entre **Lotação** (unidade física de trabalho do servidor) e **Setores** (unidades administrativas por onde tramitam os processos).


* Associação muitos-para-muitos (`usuario_setor`): permissão para um mesmo servidor despachar em múltiplos departamentos autorizados.


* Bloqueio de manutenção centralizado com libertação exclusiva para o perfil Administrador.



---

## 📈 Dashboard em Tempo Real

* **KPIs Instantâneos**: Total de ofícios emitidos, processos em andamento, concluídos e volume do mês corrente.


* **Evolução Semestral**: Gráfico histórico de documentos emitidos nos últimos 6 meses com agrupamento dinâmico via Chart.js.


* **Distribuição por Tipo**: Percentagem dos tipos documentais mais recorrentes na instituição.



---

## 🛠️ Tecnologias e Bibliotecas

| Camada | Tecnologia | Função no Sistema |
| --- | --- | --- |
| **Backend** | Python 3 / Flask | Servidor HTTP, regras de negócio e rotas MVC

 |
| **ORM / Base de Dados** | Flask-SQLAlchemy / PostgreSQL / SQLite | Abstração de base de dados híbrida (Local x Nuvem Neon)

 |
| **Segurança** | Flask-Login / Werkzeug | Hash de palavras-passe, controlo de sessões e cookies seguros

 |
| **Formulários** | Flask-WTF / WTForms | Validação de formulários, campos dinâmicos e proteção CSRF

 |
| **Frontend** | Tailwind CSS / Bootstrap 5 | Interface responsiva e componentes de formulário

 |
| **Gráficos** | Chart.js | Visualização de dados analíticos no painel principal

 |
| **Relatórios** | Pandas / PDFKit | Exportação e processamento tabular de dados

 |

---

## 📂 Estrutura de Diretórios

```
sgo-main/
├── app/
│   ├── controllers/         # Módulos: admin, auth, main, notas, oficios
│   ├── services/            # Utilitários de exportação (Excel / PDF)
│   ├── static/              # Estilos Tailwind, Bootstrap e Chart.js
│   ├── templates/           # Ecrãs Jinja2 organizados por módulo
│   ├── forms.py             # Formulários WTForms
│   ├── models.py            # Modelos SQLAlchemy e base de dados
│   └── routes.py            # Registo de rotas e blueprints
├── atualizar_banco.py       # Criação e atualização de tabelas no SQLite local
├── baixar_banco.py          # Sincronização: Neon Postgres (Nuvem) -> SQLite local
├── migrar_banco.py          # Migração: SQLite local -> Neon Postgres (Nuvem)
├── config.py                # Configurações de ambientes (Dev, Prod, Test)
├── main.py                  # Ponto de entrada para deploy na nuvem / Vercel
├── run.py                   # Ponto de entrada para execução local
├── requirements.txt         # Dependências do projeto
└── vercel.json              # Configurações de implementação serverless

```

---

## 🚀 Instalação e Execução

### 1. Clonar o Repositório

```bash
git clone https://github.com/oldboy465/sgo.git
cd sgo

```

### 2. Configurar o Ambiente Virtual

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate

```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt

```

### 4. Inicializar a Base de Dados Local

```bash
python atualizar_banco.py

```

*(Opcional)* Para sincronizar os dados da nuvem com a base de dados SQLite local:

```bash
python baixar_banco.py

```

### 5. Executar a Aplicação

```bash
python run.py

```

Aceda no navegador: `http://localhost:5000`.

---




---

Desenvolvido por **[oldboy465](https://www.google.com/search?q=https://github.com/oldboy465)**
