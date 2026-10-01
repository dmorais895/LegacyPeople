# LegacyPeople

Uma aplicação web monolítica desenvolvida em **Python** e **Django** para a gestão, acolhimento e acompanhamento de pessoas e membros da igreja (Ministério Legacy / Lagoinha). O objetivo da aplicação é capturar informações fundamentais dos visitantes e membros — dados de contato, participação em Grupos de Crescimento, acompanhamento emocional, pedidos de oração e feedback sobre os cultos — de forma intuitiva, moderna e responsiva.

---

## 🏗 Arquitetura e Tech Stack

O projeto segue a arquitetura de **Monólito Django**, priorizando simplicidade de implantação, alta coesão e forte integridade de dados.

### Tecnologias Utilizadas

#### **Backend & Core**
- **Python 3.12**: Mesma versão em desenvolvimento local, CI e Docker (`python:3.12-slim`).
- **Django 4.2 LTS**: Framework web monolítico.
- **PyMySQL**: Conector nativo de banco de dados MySQL para Python.
- **Gunicorn**: Servidor WSGI de produção para ambientes em container.
- **WhiteNoise**: Servidor de arquivos estáticos de alta performance integrado ao Django.

#### **Frontend & UI/UX**
- **Bootstrap 5 + Bootstrap Icons**: Layouts responsivos, grid do sistema e ícones vetoriais.
- **Dart Sass (SCSS)**: Arquitetura modular de estilos (`_variables.scss`, `_layout.scss`, `_components.scss`) utilizando o padrão moderno `@use`.
- **Django Compressor**: Pré-compilação e minificação automática de SCSS/CSS.
- **Design System Glassmorphism**: Interface visual em tons suaves de acrílico e gradientes dourados (`#f5c701`), totalmente responsiva.
- **Modais Estatísticos Reutilizáveis & Paginados**: Modal unificado via AJAX (`#statModal`) com paginação de até 10 pessoas por página, transição suave de opacidade, altura padronizada, rolagens internas nos cartões e botões diretos de integração com WhatsApp.

#### **Segurança**
- Proteção contra **Brute Force** no login (5 tentativas por IP em 15 minutos) e abuso do formulário (20 submissões por IP por hora), com contadores atômicos compartilhados no banco de dados.
- `X-Forwarded-For` é ignorado por padrão; somente proxies explicitamente configurados em `TRUSTED_PROXY_CIDRS` podem informar o IP do cliente.
- Dashboard e respostas AJAX exigem uma conta ativa com status de equipe (`is_staff`) e permissão `legacy_people.view_person`; o login administrativo aplica a mesma regra.
- Sanitização de campos via `strip_tags()` e validações de comprimento máximo para prevenção de **XSS Stored** e **DoS**.
- Escape de dados do servidor no frontend (função `esc()`) para prevenção de **XSS Client-Side**.
- **CSRF**, **Clickjacking** (`X-Frame-Options: DENY`) e **HSTS** configurados.
- Flags seguras nos cookies de sessão e CSRF (`HttpOnly`, `SameSite`, `Secure`).

#### **Qualidade de Código & Testes**
- **Pylint & pylint-django**: Análise estática com nota máxima de qualidade (**10.00 / 10**).
- **Django Test Runner**: Suíte automatizada cobrindo regras de negócio, validações de formulário, modais estatísticos paginados, segurança, autorização e rate limiting concorrente.


#### **DevOps & CI/CD**
- **Docker & Docker Compose**: Conteinerização de produção e desenvolvimento isolado.
- **GitHub Actions**:
  - `Feature CI`: Validação automatizada de Pylint (nota 10/10) e testes com Python 3.12, selecionado pelo arquivo `.python-version`.
  - `Develop CI`: Build automatizado e publicação de imagens Docker no GitHub Container Registry (GHCR).

---

## 📋 Pré-requisitos

| Dependência | Versão mínima | Necessidade |
|---|---|---|
| Python | 3.12.x | Sempre necessário; outras versões menores não são suportadas |
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
| `TRUSTED_PROXY_CIDRS` | Não | Vazio | IPs/CIDRs dos proxies confiáveis, separados por vírgula. Vazio ignora `X-Forwarded-For`. |
| `SITE_DOMAIN` | Compose prod. | — | Hostname público servido por Caddy, sem protocolo ou caminho. Também define `ALLOWED_HOSTS` neste stack. |
| `PROXY_SUBNET` | Não | `172.30.0.0/24` | Subrede privada do stack de produção. |
| `PROXY_IP` | Não | `172.30.0.10` | IPv4 do Caddy dentro de `PROXY_SUBNET`; somente este IP é confiável no stack de produção. |
| `DB_ENGINE` | Não | `django.db.backends.mysql` | Use `django.db.backends.sqlite3` para desenvolvimento sem MySQL |
| `DB_NAME` | MySQL | `legacypeople` | Nome do banco de dados MySQL |
| `DB_USER` | MySQL | `django` | Usuário do banco de dados MySQL |
| `DB_PASSWORD` | MySQL | `django` | Senha do usuário MySQL |
| `DB_HOST` | MySQL | `127.0.0.1` | Host do servidor MySQL |
| `DB_PORT` | MySQL | `3306` | Porta do servidor MySQL |
| `DB_ROOT_PASSWORD` | Docker | `root` | Senha root do MySQL (usado apenas no Docker Compose) |

> **Dica para desenvolvimento rápido com SQLite:** defina `DB_ENGINE=django.db.backends.sqlite3` e as variáveis `DB_*` de MySQL podem ser ignoradas.

Os limites usam janelas fixas: novas tentativas não prolongam o prazo. Os contadores são compartilhados entre processos e containers que usam o mesmo banco. Execute `python manage.py migrate` antes de iniciar a versão atualizada.

