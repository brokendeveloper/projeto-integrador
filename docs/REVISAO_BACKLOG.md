# Revisão Final do Backlog — Milestone 3 Mobile

**Projeto:** LicitaME  
**Disciplina:** Desenvolvimento Mobile - Projeto Integrador (2026.1)  
**Participantes:** Luccas Fernandes, Gabriel Nogueira, Maria Eduarda Pernambuco, Luiz Henrique Cavalcanti, Nathalia Carvalho, Carlos Cavalcante

---

## Backlog priorizado

| Prioridade | Requisito | História de usuário | Critérios de aceite | Planejado | Entregue | Status | Responsáveis |
|---|---|---|---|---|---|---|---|
| P0 | RF01 - Busca de editais | Como MEI, quero buscar editais por critérios relevantes para encontrar oportunidades viáveis. | Listar editais, exibir valor/órgão/UF, indicar oportunidades favoráveis ao MEI e permitir busca. | Busca por região, valor e CNAE | Tela de editais com busca, paginação e integração à API | ✅ Implementada | Luccas Fernandes, Maria Eduarda Pernambuco |
| P0 | RF02 - Checklist Lei 14.133/2021 | Como MEI, quero saber quais requisitos preciso cumprir para participar de um edital. | Exibir itens, progresso e permitir marcar conclusão. | Checklist automático por edital | Tela de checklist com progresso e atualização por item | ✅ Implementada | Gabriel Nogueira, Luiz Henrique Cavalcanti |
| P0 | RF03 - Documentos | Como MEI, quero organizar documentos de habilitação por edital. | Selecionar arquivo, enviar, listar e remover documentos. | Upload e templates | Upload nativo e listagem por edital; templates ficam como próximo incremento | 🚧 Parcial | Nathalia Carvalho, Carlos Cavalcante |
| P0 | RF04 - Alertas | Como MEI, quero receber alertas de oportunidades compatíveis com meu perfil. | Criar filtros por CNAE/valor/UF, listar e remover alertas. | Alertas e notificações | Criação/listagem/remoção de alertas; push notification fica preparado para evolução | 🚧 Parcial | Maria Eduarda Pernambuco, Gabriel Nogueira |
| P0 | RF05 - Histórico | Como MEI, quero acompanhar minhas participações e resultados. | Registrar participação, listar histórico e ver resumo por status. | Dashboard de histórico | Tela de histórico com resumo e registros | ✅ Implementada | Luiz Henrique Cavalcanti, Luccas Fernandes |
| P1 | Autenticação | Como usuário, quero entrar com segurança no app. | Login, cadastro, token salvo e logout. | Login/cadastro | Fluxo com Expo Secure Store e proteção de rotas | ✅ Implementada | Nathalia Carvalho |
| P1 | Assistente Léo | Como MEI, quero tirar dúvidas sobre oportunidades e requisitos. | Chat integrado ao backend, com regra de plano. | Diferencial opcional | Tela do assistente adicionada às tabs | ✅ Implementada | Carlos Cavalcante |

## Próximos passos pós-Milestone 3

1. Publicar protótipo visual final em Figma e anexar link definitivo.
2. Capturar prints em dispositivo real para cada RF.
3. Finalizar templates de documentos de habilitação por tipo de edital.
4. Ativar push notifications reais com permissões e token do dispositivo.
5. Criar testes automatizados mobile com Jest/React Native Testing Library.
6. Gerar build APK ou EAS Build para distribuição fora do Expo Go.

