# Segurança da Informação — LicitaME
## Documentação de Requisitos para Apresentação

**Disciplina:** Segurança da Informação
**Projeto:** LicitaME — Plataforma de Apoio à Concorrência Pública para MEIs
**Data de Entrega:** 10–11/06/2026
**Equipe:** Luccas Fernandes, Gabriel Nogueira, Maria Eduarda Pernambuco, Luiz Henrique Cavalcanti, Nathalia Carvalho, Carlos Cavalcante

---

## Visão Geral da Plataforma

A **LicitaME** é uma API REST construída com **FastAPI + MongoDB Atlas**, com app mobile em **Expo (React Native)**. Apoia Microempreendedores Individuais (MEIs) a descobrir e participar de licitações públicas via integração com o PNCP (Portal Nacional de Contratações Públicas).

```
Stack de Segurança
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Backend    FastAPI 0.115 + Motor 3.7 (async MongoDB)
Auth       JWT HS256 (python-jose) + bcrypt (passlib)
Rate Limit slowapi — 5–10 req/min por IP
Headers    SecurityHeadersMiddleware (7 headers)
LGPD       3 endpoints: meus-dados, consentimento, minha-conta
Mobile     expo-secure-store (Keychain/Keystore)
CI/CD      GitHub Actions — pytest + pip-audit + backup semanal
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Requisito 1 — Gestão de Autenticação de Usuários e Gestão de Senhas

### 1.1 Autenticação com JWT

| Atributo | Valor |
|---|---|
| Biblioteca | `python-jose[cryptography]` 3.3.0 |
| Algoritmo | HS256 |
| Expiração | Configurável via `JWT_EXPIRE_MINUTES` (padrão: 1440 min = 24h) |
| Transporte | `Authorization: Bearer <token>` — nunca em cookies ou query string |
| Validação | `HTTPBearer` do FastAPI em todos os endpoints protegidos |
| Falha | HTTP 401 com mensagem humanizada, sem revelar detalhes internos |

**Arquivo:** `api/auth/security.py`
```python
def criar_token(data: dict) -> str:
    payload = data.copy()
    expira = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload["exp"] = expira
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
```

### 1.2 Gerenciamento de Senhas com bcrypt

| Atributo | Valor |
|---|---|
| Biblioteca | `passlib[bcrypt]` 1.7.4 |
| Algoritmo | bcrypt com **salt aleatório por hash** |
| Validação | Mínimo de 8 caracteres — rejeitado no schema Pydantic (HTTP 422) |
| Armazenamento | `senha_hash` no MongoDB — **texto original jamais persistido** |
| Exposição | Senha e hash **nunca** retornados em nenhuma resposta da API |

**Arquivo:** `api/auth/security.py`
```python
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_senha(senha: str) -> str:
    return pwd_context.hash(senha)   # salt automático

def verificar_senha(senha: str, hash: str) -> bool:
    return pwd_context.verify(senha, hash)
```

### 1.3 Rate Limiting em Endpoints de Autenticação

| Endpoint | Limite | Resposta |
|---|---|---|
| `POST /auth/login` | 10 req/min por IP | HTTP 429 |
| `POST /auth/register` | 10 req/min por IP | HTTP 429 |
| `POST /auth/esqueci-senha` | 5 req/min por IP | HTTP 429 |
| `POST /auth/redefinir-senha` | 5 req/min por IP | HTTP 429 |

**Biblioteca:** `slowapi` 0.1.9 — wrapper do `limits` sobre Starlette

### 1.4 Reset de Senha Seguro

Fluxo implementado sem dependência de serviço de e-mail externo:

```
1. POST /auth/esqueci-senha { email }
   → Gera token com secrets.token_urlsafe(32)  [256 bits de entropia]
   → TTL: 1 hora — armazenado em collection reset_tokens
   → Tokens anteriores do mesmo usuário são removidos
   → Retorna { reset_token, expira_em }

2. POST /auth/redefinir-senha { token, nova_senha }
   → Valida existência e expiração do token
   → Atualiza senha_hash com novo bcrypt hash
   → Invalida o token após o uso (delete_one)
