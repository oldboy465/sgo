```markdown
<div align="center">

# 🏛️ SGO — Sistema de Gerenciamento de Ofícios e Notas Orçamentárias
### *Plataforma Institucional para Controle de Tramitação de Processos, Lotações e Execução Orçamentária*

<!-- Terminal Typing com Efeito de Digitação Contínuo -->
<a href="https://git.io/typing-svg">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=16&duration=2600&pause=1100&color=009CFF&center=true&vCenter=true&multiline=false&width=760&lines=Rastreamento+de+Processos+Administrativos+e+SEI;Gest%C3%A3o+de+Notas+Or%C3%A7ament%C3%A1rias+e+Cr%C3%A9ditos+Adicionais;Controle+Granular+de+Acesso+por+Lota%C3%A7%C3%A3o+e+Setores;Sincroniza%C3%A7%C3%A3o+H%C3%ADbrida%3A+SQLite+Local+%E2%86%94+PostgreSQL+Neon" alt="SGO Typing SVG" />
</a>

<br/><br/>

<!-- Badges de Tecnologia e Status -->
[![Flask](https://img.shields.io/badge/Flask-2.x-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/Neon_PostgreSQL-Cloud_DB-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://neon.tech/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38BDF8?style=for-the-badge&logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![Chart.js](https://img.shields.io/badge/Chart.js-Analytics-FF6384?style=for-the-badge&logo=chartdotjs&logoColor=white)](https://www.chartjs.org/)
[![Deploy Vercel](https://img.shields.io/badge/Vercel-Production_Ready-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com/)

</div>

---

## 🧭 Visão Geral

O **SGO (Sistema de Gestão e Operações)** é uma aplicação web de governança administrativa desenvolvida com arquitetura **MVC (Model-View-Controller)** em Python/Flask. O sistema atende à demanda institucional de rastreabilidade documental, auditabilidade de movimentações entre departamentos e acompanhamento de créditos e notas orçamentárias.

Possui isolamento estrito de permissões: usuários comuns interagem apenas com processos vinculados à sua **Lotação** ou aos seus **Setores de Tramitação Autorizados**, enquanto o perfil **Administrador** detém visão executiva global, parametrizações e controle de manutenção.

---

## ⚡ Principais Módulos do Sistema


```

┌────────────────────────────────────────────────────────────────────────┐
│                                 SGO CORE                               │
├─────────────────────┬──────────────────────────┬───────────────────────┤
│  📄 GESTÃO DE OFÍCIOS │  💰 NOTAS ORÇAMENTÁRIAS  │  🔒 ADMIN & ACESSO    │
│  - Tramitação física │  - Crédito Adicional     │  - Lotação de Trabalho│
│  - Vinculação ao SEI │  - Portarias e Repasses  │  - Setores de Trâmite │
│  - Tempo no setor    │  - Despacho & Status     │  - Trava de Manutenção│
│  - Exportação A4/PDF │  - Relatório Sintético   │  - Log de Notificações│
└─────────────────────┴──────────────────────────┴───────────────────────┘

```

### 1. Núcleo de Ofícios e Processos Administrativos
* Registro detalhado: identificador do ofício, processo SEI, responsável pela assinatura, emissor original e setor receptor.
* Cálculo dinâmico de **tempo de permanência no setor** com base em data/hora de recebimento.
* Workflow de status: *Em andamento*, *Concluído*, *Atendido*, *Substituído* ou *Cancelada*.

### 2. Módulo de Notas Orçamentárias (`NO`)
* Acompanhamento de alterações orçamentárias: *Créditos Adicionais*, *Transposições*, *Transferências*, *Portarias* e *Alterações de Sistema*.
* Correlação direta ou independente com números de ofício e processos SEI.
* Camada de segurança estrita: o usuário comum visualiza, edita e emite relatórios exclusivamente das suas próprias notas registradas.

### 3. Painel Administrativo e Governança
* Distinção entre **Lotação** (unidade de trabalho físico do servidor) e **Setores** (unidades administrativas por onde tramitam os processos).
* Associação muitos-para-muitos (`usuario_setor`): permissão para um mesmo servidor despachar em nome de múltiplos departamentos credenciados.
* **Modo de Manutenção Centralizado**: bloqueia o acesso operacional de forma imediata mantendo acesso liberado apenas aos administradores.

---

## 🔄 Fluxo de Tramitação e Arquitetura de Dados

```text
[ Setor Emissor ] ────────► [ Tramitação / Validação ] ────────► [ Setor Destino / Execução ]
       │                                                                  │
       ├─► Criação do Ofício / SEI                                       ├─► Registro de Despacho
       └─► Associação com Nota Orçamentária (se aplicável)                └─► Conclusão / Atendimento

