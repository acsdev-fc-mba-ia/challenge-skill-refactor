# Desafio: Refatoração Arquitetural com Skills

Rode o projeto com Dev Containers.

_Como o projeto foi modificado para usar devcontainers, modifiquei *localhost* por *127.0.0.1*_

## Como rodar os projetos

### code-smells-project

```bash
cd code-smells-project
python3 -m venv venv &&. venv/bin/activate # Criar ambiente virtual
pip install -r requirements.txt
python app.py

# Acessar API em http://127.0.0.1:5000
deactivate # Execute deactivate para sair do ambiente virtual
```

### ecommerce-api-legacy

A applicação tem um arquivo api.http para testar os endpoints manualmente

```bash
cd ecommerce-api-legacy
npm install
npm start
# Accessible at http://127.0.0.1:3000
# In-memory database auto-populated on startup
```

### task-manager-api

```bash
cd task-manager-api
python3 -m venv venv &&. venv/bin/activate # Criar ambiente virtual
pip install -r requirements.txt
python seed.py  # prepare os dados                  
python app.py
# Accessible at http://127.0.0.1:5000
deactivate # Execute deactivate para sair do ambiente virtual
```

## A) Análise Manual

Análise manual dos três projetos legados, identificando problemas de arquitetura, segurança e qualidade de código classificados por severidade.

---

### Projeto 1 — `code-smells-project` (Python/Flask — API de E-commerce)

**Stack:** Python + Flask 3.1.1 ; **Banco:** SQLite (`loja.db`)

| # | Severidade | Problema | Arquivo |
|---|---|---|---|
| 1 | CRITICAL | SQL Injection via concatenação de strings | `models.py` |
| 2 | CRITICAL | Endpoint de execução arbitrária de SQL sem autenticação | `app.py` |
| 3 | CRITICAL | `SECRET_KEY` e `DEBUG=True` hardcoded | `app.py` |
| 4 | HIGH | `secret_key` exposta publicamente na resposta do endpoint `/health` | `controllers.py` |
| 5 | HIGH | Senhas armazenadas e comparadas em texto plano, sem hash | `models.py` |
| 6 | MEDIUM | N+1 Query: para cada pedido, N queries extras para itens e nomes de produtos | `models.py` |
| 7 | MEDIUM | Endpoint `/admin/reset-db` apaga todos os dados sem autenticação ou confirmação | `app.py` |
| 8 | LOW | Magic numbers nas regras de desconto (thresholds e percentuais hardcoded inline) | `models.py` |
| 9 | LOW | Lista de categorias válidas hardcoded no controller em vez de configuração/banco | `controllers.py` |

---

### Projeto 2 — `ecommerce-api-legacy` (Node.js/Express — LMS API)

**Stack:** Node.js + Express 4.18.2 ; **Banco:** SQLite in-memory

| # | Severidade | Problema | Arquivo |
|---|---|---|---|
| 1 | CRITICAL | God Class — `AppManager` centraliza DB, rotas, negócio, pagamento, auditoria e relatórios | `src/AppManager.js` |
| 2 | CRITICAL | Credenciais de produção hardcoded (DB, gateway de pagamento, SMTP) |
| 4 | HIGH | Callback Hell — checkout aninhado em 5 níveis de callbacks (course → user → enroll → payment → audit) | `src/AppManager.js` |
| 5 | HIGH | Race condition — contadores decrementados em callbacks async paralelos sem lock/mutex | `src/AppManager.js` |
| 6 | MEDIUM | Validação de entrada insuficiente no checkout — verifica apenas presença, não formato/tipo | `src/AppManager.js` |
| 7 | MEDIUM | Deleção de usuário sem cascata — matrículas e pagamentos ficam órfãos no banco | `src/AppManager.js` |
| 8 | LOW | Variáveis com nomes de 1–2 letras sem semântica (`u`, `e`, `p`, `cid`, `cc`) | `src/AppManager.js` |
| 9 | LOW | Lógica de aprovação de pagamento como magic number (`cc.startsWith("4")` = Visa, sem constante) | `src/AppManager.js` |

---

### Projeto 3 — `task-manager-api` (Python/Flask — API de Task Manager)

**Stack:** Python + Flask 3.0.0 + SQLAlchemy ; **Banco:** SQLite (`tasks.db`)

| # | Severidade | Problema | Arquivo |
|---|---|---|---|
| 1 | CRITICAL | Credenciais SMTP hardcoded apesar de `python-dotenv` já estar nas dependências | `services/notification_service.py` |
| 2 | HIGH | `SECRET_KEY` hardcoded no `app.py` — infraestrutura `.env` disponível mas ignorada | `app.py` |
| 3 | MEDIUM | N+1 Query — para cada task, queries separadas para `User` e `Category` sem eager loading | `routes/task_routes.py` |
| 4 | MEDIUM | `except:` sem tipo captura `KeyboardInterrupt` e `SystemExit`, silenciando erros críticos | `routes/task_routes.py` |
| 5 | LOW | Imports não utilizados (`json`, `os`, `sys`, `time`) presentes em múltiplos arquivos | `routes/task_routes.py`, `app.py` |
| 6 | LOW | `print()` usado como logging sem logger configurado — sem nível, sem formato, sem destino | `routes/task_routes.py` |

**Justificativas dos achados mais relevantes:**

---

## B) Construção da Skill

> _Seção a ser preenchida após a criação da skill (`/refactor-arch`)._

---

## C) Resultados

> _Seção a ser preenchida após a execução da skill nos 3 projetos._

---