```

**Arquivo:** `api/auth/service.py` — funções `solicitar_reset_senha()` e `redefinir_senha()`

### 1.5 Controle de Duplicidade e Validações de Registro

- Verificação de e-mail duplicado → HTTP 409 com mensagem humanizada
- Verificação de CNPJ duplicado → HTTP 409 com mensagem humanizada
- CNPJ validado com 14 dígitos via regex no schema Pydantic
- E-mail validado via `EmailStr` do pydantic-email-validator

---

## Requisito 2 — Gerenciamento de Dados em Repouso / Anonimização

### 2.1 Criptografia em Repouso — MongoDB Atlas AES-256

Todos os dados persistidos na plataforma (senhas em hash, documentos GridFS, tokens de reset, histórico, alertas) são armazenados no **MongoDB Atlas** com **criptografia em repouso habilitada pelo provedor**:

| Camada | Mecanismo |
|---|---|
| Storage Engine | AES-256 via MongoDB Atlas Encrypted Storage Engine |
| Gestão de Chaves | Key Management Service (KMS) configurado no projeto Atlas |
| Escopo | Todo o cluster — collections, índices e arquivos GridFS |
| Referência | [MongoDB Atlas — Encrypt at Rest](https://www.mongodb.com/docs/atlas/security-encrypt-at-rest/) |

> Documentado no módulo `api/auth/security.py` (docstring de módulo).

### 2.2 Proteção de Dados Sensíveis na Aplicação

| Dado | Proteção |
|---|---|
| Senha | Hash bcrypt com salt — texto original descartado imediatamente após hashing |
| Token JWT | Mascarado em logs (`Bearer [REDACTED]`) pelo `AuthorizationMaskFilter` |
| Documentos (PDF/DOCX/JPEG) | Armazenados no GridFS com hash SHA-256 de integridade; acesso exige autenticação |
| CNPJ | Armazenado apenas como string normalizada (14 dígitos); sem dado fiscal derivado |

### 2.3 Mascaramento de Logs — AuthorizationMaskFilter

Tokens JWT são automaticamente mascarados em todos os logs da aplicação para evitar exposição em painéis de log e monitoramento.

**Arquivo:** `api/middleware.py`
```python
class AuthorizationMaskFilter(logging.Filter):
    _PATTERN = re.compile(r"(Bearer\s+)[A-Za-z0-9\-_\.]+", re.IGNORECASE)

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = self._PATTERN.sub(r"\1[REDACTED]", str(record.msg))
        ...
        return True
```

### 2.4 Integridade de Arquivos via SHA-256

Todo arquivo enviado via `POST /editais/:id/documentos` tem seu hash SHA-256 calculado e armazenado nos metadados do GridFS no momento do upload, permitindo verificação de integridade a qualquer momento.

### 2.5 Controle de Tipos de Arquivo (Whitelist MIME)

| MIME Permitido | Tipo |
|---|---|
| `application/pdf` | PDF |
| `image/jpeg` / `image/png` | Imagens |
| `application/msword` | Word (.doc) |
| `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | Word (.docx) |

Tamanho máximo: **10 MB por arquivo**. Arquivos fora da whitelist recebem HTTP 400.

---

## Requisito 3 — Atendimento a Requisitos de LGPD (Lei nº 13.709/2018)

### 3.1 Dados Coletados e Base Legal

| Dado | Finalidade | Base Legal (LGPD) |
|---|---|---|
| Nome completo | Identificação do MEI | Execução de contrato (Art. 7º, V) |
| E-mail | Autenticação e notificações | Execução de contrato (Art. 7º, V) |
| CNPJ (MEI) | Validação do enquadramento | Execução de contrato (Art. 7º, V) |
| Senha (hash bcrypt) | Autenticação segura | Execução de contrato (Art. 7º, V) |
| Plano (free/premium) | Controle de funcionalidades | Execução de contrato (Art. 7º, V) |
| Documentos enviados | Habilitação em licitações | Consentimento do titular (Art. 7º, I) |
| Histórico de participações | Dashboard pessoal | Consentimento do titular (Art. 7º, I) |
| Alertas configurados | Notificações de interesse | Consentimento do titular (Art. 7º, I) |
| **consentiu_termos** | Registro de consentimento | Obrigação legal (Art. 7º, II) |
| **data_consentimento** | Auditoria do aceite | Obrigação legal (Art. 7º, II) |

**Dados NÃO coletados:** biometria, localização em tempo real, dados de menores, dados de terceiros sem consentimento.

### 3.2 Direitos dos Titulares Implementados

