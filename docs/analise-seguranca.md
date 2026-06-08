# Análise de Segurança — LicitaME

**Disciplina:** Segurança da Informação
**Projeto:** LicitaME — Plataforma de Apoio à Concorrência Pública para MEIs
**Data:** Junho/2026
**Autores:** Luccas Fernandes, Gabriel Nogueira, Maria Eduarda Pernambuco, Luiz Henrique Cavalcanti, Nathalia Carvalho, Carlos Cavalcante

---

## 1. Superfícies de Ataque Identificadas

### 1.1 API REST (FastAPI)

| Superfície | Vetor de Ataque | Criticidade |
|---|---|---|
| `POST /auth/register` | Criação de contas em massa (abuso de bots) | Alta |
| `POST /auth/login` | Força bruta de senhas (credential stuffing) | Alta |
| `POST /editais/:id/documentos` | Upload de arquivos maliciosos | Alta |
| `GET /editais` | Injeção de queries no MongoDB via parâmetros de busca | Média |
| Todos os endpoints autenticados | Uso de tokens JWT roubados ou expirados | Média |
| Headers HTTP | Clickjacking, XSS via resposta, MIME sniffing | Média |
| `DELETE /lgpd/minha-conta` | Exclusão não autorizada de conta | Alta |

### 1.2 App Mobile (Expo / React Native)

| Superfície | Vetor de Ataque | Criticidade |
|---|---|---|
| Armazenamento do JWT | Extração do token em dispositivos com root/jailbreak | Alta |
| Comunicação com a API | Interceptação via MITM se SSL não for validado | Alta |
| Campos de formulário | Entrada de dados não sanitizados enviados ao backend | Baixa |

### 1.3 Pipeline ETL

| Superfície | Vetor de Ataque | Criticidade |
|---|---|---|
| Credenciais no ambiente | Vazamento de `MONGODB_URI` ou `JWT_SECRET_KEY` | Alta |
| Dados de terceiros (PNCP) | Envenenamento de dados na fonte externa | Baixa |

---

## 2. Controles de Segurança Implementados

### 2.1 Autenticação e Autorização

**JWT (JSON Web Token)**
- Biblioteca: `python-jose[cryptography]`
- Algoritmo: HS256
- Expiração configurável via `JWT_EXPIRE_MINUTES` (padrão: 1440 min = 24h)
- Token transportado via `Authorization: Bearer <token>` — nunca em cookies ou query string
- Validação via `HTTPBearer` no FastAPI em todos os endpoints protegidos
- Em caso de token inválido ou expirado: HTTP 401 com mensagem humanizada

**Gerenciamento de Senhas (bcrypt)**
- Biblioteca: `passlib[bcrypt]`
- Algoritmo: bcrypt com salt aleatório por hash
- Senhas **nunca** retornadas em nenhum response da API
- Validação mínima de 8 caracteres no schema de registro

**Autorização por Recurso**
- Todos os endpoints de editais, checklist, documentos, alertas e histórico exigem `Depends(get_usuario_atual)`
- Documentos e alertas só podem ser acessados/excluídos pelo próprio dono (verificação via `usuario_id` na query)

### 2.2 Rate Limiting

- Biblioteca: `slowapi` (wrapper do Limits sobre Starlette)
- Limites aplicados:
  - `POST /auth/login`: **10 requisições/minuto por IP**
  - `POST /auth/register`: **10 requisições/minuto por IP**
- Resposta ao exceder o limite: HTTP 429 Too Many Requests
- Objetivo: mitigar força bruta e abuso de criação de contas

### 2.3 Headers HTTP de Segurança

Implementados via `SecurityHeadersMiddleware` em `api/middleware.py`:

| Header | Valor | Proteção |
|---|---|---|
| `X-Content-Type-Options` | `nosniff` | MIME type sniffing |
| `X-Frame-Options` | `DENY` | Clickjacking |
| `X-XSS-Protection` | `1; mode=block` | XSS legado |
| `Strict-Transport-Security` | `max-age=63072000` | Força HTTPS |
| `Referrer-Policy` | `no-referrer` | Vazamento de URL |
| `Permissions-Policy` | `geolocation=(), camera=()` | Acesso a recursos do dispositivo |

### 2.4 Upload de Arquivos

- Tipos MIME permitidos (whitelist): `application/pdf`, `image/jpeg`, `image/png`, `application/msword`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- Tamanho máximo: **10 MB por arquivo**
- Hash SHA-256 calculado e armazenado nos metadados do GridFS para verificação de integridade
- Armazenamento no GridFS (MongoDB): arquivos separados dos dados, nunca servidos diretamente sem autenticação
- Arquivos não executáveis são rejeitados antes do armazenamento

### 2.5 Proteção contra Injeção

- **MongoDB Injection**: uso exclusivo de queries estruturadas via Motor (driver assíncrono) com parâmetros tipados pelo Pydantic — nenhuma query construída por concatenação de strings
- **Busca por regex**: flags `$options: "i"` sem âncoras — o risco de ReDoS foi avaliado e considerado baixo dado o volume de dados
- **Validação de entrada**: todos os dados de entrada passam por schemas Pydantic com tipagem estrita antes de alcançar a camada de serviço

