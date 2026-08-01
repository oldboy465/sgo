# 🌳 SGO — Sistema de Gerenciamento de Ofícios e Notas Orçamentárias

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.x-green?style=for-the-badge&logo=flask&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Development-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Vercel](https://img.shields.io/badge/Deploy-Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)
![Tailwind/Bootstrap](https://img.shields.io/badge/UI-Bootstrap%2FTailwind-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white)

O **SGO (Sistema de Gerenciamento de Ofícios e Notas Orçamentárias)** é uma plataforma web corporativa moderna, robusta e modular desenvolvida com **Python (Flask)** e **SQLAlchemy**, projetada para controle, acompanhamento e rastreabilidade de processos administrativos, movimentação de ofícios e execução de notas orçamentárias na **Universidade Estadual do Maranhão (UEMA)**.

---

## ⚡ Principais Funcionalidades

- 🏛️ **Gestão de Ofícios & Processos (SEI):** Registro completo com controle de prazos, responsável por assinatura, tempo de permanência no setor e histórico de despachos.
- 💰 **Módulo de Notas Orçamentárias (NO):** Controle individual de créditos adicionais, transferências, transposições e alterações orçamentárias associadas a processos.
- 👥 **Controle de Acesso Baseado em Perfis (RBAC):** Níveis de acesso diferenciados para **Administradores** e **Usuários Padrão**, com restrições por setores autorizados.
- 📊 **Dashboard Analítico e Gráficos:** Indicadores em tempo real (KPIs) com taxas de conclusão, acompanhamento mensal e distribuição por tipo de processo via Chart.js.
- 🔔 **Notificações Globais:** Sistema interno de alertas e eventos em tempo real no menu superior.
- 📄 **Relatórios Gerenciais:** Emissão de relatórios em PDF com leiaute A4 profissional e exportação legível em relatórios analíticos.
- 🛠️ **Modo Manutenção & Trava de Segurança:** Bloqueio dinâmico do sistema para usuários padrão durante atualizações críticas do banco ou servidor.
- ☁️ **Ambiente Multi-Nuvem:** Compatível com execução local (SQLite) e sincronização/migração automática em produção (PostgreSQL via Neon / Hostgator / Vercel).

---

## 🛠️ Arquitetura do Projeto

O projeto adota uma arquitetura inspirada em **MVC (Model-View-Controller)** com suporte a **Blueprints**, garantindo alta escalabilidade e separação de responsabilidades.

```text
sgo-main/
├── app/
│   ├── controllers/      # Controladores da aplicação (Blueprints)
│   │   ├── admin.py      # Gestão de usuários, setores e configurações
│   │   ├── auth.py       # Autenticação e sessão de usuário
│   │   ├── main.py       # Dashboard e visualizações gerais
│   │   ├── notas.py      # Módulo de Notas Orçamentárias
│   │   └── oficios.py    # Módulo de Tramitação de Ofícios
│   ├── services/         # Serviços auxiliares (Geração de PDFs e Excel)
│   ├── static/           # Arquivos estáticos (CSS, JS, Logos e Bibliotecas)
│   ├── templates/        # Templates HTML com Jinja2
│   ├── forms.py          # Formulários e validações (Flask-WTF / WTForms)
│   ├── models.py         # Mapeamento de Banco de Dados (Flask-SQLAlchemy)
│   └── routes.py         # Mapeamento central de rotas e decoradores
├── atualizar_banco.py    # Script de atualização/patch da estrutura de tabelas local
├── config.py             # Configurações dinâmicas de ambiente (Dev / Prod / Test)
├── main.py               # Ponto de entrada (WSGI) para deploy na Vercel
├── migrar_banco.py       # Script de migração massiva SQLite -> PostgreSQL (Neon)
├── requirements.txt      # Dependências do projeto Python
├── run.py                # Servidor de desenvolvimento local Flask
├── vercel.json           # Configuração de rotas e build na Vercel
└── README.md             # Documentação do projeto