| Direito LGPD | Artigo | Endpoint | Comportamento |
|---|---|---|---|
| Acesso | Art. 18, II | `GET /lgpd/meus-dados` | Retorna JSON completo: usuário, checklist, alertas, histórico, consentimento |
| Exclusão | Art. 18, VI | `DELETE /lgpd/minha-conta` | Deleção em cascata: usuário + checklist + alertas + histórico + GridFS |
| Informação sobre consentimento | Art. 18, VII | `GET /lgpd/consentimento` | Retorna `consentiu_termos` e `data_consentimento` |

### 3.3 Rastreamento de Consentimento

O consentimento é coletado e registrado no momento do cadastro:

**Schema:** `api/auth/schemas.py`
```python
class UserRegister(BaseModel):
    ...
    consentiu_termos: bool        # obrigatório — False → HTTP 422
    data_consentimento: Optional[datetime] = None

    @field_validator("consentiu_termos")
    def validar_consentimento(cls, v: bool) -> bool:
        if not v:
            raise ValueError("É necessário consentir com os termos de uso.")
        return v
```

**Persistência** (`api/auth/service.py`):
```python
usuario = {
    ...
    "consentiu_termos": dados.consentiu_termos,
    "data_consentimento": dados.data_consentimento.isoformat() or agora,
}
```

### 3.4 Exclusão em Cascata (Direito ao Esquecimento)

**Arquivo:** `api/lgpd/service.py` — `excluir_conta_usuario()`

```
DELETE /lgpd/minha-conta
  → db.usuarios.delete_one()
  → db.checklist_progresso.delete_many()
  → db.alertas.delete_many()
  → db.historico.delete_many()
  → GridFS: fs.files.find() → fs.chunks.delete_many() → fs.files.delete_one()
```

---

## Requisito 4 — Disponibilidade e Proteção contra Ataques Digitais

### 4.1 Headers HTTP de Segurança

Implementados via `SecurityHeadersMiddleware` em **todas as respostas** da API:

| Header | Valor | Proteção |
|---|---|---|
| `X-Content-Type-Options` | `nosniff` | MIME type sniffing |
| `X-Frame-Options` | `DENY` | Clickjacking |
| `X-XSS-Protection` | `1; mode=block` | XSS legado |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Força HTTPS por 1 ano |
| `Cache-Control` | `no-store` | Previne cache de dados sensíveis |
| `Referrer-Policy` | `no-referrer` | Vazamento de URL entre domínios |
| `Permissions-Policy` | `geolocation=(), camera=(), microphone=()` | Acesso a recursos do dispositivo |

**Arquivo:** `api/middleware.py` — classe `SecurityHeadersMiddleware`

**Verificação:**
```bash
curl -I https://<dominio>/health
# Resposta inclui todos os 7 headers acima
```

### 4.2 Controle de Origens (CORS)

Origins permitidas configuradas via variável de ambiente — sem wildcard em produção:

**Arquivo:** `api/main.py`
```python
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8501")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, ...)
```

| Ambiente | Configuração |
|---|---|
| Desenvolvimento | `http://localhost:3000,http://localhost:8501` (default) |
| Produção | Definir `ALLOWED_ORIGINS` com domínios reais no servidor |

### 4.3 Proteção contra Injeção

| Vetor | Proteção |
|---|---|
| MongoDB Injection | Queries estruturadas via Motor + Pydantic — nenhuma query por concatenação de strings |
| Input Validation | Todos os schemas Pydantic com tipagem estrita antes de alcançar a camada de serviço |
| E-mail | `EmailStr` do pydantic-email-validator |
| CNPJ | Regex `/\D/` para normalização + validação de 14 dígitos |

### 4.4 Segurança no App Mobile

| Controle | Implementação |
|---|---|
| Armazenamento do JWT | `expo-secure-store` — Keychain (iOS) / Keystore (Android) — **nunca** AsyncStorage |
| Expiração automática | Interceptor axios remove token ao receber HTTP 401 |
| Timeout de requisições | 10 segundos — evita conexões abertas indefinidas |
| Comunicação | HTTPS obrigatório em produção (HSTS configurado na API) |

### 4.5 Autorização por Recurso

Todos os endpoints protegidos exigem `Depends(get_usuario_atual)`. Acesso a documentos, alertas e histórico é restrito ao próprio dono via `usuario_id` na query — tentativas de acesso cruzado retornam HTTP 403 ou HTTP 404.

### 4.6 CI/CD para Disponibilidade

| Controle | Detalhe |
|---|---|
| GitHub Actions | Executa em push para `main`/`dev` e em Pull Requests |
| Testes automatizados | `pytest tests/ -v` — auth, editais, checklist, alertas, histórico |
| Auditoria de dependências | `pip-audit` em cada build — falha o CI em CVEs conhecidos |
| Deploy | Render (API) + Streamlit Cloud (dashboard) — configurados em `.render.yaml` |