Atrás de um proxy reverso, configure `TRUSTED_PROXY_CIDRS` com os IPs/CIDRs exatos dos proxies sob seu controle. Eles devem remover o `X-Forwarded-For` recebido ou acrescentar o IP real da conexão ao final. A aplicação percorre a cadeia da direita para a esquerda e para no primeiro IP não confiável, inclusive endereços privados. Não confie em todas as redes (`0.0.0.0/0` ou `::/0`); restrinja também o acesso direto ao servidor da aplicação.

Agende `python manage.py cleanup_rate_limits` periodicamente para remover contadores expirados. O comando preserva os limites ativos.

---

## 🚀 Como Executar o Projeto em Desenvolvimento

Instale Python **3.12** antes de criar o ambiente virtual. O arquivo `.python-version` define essa versão para ferramentas compatíveis; os comandos abaixo selecionam explicitamente o interpretador. A aplicação recusa iniciar com outras versões menores. Se já houver um `venv` criado com outra versão, recrie-o com Python 3.12 e reinstale `requirements-dev.txt`.

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
python3.12 -m venv venv
# Windows: py -3.12 -m venv venv
source venv/bin/activate       # Linux/macOS
# venv\Scripts\activate        # Windows
python --version              # Deve mostrar Python 3.12.x
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

Superusuários têm acesso ao dashboard automaticamente. Para outras contas administrativas, marque **Ativo** e **Membro da equipe** no Django Admin e conceda a permissão **Can view Pessoa** (`legacy_people.view_person`), diretamente ou por um grupo. Contas sem esses requisitos não podem entrar pela área administrativa; sessões existentes recebem HTTP 403 ao acessar o dashboard após a revogação do acesso.

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
python3.12 -m venv venv
source venv/bin/activate
python --version              # Deve mostrar Python 3.12.x
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

### Opção 3: Via Docker Compose

O Docker Compose sobe simultaneamente o container da aplicação e o MySQL 8.0.
O container executa as migrações e coleta os arquivos estáticos antes de iniciar. Sem um comando explícito, `DEBUG=True` seleciona `runserver`; qualquer outro valor seleciona Gunicorn. Comandos explícitos, como `python manage.py createsuperuser`, têm precedência.

#### 🛠️ Container de Desenvolvimento (`DEBUG=True`)

```bash
git clone https://github.com/dmorais895/LegacyPeople.git
cd LegacyPeople
cp .env.example .env
```

Edite o `.env` para o modo desenvolvimento:
```dotenv
SECRET_KEY=qualquer-string-longa-aqui
DEBUG=True
ALLOWED_HOSTS=          # Pode deixar vazio em DEBUG=True
DB_NAME=legacypeople
DB_USER=django
DB_PASSWORD=django
DB_ROOT_PASSWORD=root
```

```bash
docker compose --env-file .env -f devops/docker-compose.yml up --build
```

O servidor de desenvolvimento fica disponível em `http://127.0.0.1:8000`. As portas da aplicação e do MySQL são publicadas somente em loopback.

#### 🚀 Container de Produção (`DEBUG=False`)

```bash
cp .env.example .env
```

Edite o `.env` para o modo produção:
```dotenv
SECRET_KEY=<chave-gerada-com-get_random_secret_key>
DEBUG=False
SITE_DOMAIN=legacypeople.com.br
DB_NAME=legacypeople
DB_USER=django
DB_PASSWORD=<senha-forte>
DB_ROOT_PASSWORD=<senha-root-forte>
```

```bash
docker compose --env-file .env -f devops/docker-compose.prod.yml up -d --build
```

Use o arquivo de produção sozinho, sem combiná-lo com `docker-compose.yml`. Ele força `DEBUG=False`, inicia Gunicorn e adiciona Caddy como proxy HTTPS. Apenas as portas 80 e 443 são públicas; aplicação e MySQL ficam na rede privada. O IP fixo do Caddy configura automaticamente a confiança usada pelo rate limiter. Se a subrede conflitar com outra rede do host, ajuste `PROXY_SUBNET` e `PROXY_IP` juntos.

Antes de iniciar, aponte os registros DNS A/AAAA de `SITE_DOMAIN` para o servidor e permita conexões externas nas portas 80 e 443. O Caddy obtém e renova os certificados automaticamente e redireciona HTTP para HTTPS. Os certificados ficam no volume persistente `caddy_data`. Referência: [HTTPS automático do Caddy](https://caddyserver.com/docs/automatic-https).

> **⚠️ Atenção:** O `entrypoint.sh` valida a presença de `SECRET_KEY` antes de iniciar o servidor. O container falha imediatamente com uma mensagem clara caso ela não esteja definida.

Acesse a produção em `https://<SITE_DOMAIN>`.

---

## 🧪 Testes e Qualidade de Código

```bash
# Ativar o ambiente virtual
source venv/bin/activate

# Executar os testes automatizados com SQLite

DB_ENGINE=django.db.backends.sqlite3 python manage.py test

# Para incluir o teste de concorrência, use um banco SQLite de teste em arquivo:
DB_ENGINE=django.db.backends.sqlite3 SQLITE_TEST_DB_PATH=/tmp/legacypeople-tests.sqlite3 python manage.py test

# Executar a verificação de qualidade com Pylint (nota mínima: 10.00/10)
pylint --fail-under=10.0 manage.py core legacy_people
```

---

## 👤 Autor

Desenvolvido por **David Morais**
- **GitHub:** [@dmorais895](https://github.com/dmorais895)
- **Projeto:** LegacyPeople — Ministério Legacy / Igreja Lagoinha
