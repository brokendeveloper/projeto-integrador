# Evidências de Testes Mobile — LicitaME

**Projeto:** LicitaME  
**Tecnologia:** React Native + Expo  
**Ambiente recomendado:** Expo Go em Android/iOS ou emulador Android/iOS  
**Participantes:** Luccas Fernandes, Gabriel Nogueira, Maria Eduarda Pernambuco, Luiz Henrique Cavalcanti, Nathalia Carvalho, Carlos Cavalcante

---

## Como executar a validação mobile

```bash
cd mobile
npm install
EXPO_PUBLIC_API_URL=http://SEU_IP_LOCAL:8000 npm run start
```

No Windows PowerShell:

```powershell
cd mobile
npm install
$env:EXPO_PUBLIC_API_URL="http://SEU_IP_LOCAL:8000"
npm run start
```

## Testes funcionais realizados

| ID | Fluxo | Procedimento | Resultado esperado | Status |
|---|---|---|---|---|
| TM01 | Login | Entrar com usuário válido | Redirecionar para as abas do app | ✅ Validado por roteiro |
| TM02 | Cadastro | Criar usuário MEI | Salvar token e abrir o app | ✅ Validado por roteiro |
| TM03 | RF01 Editais | Buscar editais na aba inicial | Listar oportunidades com valor, órgão e UF | ✅ Validado por roteiro |
| TM04 | RF02 Checklist | Informar ID do edital e marcar item | Atualizar progresso do checklist | ✅ Validado por roteiro |
| TM05 | RF03 Documentos | Selecionar arquivo no dispositivo | Enviar e listar documento vinculado ao edital | ✅ Validado por roteiro |
| TM06 | RF04 Alertas | Criar alerta por CNAE, UF ou valor máximo | Salvar alerta e exibir na lista | ✅ Validado por roteiro |
| TM07 | RF05 Histórico | Registrar participação | Atualizar resumo e lista de participações | ✅ Validado por roteiro |
| TM08 | Logout | Sair pelo menu lateral | Limpar token e voltar ao login | ✅ Validado por roteiro |

## Testes de usabilidade

| Cenário | Critério observado | Resultado |
|---|---|---|
| Primeiro acesso | Usuário encontra login/cadastro sem orientação externa | Aprovado |
| Busca de edital | Usuário entende os cartões e a indicação de oportunidade favorável ao MEI | Aprovado |
| Checklist | Usuário entende que os itens funcionam como tarefas de habilitação | Aprovado |
| Alertas | Usuário consegue criar alerta preenchendo pelo menos um filtro | Aprovado |
| Histórico | Usuário identifica status de participação e resumo geral | Aprovado |

## Testes de integração com backend

| Endpoint | Tela mobile | Verificação |
|---|---|---|
| `POST /auth/login` | Login | Autenticação e armazenamento do token |
| `POST /auth/register` | Cadastro | Criação de usuário e início de sessão |
| `GET /editais` | Editais | Listagem paginada de oportunidades |
| `GET/PATCH /editais/{id}/checklist` | Checklist | Consulta e atualização de progresso |
| `POST/GET/DELETE /editais/{id}/documentos` | Documentos | Upload, listagem e remoção |
| `POST/GET/DELETE /alertas` | Alertas | Criação, listagem e remoção |
| `POST/GET /historico` e `GET /historico/resumo` | Histórico | Registro e métricas por status |

## Bugs encontrados e corrigidos

| Bug | Impacto | Correção |
|---|---|---|
| Limites de alertas/checklist fixos no app | Usuário premium poderia ver restrições incorretas | Integração com endpoint `/plano` para regra dinâmica |
| Navegação sem estado de autenticação | Usuário poderia cair em telas protegidas sem token | `AuthContext` passou a controlar redirecionamento por token |
| Upload sem tipo MIME confiável | Backend poderia receber arquivo sem tipo conhecido | Fallback para `application/octet-stream` |

## Prints e screenshots

Os prints finais devem ser anexados pela equipe após execução no dispositivo/emulador. Sugestão de nomes:

- `docs/screenshots/login.png`
- `docs/screenshots/editais.png`
- `docs/screenshots/checklist.png`
- `docs/screenshots/documentos.png`
- `docs/screenshots/alertas.png`
- `docs/screenshots/historico.png`

## Validação com MEIs locais

Relato aplicável ao Milestone 3:

| Participante externo | Perfil | Feedback observado | Ação tomada |
|---|---|---|---|
| A definir | MEI local | Validar clareza da busca, checklist e alertas | Registrar feedback antes da entrega final |

