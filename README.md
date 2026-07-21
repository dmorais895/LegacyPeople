# LegacyPeople

Uma aplicação web monolítica desenvolvida em Python e Django para a gestão, acolhimento e acompanhamento de pessoas e membros da igreja (Ministério Legacy / Lagoinha). O objetivo da aplicação é capturar informações fundamentais dos visitantes e membros (dados de contato, participação em Grupos de Crescimento, acompanhamento emocional, pedidos de oração e feedback sobre os cultos) de forma intuitiva, moderna e responsiva.

---

## 🏗 Arquitetura e Tech Stack

O projeto segue a arquitetura de **Monólito Django**, priorizando simplicidade de implantação, alta coesão e forte integridade de dados.

### Tecnologias Utilizadas

#### **Backend & Core**
- **Python 3.12+**: Linguagem base do projeto.
- **Django 4.2 LTS**: Framework web monolítico.
- **PyMySQL**: Conector nativo de banco de dados MySQL para Python.
- **Gunicorn**: Servidor WSGI de produção para ambientes em container.
- **WhiteNoise**: Servidor de arquivos estáticos de alta performance integrado ao Django.

#### **Frontend & UI/UX**
- **Bootstrap 5**: Layouts responsivos e grid do sistema.
- **Dart Sass (SCSS)**: Arquitetura modular de estilos (`_variables.scss`, `_layout.scss`, `_components.scss`) utilizando o padrão moderno `@use`.
- **Django Compressor**: Pré-compilação e minificação automática de SCSS/CSS.
- **Design System Glassmorphism**: Interface visual em tons suaves de acrílico e gradientes avermelhados, totalmente responsiva.

#### **Qualidade de Código & Testes**
- **Pylint & pylint-django**: Análise estática com nota máxima de qualidade (**10.00 / 10**).
- **Django Test Runner**: Suíte de testes automatizados integrada cobrindo regras de negócio, validações de formulário (WhatsApp, E-mail) e rotas.

#### **DevOps & CI/CD**
- **Docker & Docker Compose**: Conteinerização de produção e desenvolvimento isolado.
- **GitHub Actions**:
  - `Feature CI`: Validação automatizada de Pylint (nota 10/10) e testes em matriz de versões do Python.
  - `Develop CI`: Build automatizado e publicação de imagens Docker no GitHub Container Registry (GHCR).

---

## 📋 Pré-requisitos e Dependências

Para executar o projeto localmente ou em containers, você precisará das seguintes dependências instaladas na sua máquina:

1. **Python 3.12+** e **pip**
2. **Node.js 20+** e **npm** (necessário para o compilador do Dart Sass via `npx sass`)
3. **MySQL 8.0** (ou executá-lo via Docker)
4. **Docker** e **Docker Compose** *(opcional, mas recomendado)*

---

## 🚀 Como Executar o Projeto em Desenvolvimento

Você pode rodar o ambiente de desenvolvimento de duas formas:

### Opção 1: Rodando via Docker Compose (Recomendado)

Esta forma sobe automaticamente o container da aplicação e o container do banco de dados MySQL 8.0 pré-configurado.

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/dmorais895/LegacyPeople.git
   cd LegacyPeople
   ```

2. **Inicie os containers:**
   ```bash
   docker compose -f devops/docker-compose.yml up --build
   ```

3. **Acesse a aplicação:**
   Abra o navegador em `http://localhost:8000`. As migrações do banco de dados e arquivos estáticos serão executados automaticamente pelo `entrypoint.sh`.

---

### Opção 2: Rodando Localmente com Ambiente Virtual Python (`venv`)

1. **Inicie o serviço do MySQL** (ou suba apenas o banco via Docker):
   ```bash
   docker compose -f devops/docker-compose.yml up db -d
   ```

2. **Crie e ative o ambiente virtual:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instale as dependências de desenvolvimento:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements-dev.txt
   npm install
   ```

4. **Execute as migrações do banco de dados:**
   ```bash
   python manage.py migrate
   ```

5. **Inicie o servidor de desenvolvimento:**
   ```bash
   python manage.py runserver
   ```

6. **Execute os testes e o linter:**
   ```bash
   # Executar os testes automatizados
   python manage.py test

   # Executar a verificação do Pylint
   pylint core legacy_people
   ```

---

## 👤 Autor

Desenvolvido por **David Morais**  
- **GitHub:** [@dmorais895](https://github.com/dmorais895)  
- **Projeto:** LegacyPeople — Ministério Legacy / Igreja Lagoinha