---

## Requisito 5 — Backup e Continuidade de Operação

### 5.1 Objetivos de Recuperação (RTO/RPO)

| Métrica | Valor | Definição |
|---|---|---|
| **RTO** (Recovery Time Objective) | **4 horas** | Tempo máximo para restaurar o serviço após falha total |
| **RPO** (Recovery Point Objective) | **24 horas** | Janela máxima de perda de dados aceita |

### 5.2 Mecanismo de Backup Automatizado

| Atributo | Detalhe |
|---|---|
| Ferramenta | `mongodump` — MongoDB Database Tools |
| Frequência | **Semanal — toda domingo às 02:00 UTC** |
| Acionamento | GitHub Actions (`.github/workflows/backup.yml`) + `workflow_dispatch` manual |
| Compressão | `--gzip` ativo — reduz tamanho em ~70% |
| Destino | Artefato GitHub Actions com **retenção de 30 dias** |
| Escopo | Database completo `pncp_etl`: usuários, contratos, alertas, histórico, GridFS |

**Arquivo:** `scripts/backup.sh`
```bash
mongodump \
    --uri="${MONGODB_URI}" \
    --db="${MONGODB_DB}" \
    --out="backups/$(date +%Y-%m-%d_%H-%M)" \
    --gzip
```

### 5.3 Procedimento de Restauração

**Arquivo:** `scripts/restore.sh`

```bash
# 1. Baixar artefato do GitHub Actions
# 2. Definir variáveis de ambiente
export MONGODB_URI="<uri>"
export MONGODB_DB="pncp_etl"
export BACKUP_PATH="backups/2026-06-08_02-00"

# 3. Executar restauração
bash scripts/restore.sh
# → mongorestore --drop (substitui collections existentes)

# 4. Verificar integridade
curl https://<api>/health
curl https://<api>/analytics/estatisticas
```

### 5.4 Workflow de Backup (GitHub Actions)

**Arquivo:** `.github/workflows/backup.yml`

```yaml
on:
  schedule:
    - cron: "0 2 * * 0"   # toda domingo 02:00 UTC
  workflow_dispatch:        # execução manual pelo time

jobs:
  backup:
    steps:
      - Instalar MongoDB Database Tools
      - Executar scripts/backup.sh
      - Upload do artefato (retenção 30 dias)
```

### 5.5 Continuidade via CI/CD

- Cada merge para `main` dispara deploy automático no Render
- Testes automatizados impedem deploys com regressões
- Rollback via GitHub Actions: re-deploy da tag anterior em < 10 min

### 5.6 Evolução Recomendada para Produção

| Atual | Recomendação |
|---|---|
| Backup semanal (RPO 24h) | MongoDB Atlas Continuous Cloud Backup (RPO segundos) |
| Artefato GitHub (30 dias) | Bucket S3/GCS com criptografia server-side e retenção configurável |
| Sem validação de backup | Step de restore em banco temporário no próprio workflow |

---

## Requisito 6 — Gestão de Fornecedores

### 6.1 Inventário de Dependências

**Backend (Python 3.12):**

| Pacote | Versão | Função | Risco |
|---|---|---|---|
| `fastapi` | 0.115.0 | Framework web principal | Médio |
| `motor` | 3.7.1 | Driver MongoDB assíncrono | Médio |
| `python-jose[cryptography]` | 3.3.0 | Geração e validação de JWT | **Alto** |
| `passlib[bcrypt]` | 1.7.4 | Hash de senhas | **Alto** |
| `slowapi` | 0.1.9 | Rate limiting | Baixo |
| `pymongo` | 4.9.0 | Driver MongoDB síncrono (ETL) | Médio |
| `anthropic` | 0.40.0 | SDK do chatbot Léo (Claude) | Baixo |
| `mcp` | 1.3.0 | Model Context Protocol | Baixo |

**Mobile (Node.js / Expo):**

| Pacote | Versão | Função |
|---|---|---|
| `expo` | ~54.0.0 | SDK React Native |
| `expo-secure-store` | ~15.0.8 | Armazenamento seguro de JWT |
| `expo-router` | ~6.0.23 | Navegação |
| `axios` | ^1.7.0 | Cliente HTTP |

### 6.2 Varredura Automática de CVEs