```

---

## 📈 Dashboard em Tempo Real

O sistema conta com painel estatístico alimentado via **Chart.js v3** e agregação direta via SQLAlchemy:

* **KPIs Instantâneos**: Total de ofícios emitidos, processos em andamento, concluídos e volume acumulado no mês corrente.
* **Evolução Semestral**: Gráfico histórico de documentos gerados nos últimos 6 meses com agrupamento dinâmico.
* **Distribuição por Tipo de Processo**: Identificação dos tipos documentais mais recorrentes na instituição.

---

## 🛠️ Tecnologias e Bibliotecas

| Camada | Tecnologia / Biblioteca | Função no Sistema |
| --- | --- | --- |
| **Backend** | Python 3 / Flask | Servidor HTTP, regras de negócio e roteamento MVC |
| **ORM / Banco** | Flask-SQLAlchemy / PostgreSQL / SQLite | Abstração de banco de dados híbrido (Local vs Nuvem) |
| **Segurança** | Flask-Login / Werkzeug | Hash de senhas, controle de sessões e cookies seguros |
| **Formulários** | Flask-WTF / WTForms | Validação de CSRF, tipagem e campos dinâmicos |
| **Frontend** | Tailwind CSS / Bootstrap 5 / OwlCarousel | Design responsivo, temas de cores e transições de tela |
| **Gráficos** | Chart.js | Visualização de dados analíticos no dashboard |
| **Relatórios** | Pandas / PDFKit | Exportação estruturada para relatórios executivos |

---

## 📂 Estrutura de Diretórios

```bash
sgo-main/
├── app/
│   ├── controllers/         # Regras de Negócio e Rotas (admin, auth, main, notas, oficios)
│   ├── services/            # Serviços utilitários (exportação Excel / PDF)
│   ├── static/              # Assets estáticos (Tailwind, Chart.js, styles customizados)
│   ├── templates/           # Telas Jinja2 organizadas por domínio funcional
│   ├── forms.py             # Definição e validação de formulários WTForms
│   ├── models.py            # Entidades do SQLAlchemy e relacionamentos de banco
│   └── routes.py            # Orquestração de blueprints e interceptores de requisição
├── atualizar_banco.py       # Migrações manuais e criação de tabelas no SQLite local
├── baixar_banco.py          # Script de sincronização de dados Nuvem (Neon) -> SQLite
├── migrar_banco.py          # Script de migração massiva SQLite -> Postgres na Nuvem
├── config.py                # Configurações de ambientes (Dev, Prod, Test)
├── main.py                  # Entrypoint de execução em produção / Vercel
├── run.py                   # Entrypoint com autodetecção de IP para desenvolvimento local
├── requirements.txt         # Lista de dependências Python
└── vercel.json              # Configuração de build serverless para nuvem

```

---

## 🚀 Instalação e Execução

### 1. Clonar o Repositório

```bash
git clone [https://github.com/oldboy465/sgo.git](https://github.com/oldboy465/sgo.git)
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

### 4. Inicializar a Base de Dados

Para desenvolvimento local com SQLite:

```bash
python atualizar_banco.py

```

*(Opcional)* Caso deseje sincronizar sua base de desenvolvimento local com os registros da nuvem:

```bash
python baixar_banco.py

```

### 5. Executar a Aplicação

```bash
python run.py

```

> O terminal exibirá o endereço de acesso local (`http://localhost:5000`) e o IP atribuído à máquina para acesso de outros computadores da rede interna.

---

.

---

Desenvolvido por **[oldboy465](https://www.google.com/search?q=https://github.com/oldboy465)**
