# Resultado da Análise — Plano de Construção da Skill `refactor-arch`

> Documento gerado a partir da análise consolidada de `CLAUDE.md`, `README.Challenge-Description.md` e `task-manager-api/README.md`. Serve como blueprint para a construção da Skill `refactor-arch` em `<repo-root>/.claude/skills/refactor-arch/` (diretório raiz do repositório).

---

## 1. Visão Geral do Desafio

Criar uma **Skill agnóstica de tecnologia** que automatiza três fases sequenciais sobre qualquer codebase backend:

1. **Fase 1 — Análise:** detectar stack (linguagem, framework, banco, domínio, arquitetura atual).
2. **Fase 2 — Auditoria:** cruzar o código contra um catálogo de anti-patterns, gerar relatório com severidade + arquivo:linha, **pausar para confirmação do usuário**.
3. **Fase 3 — Refatoração:** reestruturar para MVC, validar que a aplicação sobe e os endpoints respondem.

A skill deve funcionar em **três projetos com stacks e níveis de organização distintos**:

| Projeto | Stack | Estado |
|---|---|---|
| `code-smells-project` | Python/Flask | Monolítico, 4 arquivos, raw SQL |
| `ecommerce-api-legacy` | Node.js/Express | God Class única (`AppManager`) |
| `task-manager-api` | Python/Flask | Parcialmente organizado (models/, routes/, services/) |

---

## 2. Trabalho Necessário (Resumo Executivo)

| Etapa | Entregável | Esforço estimado |
|---|---|---|
| 2.1 | Análise manual documentada dos 3 projetos | Baixo (já temos o mapa em CLAUDE.md) |
| 2.2 | Criar `.claude/skills/refactor-arch/` na **raiz do repositório** (`/workspace/.claude/skills/refactor-arch/`) com `SKILL.md` + 5 arquivos de referência | Alto |
| 2.3 | Após finalizar e validar a skill, copiar manualmente para dentro de cada projeto (`code-smells-project/`, `ecommerce-api-legacy/`, `task-manager-api/`) | Baixo |
| 2.4 | Executar a skill nos 3 projetos, salvar `reports/audit-project-{1,2,3}.md` | Médio |
| 2.5 | Commitar o código refatorado dos 3 projetos | Médio |
| 2.6 | Atualizar `README.md` raiz com as seções A, B, C, D | Médio |

---

## 3. Análise Manual Consolidada (insumo para o catálogo)

### 3.1 `code-smells-project` (Python/Flask Monolito)

| # | Problema | Severidade | Local |
|---|---|---|---|
| 1 | SQL Injection via concatenação | CRITICAL | `models.py` (várias) |
| 2 | `SECRET_KEY` hardcoded | CRITICAL | `app.py:7` |
| 3 | Endpoint `/admin/query` executa SQL arbitrário | CRITICAL | `app.py:59-78` |
| 4 | God File (lógica + dados + transformação) | CRITICAL | `models.py` (314 LOC) |
| 5 | Mistura HTTP + negócio + DB | HIGH | `controllers.py` |
| 6 | Validação de input ausente/inconsistente | HIGH | `controllers.py` |
| 7 | Sem ORM, schema manual | HIGH | `database.py` |
| 8 | `DEBUG = True` em produção | MEDIUM | `app.py:8` |
| 9 | `except Exception` genérico sem logging | MEDIUM | `controllers.py` |

### 3.2 `ecommerce-api-legacy` (Node.js/Express)

| # | Problema | Severidade | Local |
|---|---|---|---|
| 1 | God Class `AppManager` (141 LOC, tudo dentro) | CRITICAL | `src/AppManager.js` |
| 2 | Credenciais DB/gateway/SMTP hardcoded | CRITICAL | `src/utils.js:2-4` |
| 3 | "Hashing" via base64 × 10.000 (não é cripto) | CRITICAL | `src/utils.js:17-23` |
| 4 | Design frágil que convida a SQLi | HIGH | `src/AppManager.js` |
| 5 | Estado global mutável (`globalCache`, `totalRevenue`) | HIGH | `src/utils.js:9-10` |
| 6 | Callback hell aninhado | HIGH | `src/AppManager.js:40-77` |
| 7 | Validação mínima no `/api/checkout` | MEDIUM | `src/AppManager.js:28-34` |
| 8 | Race condition em contador de callbacks | MEDIUM | `src/AppManager.js:86-98` |

