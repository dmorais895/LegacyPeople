# LegacyPeople

Uma aplicação web monolítica desenvolvida em **Python** e **Django** para a gestão, acolhimento e acompanhamento de pessoas e membros da igreja (Ministério Legacy / Lagoinha). O objetivo da aplicação é capturar informações fundamentais dos visitantes e membros — dados de contato, participação em Grupos de Crescimento, acompanhamento emocional, pedidos de oração e feedback sobre os cultos — de forma intuitiva, moderna e responsiva.

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
- **Bootstrap 5 + Bootstrap Icons**: Layouts responsivos, grid do sistema e ícones vetoriais.
- **Dart Sass (SCSS)**: Arquitetura modular de estilos (`_variables.scss`, `_layout.scss`, `_components.scss`) utilizando o padrão moderno `@use`.
- **Django Compressor**: Pré-compilação e minificação automática de SCSS/CSS.
- **Design System Glassmorphism**: Interface visual em tons suaves de acrílico e gradientes avermelhados, totalmente responsiva.

#### **Segurança**
- Proteção contra **Brute Force** no login (rate limiting por IP via Django Cache).
- Sanitização de campos via `strip_tags()` e validações de comprimento máximo para prevenção de **XSS Stored** e **DoS**.
- Escape de dados do servidor no frontend (função `esc()`) para prevenção de **XSS Client-Side**.
- **CSRF**, **Clickjacking** (`X-Frame-Options: DENY`) e **HSTS** configurados.
- Flags seguras nos cookies de sessão e CSRF (`HttpOnly`, `SameSite`, `Secure`).

#### **Qualidade de Código & Testes**
- **Pylint & pylint-django**: Análise estática com nota máxima de qualidade (**10.00 / 10**).
- **Django Test Runner**: Suíte com **30 testes automatizados** cobrindo regras de negócio, validações de formulário, segurança e rate limiting.

#### **DevOps & CI/CD**
- **Docker & Docker Compose**: Conteinerização de produção e desenvolvimento isolado.
- **GitHub Actions**:
  - `Feature CI`: Validação automatizada de Pylint (nota 10/10) e testes em matriz de versões do Python.
  - `Develop CI`: Build automatizado e publicação de imagens Docker no GitHub Container Registry (GHCR).

---

## 📋 Pré-requisitos

| Dependência | Versão mínima | Necessidade |
|---|---|---|
| Python | 3.12+ | Sempre necessário |
| pip | Última | Sempre necessário |
| Node.js + npm | 20+ | Sempre necessário (compilador Dart Sass via `npx sass`) |
| MySQL | 8.0 | Apenas para banco MySQL (opcional em dev com SQLite) |
| Docker + Docker Compose | Qualquer | Apenas para rodar via containers |

---

## ⚙️ Configuração do Ambiente (`.env`)

A aplicação usa variáveis de ambiente para todas as configurações sensíveis. **Antes de executar**, crie seu `.env` a partir do arquivo de exemplo:

```bash
cp .env.example .env
```

Em seguida, edite o `.env` gerado. Abaixo está a referência completa de cada variável:

| Variável | Obrigatória | Padrão | Descrição |
|---|---|---|---|
| `SECRET_KEY` | ✅ Sim | — | Chave criptográfica do Django. Gere com `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DEBUG` | ✅ Sim | `False` | `True` em desenvolvimento. **Nunca `True` em produção.** |
| `ALLOWED_HOSTS` | Prod. | `*` (quando DEBUG=True) | Hosts permitidos, separados por vírgula. Ex: `legacypeople.com.br` |
| `DB_ENGINE` | Não | `django.db.backends.mysql` | Use `django.db.backends.sqlite3` para desenvolvimento sem MySQL |
| `DB_NAME` | MySQL | `legacypeople` | Nome do banco de dados MySQL |
| `DB_USER` | MySQL | `django` | Usuário do banco de dados MySQL |
| `DB_PASSWORD` | MySQL | `django` | Senha do usuário MySQL |
| `DB_HOST` | MySQL | `127.0.0.1` | Host do servidor MySQL |
| `DB_PORT` | MySQL | `3306` | Porta do servidor MySQL |
| `DB_ROOT_PASSWORD` | Docker | `root` | Senha root do MySQL (usado apenas no Docker Compose) |