### 2.6 Segurança no Mobile

- JWT armazenado exclusivamente no `expo-secure-store` (Keychain no iOS, Keystore no Android) — **nunca** em `AsyncStorage` ou `localStorage`
- Interceptor axios remove o token automaticamente ao receber HTTP 401
- Timeout de 10 segundos nas requisições HTTP para evitar conexões abertas

---

## 3. Conformidade LGPD (Lei nº 13.709/2018)

### 3.1 Dados Coletados

| Dado | Finalidade | Base Legal (LGPD) |
|---|---|---|
| Nome completo | Identificação do MEI na plataforma | Execução de contrato (Art. 7º, V) |
| E-mail | Autenticação e notificações | Execução de contrato (Art. 7º, V) |
| CNPJ (MEI) | Validação do enquadramento como MEI | Execução de contrato (Art. 7º, V) |
| Senha (hash bcrypt) | Autenticação segura | Execução de contrato (Art. 7º, V) |
| Plano (free/premium) | Controle de funcionalidades | Execução de contrato (Art. 7º, V) |
| Documentos enviados | Habilitação em licitações | Consentimento do titular (Art. 7º, I) |
| Histórico de participações | Dashboard pessoal do MEI | Consentimento do titular (Art. 7º, I) |
| Alertas configurados | Notificações de interesse | Consentimento do titular (Art. 7º, I) |

### 3.2 Dados **NÃO** Coletados

- Dados biométricos
- Localização em tempo real
- Dados de terceiros sem consentimento
- Dados de menores de idade

### 3.3 Direitos dos Titulares Implementados

Endpoints disponíveis em `/lgpd/`:

| Direito (LGPD) | Endpoint | Descrição |
|---|---|---|
| Acesso (Art. 18, II) | `GET /lgpd/meus-dados` | Exporta todos os dados do usuário em JSON |
| Exclusão (Art. 18, VI) | `DELETE /lgpd/minha-conta` | Remove permanentemente conta, documentos, alertas e histórico |

### 3.4 Retenção e Segurança dos Dados

- Senhas armazenadas **exclusivamente** como hash bcrypt — dados originais nunca persistidos
- Documentos armazenados no GridFS com metadados de rastreabilidade (usuário, edital, data)
- Dados no MongoDB Atlas com criptografia em repouso habilitada pelo provedor
- Sem transferência de dados para terceiros

---

## 4. Riscos Remanescentes e Recomendações Futuras

### 4.1 Riscos Identificados (não mitigados nesta versão)

| Risco | Probabilidade | Impacto | Recomendação |
|---|---|---|---|
| Token JWT sem revogação | Média | Alto | Implementar blacklist de tokens (Redis) ou usar refresh tokens com curta expiração |
| CORS aberto (`allow_origins=["*"]`) | Baixa | Médio | Restringir para domínios específicos em produção |
| Rate limiting apenas em `/auth` | Média | Médio | Estender rate limiting para todos os endpoints (ex: 100 req/min por usuário) |
| Ausência de 2FA | Baixa | Alto | Implementar autenticação de dois fatores via e-mail ou TOTP |
| Logs sem auditoria formal | Baixa | Médio | Implementar audit log de ações sensíveis (login, exclusão de conta, upload) |
| Sem validação de CNPJ real | Média | Médio | Integrar com API da Receita Federal para validar CNPJ ativo e MEI |
| Upload sem antivírus | Baixa | Alto | Integrar scanner de malware (ex: ClamAV) no pipeline de upload |
| Secrets em variáveis de ambiente simples | Baixa | Alto | Migrar para secrets manager (AWS Secrets Manager, HashiCorp Vault) em produção |

### 4.2 Recomendações de Infraestrutura para Produção

1. **TLS obrigatório**: configurar HTTPS com certificado válido (Let's Encrypt) no servidor de produção
2. **WAF (Web Application Firewall)**: adicionar camada de proteção antes da API
3. **Monitoramento**: integrar APM (Application Performance Monitoring) com alertas de anomalias
4. **Backup criptografado**: configurar backups automáticos do MongoDB Atlas com criptografia
5. **Dependências**: atualizar dependências regularmente e configurar alertas de CVE (ex: Dependabot)

---

## 5. Testes de Segurança Realizados

| Teste | Resultado |
|---|---|
| Tentativa de acesso sem token JWT | HTTP 401 — OK |
| Registro com CNPJ duplicado | HTTP 409 — OK |
| Login com senha incorreta | HTTP 401 sem revelação de detalhes — OK |
| Upload de arquivo EXE | HTTP 400 (tipo não permitido) — OK |
| Upload de arquivo > 10 MB | HTTP 413 — OK |
| Exceder rate limit em `/auth/login` | HTTP 429 — OK |
| Exclusão de documento de outro usuário | HTTP 403 — OK |
| Exclusão de alerta de outro usuário | HTTP 404 (não encontrado para o usuário) — OK |
| Headers de segurança presentes | Verificados via `curl -I` — OK |