### 3.3 `task-manager-api` (Python/Flask parcialmente layered)

| # | Problema | Severidade | Local |
|---|---|---|---|
| 1 | SMTP hardcoded (mesmo com `python-dotenv` instalado) | CRITICAL | `services/notification_service.py:9-10` |
| 2 | `SECRET_KEY` hardcoded | HIGH | `app.py:13` |
| 3 | Business logic e cálculo de overdue dentro das routes | HIGH | `routes/task_routes.py` |
| 4 | N+1 queries em `GET /tasks` | MEDIUM | `routes/task_routes.py:41-57` |
| 5 | `except:` bare (engole `KeyboardInterrupt`) | MEDIUM | `routes/task_routes.py:62` |
| 6 | Lógica de overdue duplicada em model + route | MEDIUM | `models/task.py` vs `routes/task_routes.py` |

> **Observação:** os 3 projetos atendem os critérios mínimos de severidade (≥1 CRITICAL/HIGH, ≥2 MEDIUM, ≥2 LOW após complementação com itens de naming/magic numbers).

---

## 4. Estrutura da Skill (proposta de arquivos)

```
/workspace/                              ← raiz do repositório
└── .claude/
    └── skills/
        └── refactor-arch/              ← skill criada aqui
            ├── SKILL.md                # Entry point: prompt das 3 fases
            ├── 01-project-analysis.md  # Heurísticas de Fase 1 (detecção de stack)
            ├── 02-antipattern-catalog.md # Catálogo de ≥8 anti-patterns + deprecated APIs
            ├── 03-report-template.md   # Template Markdown do relatório de auditoria
            ├── 04-architecture-guidelines.md # Padrão MVC alvo
            └── 05-refactor-playbook.md # ≥8 padrões antes/depois (code transformations)
```

> **Após finalização:** copiar a pasta `refactor-arch/` inteira para dentro de cada projeto:
> - `code-smells-project/.claude/skills/refactor-arch/`
> - `ecommerce-api-legacy/.claude/skills/refactor-arch/`
> - `task-manager-api/.claude/skills/refactor-arch/`

**Por que essa divisão?**
- Cada arquivo cobre **uma das 5 áreas obrigatórias** listadas no challenge.
- `SKILL.md` permanece curto e age como orquestrador, **lazy-loading** os arquivos de referência conforme a fase.
- Numeração no nome dá ordem natural de leitura para humanos auditando a skill.

---

## 5. Conteúdo de Cada Arquivo

### 5.1 `SKILL.md` (orquestrador)

**Frontmatter obrigatório:**
```yaml
---
name: refactor-arch
description: Audits any backend codebase against a catalog of anti-patterns, then refactors it into MVC. Runs in 3 phases (analyze → audit → refactor) and is stack-agnostic.
---
```

**Corpo:** instruções imperativas em inglês curtas:
1. Início ⇒ executar Fase 1 carregando `01-project-analysis.md`.
2. Imprimir o resumo no formato fixo de banner (`================`).
3. Carregar `02-antipattern-catalog.md` + `03-report-template.md`, varrer o código, emitir relatório.
4. **Bloqueio obrigatório:** perguntar `Proceed with refactoring (Phase 3)? [y/n]` e parar até receber confirmação.
5. Em `y` ⇒ carregar `04-architecture-guidelines.md` + `05-refactor-playbook.md`, executar transformações.
6. Validação final: `boot da aplicação` + `curl/http nos endpoints originais` + comparar respostas.

### 5.2 `01-project-analysis.md` (Heurísticas de detecção)