> **Dica para desenvolvimento rápido com SQLite:** defina `DB_ENGINE=django.db.backends.sqlite3` e as variáveis `DB_*` de MySQL podem ser ignoradas.

---

## 🚀 Como Executar o Projeto em Desenvolvimento

Você pode rodar o ambiente de desenvolvimento de duas formas:

---

### Opção 1: Localmente com SQLite (Mais Rápido)

Ideal para desenvolvimento rápido, **sem necessidade de MySQL ou Docker**.

**1. Clone o repositório:**
```bash
git clone https://github.com/dmorais895/LegacyPeople.git
cd LegacyPeople
```

**2. Crie e ative o ambiente virtual:**
```bash
python3 -m venv venv
source venv/bin/activate       # Linux/macOS
# venv\Scripts\activate        # Windows
```

**3. Instale as dependências:**
```bash
pip install --upgrade pip
pip install -r requirements-dev.txt
npm install
```

**4. Configure o ambiente:**
```bash
cp .env.example .env
```

Edite o `.env` e ajuste no mínimo estas três variáveis:
```dotenv
SECRET_KEY=qualquer-string-longa-aqui
DEBUG=True
DB_ENGINE=django.db.backends.sqlite3
```

**5. Execute as migrações:**
```bash
python manage.py migrate
```

**6. Crie um superusuário para acessar o painel administrativo:**
```bash
python manage.py createsuperuser
```

**7. Inicie o servidor de desenvolvimento:**
```bash
python manage.py runserver
```

Acesse a aplicação em `http://127.0.0.1:8000`.

---

### Opção 2: Localmente com MySQL via Docker Compose

Ideal para testar a aplicação com o banco de dados de produção.

**1. Clone o repositório:**
```bash
git clone https://github.com/dmorais895/LegacyPeople.git
cd LegacyPeople
```

**2. Configure o ambiente:**
```bash
cp .env.example .env
```

Edite o `.env` com as credenciais do MySQL:
```dotenv
SECRET_KEY=qualquer-string-longa-aqui
DEBUG=True
DB_ENGINE=django.db.backends.mysql
DB_NAME=legacypeople
DB_USER=django
DB_PASSWORD=django
DB_HOST=127.0.0.1
DB_PORT=3306
DB_ROOT_PASSWORD=root
```

**3. Suba apenas o banco de dados MySQL:**
```bash
docker compose -f devops/docker-compose.yml up db -d
```

**4. Crie e ative o ambiente virtual e instale as dependências:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements-dev.txt
npm install
```

**5. Execute as migrações e crie o superusuário:**
```bash
python manage.py migrate
python manage.py createsuperuser
```

**6. Inicie o servidor:**
```bash
python manage.py runserver
```

---

### Opção 3: Ambiente Completo via Docker Compose

Sobe simultaneamente o container da aplicação e o MySQL 8.0 pré-configurado.

```bash
git clone https://github.com/dmorais895/LegacyPeople.git
cd LegacyPeople
cp .env.example .env  # Edite conforme necessário
docker compose -f devops/docker-compose.yml up --build
```

Acesse em `http://localhost:8000`. As migrações e arquivos estáticos são executados automaticamente pelo `entrypoint.sh`.

---

## 🧪 Testes e Qualidade de Código

```bash
# Ativar o ambiente virtual
source venv/bin/activate

# Executar todos os 30 testes automatizados (com SQLite, sem configuração adicional)
DB_ENGINE=django.db.backends.sqlite3 python manage.py test

# Executar a verificação de qualidade com Pylint (nota mínima: 10.00/10)
pylint --fail-under=10.0 manage.py core legacy_people
```

---

## 👤 Autor

Desenvolvido por **David Morais**
- **GitHub:** [@dmorais895](https://github.com/dmorais895)
- **Projeto:** LegacyPeople — Ministério Legacy / Igreja Lagoinha