| Ferramenta | Escopo | Frequência | Arquivo de Configuração |
|---|---|---|---|
| **Dependabot** | pip + npm | Semanal (segunda, 09:00 BRT) | `.github/dependabot.yml` |
| **pip-audit** | `requirements.txt` | A cada push/PR | `.github/workflows/ci.yml` |

**Dependabot:** abre PRs automáticos com atualização de versão quando CVEs são detectados.

**pip-audit no CI:**
```yaml
- name: Instalar pip-audit
  run: pip install pip-audit

- name: Auditar vulnerabilidades
  run: pip-audit --requirement requirements.txt
  # CI falha se CVE conhecido for detectado
```

### 6.3 Processo de Resposta a CVEs

| Severidade (CVSS) | SLA de Correção | Ação |
|---|---|---|
| Crítico / Alto (≥ 7.0) | **7 dias** | Atualizar versão; revisar breaking changes; testar; merge |
| Médio / Baixo (< 7.0) | **30 dias** | Avaliar vetor de ataque; atualizar no próximo sprint |
| Falso positivo | N/A | Documentar justificativa e ignorar via `pip-audit` allowlist |

**Fluxo:**
```
Detecção (Dependabot PR / pip-audit falhou no CI)
  → Triagem em 48h: CVSS score + vetor de ataque aplicável?
  → Correção dentro do SLA
  → pip-audit deve passar antes do merge para main
```

### 6.4 Política de Gerenciamento de Versões

- Versões **fixadas** (`==`) no `requirements.txt` para reprodutibilidade
- Dependabot garante atualização semanal com revisão humana via PR
- Dependências de segurança críticas (`python-jose`, `passlib`) têm prioridade máxima
- **Nunca** usar `latest` ou ranges abertos (`*`) em dependências de produção

### 6.5 Fornecedores de Infraestrutura

| Fornecedor | Serviço | Controles de Segurança |
|---|---|---|
| **MongoDB Atlas** | Banco de dados | AES-256 at rest, TLS in transit, acesso por IP whitelist, backups automáticos |
| **GitHub** | Código + CI/CD | Secrets Manager para variáveis sensíveis, CODEOWNERS, branch protection |
| **Render** | Hospedagem da API | TLS automático (Let's Encrypt), variáveis de ambiente criptografadas |
| **Anthropic** | LLM (chatbot Léo) | Dados enviados apenas na sessão de chat; sem dados pessoais no prompt |
| **PNCP** | Fonte de editais | API pública; dados não sensíveis; timeout de 30s configurado |

---

## Sumário Executivo — Maturidade de Segurança

| Requisito | Status | Evidência Principal |
|---|---|---|
| 1. Autenticação e Senhas | **Atendido** | JWT HS256 + bcrypt + rate limit + reset seguro |
| 2. Dados em Repouso | **Atendido** | Atlas AES-256 + log masking + SHA-256 em uploads |
| 3. LGPD | **Atendido** | 3 endpoints `/lgpd/` + consentimento rastreado + deleção em cascata |
| 4. Disponibilidade e Proteção | **Atendido** | 7 security headers + CORS restrito + HSTS + CI/CD |
| 5. Backup e Continuidade | **Atendido** | Script mongodump + workflow semanal GH Actions + RTO/RPO documentados |
| 6. Gestão de Fornecedores | **Atendido** | Dependabot + pip-audit no CI + inventário + SLAs de CVE |

### Arquivos-Chave para Demonstração

| Arquivo | Requisito |
|---|---|
| `api/auth/security.py` | REQ 1 — JWT e bcrypt |
| `api/auth/router.py` | REQ 1 — Endpoints de autenticação e reset |
| `api/auth/service.py` | REQ 1, 3 — Lógica de negócio auth + consentimento |
| `api/middleware.py` | REQ 2, 4 — Headers de segurança e log masking |
| `api/lgpd/router.py` | REQ 3 — Endpoints LGPD |
| `api/lgpd/service.py` | REQ 3 — Exportação e exclusão de dados |
| `scripts/backup.sh` | REQ 5 — Script de backup |
| `scripts/restore.sh` | REQ 5 — Script de restore |
| `.github/workflows/backup.yml` | REQ 5 — Automação do backup |
| `.github/workflows/ci.yml` | REQ 4, 6 — CI com testes e pip-audit |
| `.github/dependabot.yml` | REQ 6 — Varredura automática de CVEs |
| `docs/analise-seguranca.md` | Todos — Análise técnica completa |