**Sinais a procurar (em ordem):**
- `package.json` ⇒ Node.js; ler `dependencies` para descobrir framework (`express`, `fastify`, `koa`).
- `requirements.txt` / `pyproject.toml` / `Pipfile` ⇒ Python; framework via imports (`flask`, `fastapi`, `django`).
- `go.mod`, `pom.xml`, `Gemfile`, `composer.json` ⇒ Go/Java/Ruby/PHP (mesmo padrão).
- **Banco:** procurar SQL nativo, ORMs comuns (`sqlalchemy`, `sequelize`, `prisma`, `typeorm`), driver direto (`sqlite3`, `psycopg2`).
- **Arquitetura atual:** contar arquivos por diretório raiz; presença de `models/`, `routes/`, `controllers/`, `services/` indica nível de organização.
- **Domínio:** inferir do nome das rotas/tabelas (`produtos/pedidos` ⇒ e-commerce; `tasks/users` ⇒ task manager; `checkout/courses` ⇒ LMS).

**Output formatado:** banner ASCII fixo com `Language`, `Framework`, `Dependencies`, `Domain`, `Architecture`, `Source files`, `DB tables`.

### 5.3 `02-antipattern-catalog.md` (≥8 anti-patterns)

| # | Anti-pattern | Severidade | Sinal de detecção |
|---|---|---|---|
| 1 | Hardcoded secrets/credentials | CRITICAL | Regex em strings literais com `SECRET_KEY`, `PASSWORD`, `API_KEY`, `SMTP_PASS`, `DB_PASS` |
| 2 | SQL Injection via concatenação | CRITICAL | `"SELECT ... " + var` ou f-strings com SQL |
| 3 | God Class / God File | CRITICAL | Arquivo >250 LOC com responsabilidades múltiplas (rotas + DB + crypto) |
| 4 | Endpoint admin sem auth executando SQL | CRITICAL | Rota que recebe `query`/`sql` no body e chama `execute()` |
| 5 | Business logic dentro de rotas/controllers | HIGH | Cálculos não-triviais entre `@app.route` e `return jsonify(...)` |
| 6 | Estado global mutável | HIGH | Variáveis de módulo reescritas em runtime (`globalCache.x = ...`) |
| 7 | Callback hell / falta de async-await | HIGH | ≥3 callbacks aninhados em Node |
| 8 | Weak/custom crypto | CRITICAL | `base64` repetido, MD5/SHA1 para senha, hash sem salt |
| 9 | N+1 queries | MEDIUM | Query dentro de `for` sobre resultado de outra query |
| 10 | Bare `except:` / `catch (e)` engolido | MEDIUM | `except:` sem tipo; `catch (e) {}` vazio |
| 11 | `DEBUG = True` em produção | MEDIUM | Flag de debug em config padrão |
| 12 | Código duplicado (DRY) | MEDIUM | Mesma lógica em ≥2 lugares (overdue calc em model + route) |
| 13 | **APIs deprecated** | MEDIUM | `flask.ext.*`, `request.get_json(force=True)` deprecated, `crypto.createCipher`, `new Buffer()` no Node, `datetime.utcnow()` (deprecated em Python 3.12+) |
| 14 | Magic numbers / strings | LOW | Literais numéricos repetidos sem constante (`status == 1`) |
| 15 | Naming ruim | LOW | Variáveis `x`, `data`, `tmp`, `aux` em funções não-triviais |

> O catálogo precisa **mínimo 8**, mas com 15 cobrimos com folga + atendemos o requisito explícito de **detecção de APIs deprecated**.

### 5.4 `03-report-template.md` (Template do relatório)

Estrutura padronizada:

```markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <name>
Stack:   <language> + <framework>
Files:   <N> analyzed | ~<LOC> lines of code

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [SEVERITY] <Anti-pattern name>
File: <path>:<line-start>-<line-end>
Description: <what was found, concrete>
Impact: <why it matters>
Recommendation: <one-line action>

...(repeated, ordenado por severidade)

================================
Total: <n> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

**Regras de formatação:**
- Findings **ordenados** por severidade (CRITICAL → LOW).
- `file:line` obrigatório em todos.
- Frase de confirmação **literal** no final.

### 5.5 `04-architecture-guidelines.md` (Padrão MVC alvo)

Replicar a estrutura canônica do CLAUDE.md:

```
src/
├── config/         # Env-based config
├── models/         # ORM/entidades
├── controllers/    # Orquestração HTTP
├── routes/         # Roteamento puro
├── services/       # Lógica de negócio
├── middleware/     # Cross-cutting (error handler, auth, validation)
├── database.py     # Init do ORM
└── app.py          # Composition root mínimo
```

**Responsabilidades por camada (regra de ouro de uma linha cada):**
- **Routes:** mapear URL ⇒ controller. Zero lógica.
- **Controllers:** parse de request, chamar service, montar response. Zero acesso a DB.
- **Services:** regras de negócio. Zero referência a `request`/`response`.
- **Models:** entidades + queries via ORM. Zero HTTP.
- **Config:** ler `.env`, expor constantes. Imutável em runtime.
- **Middleware:** error handler centralizado, auth, validação de schema.

**Adaptação por stack:**
- Node/Express ⇒ `controllers/` + `routes/` + `services/` + `middleware/`.
- Python/Flask ⇒ mesma estrutura, blueprints em `routes/`.

### 5.6 `05-refactor-playbook.md` (≥8 transformações antes/depois)

| # | Transformação | Aplica-se a |
|---|---|---|
| 1 | Hardcoded → `.env` + `config/settings.py` (ou `config/index.js`) | Anti-pattern #1 |
| 2 | Raw SQL → ORM (SQLAlchemy / Sequelize / Prisma) com parâmetros | Anti-patterns #2 |
| 3 | God File → quebra em `models/`, `controllers/`, `services/` por domínio | Anti-pattern #3 |
| 4 | Remoção/proteção do endpoint admin perigoso (delete ou auth + allow-list) | Anti-pattern #4 |
| 5 | Business logic em rotas → extrair para `services/<domain>_service.py` | Anti-pattern #5 |
| 6 | Estado global mutável → injetar via factory/DI ou cache encapsulado | Anti-pattern #6 |
| 7 | Callback hell → `async/await` + `util.promisify` | Anti-pattern #7 |
| 8 | Weak crypto → `bcrypt`/`argon2` (Node) ou `passlib`/`bcrypt` (Python) | Anti-pattern #8 |
| 9 | N+1 → `joinedload`/`selectinload` (SQLAlchemy) ou `include` (Sequelize) | Anti-pattern #9 |
| 10 | Bare `except:` → `except SpecificError as e:` + log estruturado | Anti-pattern #10 |
| 11 | `DEBUG = True` → `DEBUG = os.getenv("FLASK_ENV") == "development"` | Anti-pattern #11 |
| 12 | Duplicação de overdue → método único no model, chamado das routes | Anti-pattern #12 |
| 13 | APIs deprecated → substituição pontual (ex: `datetime.utcnow()` → `datetime.now(timezone.utc)`) | Anti-pattern #13 |

Cada transformação **deve trazer um bloco "before" e um bloco "after"** com código real. Mínimo 8 atende; entregamos 13.

---

## 6. Plano de Execução das 3 Fases

### Fase 1 — Análise (não-destrutiva)
1. Detectar manifest file e linguagem.
2. Ler arquivos-chave (entry point + diretórios principais).
3. Imprimir banner padronizado.

### Fase 2 — Auditoria (não-destrutiva, **pausa obrigatória**)
1. Para cada arquivo: aplicar grep/leitura contra catálogo.
2. Acumular findings com severidade.
3. Imprimir relatório seguindo template.
4. Salvar em `reports/audit-project-N.md`.
5. **Aguardar `[y/n]` antes de prosseguir.**

### Fase 3 — Refatoração (destrutiva, requer confirmação)
1. Criar estrutura MVC alvo.
2. Aplicar playbook na ordem CRITICAL → LOW.
3. Migrar arquivo por arquivo, **mantendo endpoints públicos inalterados**.
4. **Validação obrigatória:**
   - `pip install -r requirements.txt` / `npm install`
   - boot da app em background
   - **usar o arquivo `api.http` de cada projeto** para disparar os requests de validação (`curl` ou REST Client); cada projeto possui esse arquivo com os exemplos de request prontos
   - comparar status code e shape do JSON contra o estado pré-refatoração
   - imprimir checklist final ✓ / ✗

> **Nota sobre `api.http`:** todos os três projetos contêm um arquivo `api.http` na raiz com requests de exemplo para cada endpoint. A skill deve ler esse arquivo na Fase 3 para saber exatamente quais URLs, métodos e payloads usar na validação — sem depender de lista externa.

---

## 7. Checklist de Aceite (por projeto)

```
### Fase 1
- [ ] Linguagem detectada
- [ ] Framework detectado
- [ ] Domínio descrito
- [ ] Contagem de arquivos correta

### Fase 2
- [ ] Relatório segue o template
- [ ] file:line em todos os findings
- [ ] Ordenado CRITICAL → LOW
- [ ] ≥5 findings
- [ ] ≥1 deprecated API (quando aplicável)
- [ ] Pausa e pede confirmação

### Fase 3
- [ ] Estrutura MVC criada
- [ ] Config via .env (sem hardcoded)
- [ ] Models isolados
- [ ] Routes/Views separadas
- [ ] Controllers concentrando fluxo
- [ ] Error handling centralizado
- [ ] Entry point mínimo
- [ ] App boota sem erro
- [ ] Todos os requests do `api.http` respondem com status e payload corretos
```

---

## 8. Riscos e Mitigações

| Risco | Probabilidade | Mitigação |
|---|---|---|
| Skill com lógica stack-specific dentro do `SKILL.md` | Alta | Manter `SKILL.md` agnóstico; lógica de detecção isolada em `01-project-analysis.md` |
| Fase 3 quebrar endpoints (regressão) | Alta | Validação obrigatória após cada arquivo refatorado; manter endpoints públicos imutáveis |
| Falta de `.env` exemplo após refatoração | Média | Skill cria `.env.example` automaticamente listando todas as variáveis |
| `task-manager-api` "já organizado" recebe refatoração mínima e não cumpre critério | Média | Foco em **mover business logic de routes para services** + extrair config + criar controllers; é melhoria estrutural mesmo num projeto layered |
| `code-smells-project` tem `loja.db` que pode ser sobrescrito | Baixa | Adicionar `.db` ao `.gitignore` antes do commit; nunca commitar binário do SQLite |
| Skill encontra <5 findings em algum projeto | Baixa | Catálogo robusto (15 anti-patterns); cada projeto tem ≥6 problemas documentados |

---

## 9. Cronograma Sugerido

1. **Iteração 1:** Construir SKILL.md + 5 arquivos na raiz (`/workspace/.claude/skills/refactor-arch/`) → executar em `code-smells-project` (`cd code-smells-project && claude "/refactor-arch"` com path relativo à raiz).
2. **Iteração 2:** Ajustar skill na raiz → executar em `ecommerce-api-legacy` → corrigir pontos stack-specific que vazaram.
3. **Iteração 3:** Ajustar skill na raiz → executar em `task-manager-api` → validar comportamento em projeto parcialmente organizado.
4. **Iteração 4:** Polimento final → **copiar a pasta `refactor-arch/` para dentro dos 3 projetos** → commitar → atualizar `README.md` raiz.

Esperado: **2–4 iterações** (alinhado ao próprio challenge).

---

## 10. Próximos Passos Imediatos

1. Criar `/workspace/.claude/skills/refactor-arch/SKILL.md` (raiz do repositório) com o frontmatter e o esqueleto das 3 fases.
2. Escrever `02-antipattern-catalog.md` priorizando os 8 anti-patterns críticos da seção 3 deste documento (sinal de detecção + severidade + recomendação).
3. Rodar a Fase 1 manualmente para validar que o banner sai correto.
4. Iterar.

---

**Documento de planejamento concluído.** A partir daqui, próxima ação é escrever o `SKILL.md` e os 5 arquivos de referência seguindo este blueprint.
