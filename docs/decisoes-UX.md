# Decisões de UX Mobile — LicitaME

**Projeto:** LicitaME  
**Público-alvo:** Microempreendedores Individuais interessados em licitações públicas  
**Participantes:** Luccas Fernandes, Gabriel Nogueira, Maria Eduarda Pernambuco, Luiz Henrique Cavalcanti, Nathalia Carvalho, Carlos Cavalcante

---

## Princípios de experiência

- **Clareza antes de completude:** o app apresenta o essencial para o MEI agir sem precisar conhecer todos os detalhes jurídicos.
- **Fluxo guiado:** cada RF leva a uma ação concreta: buscar edital, completar checklist, enviar documento, criar alerta ou registrar participação.
- **Linguagem simples:** termos técnicos são traduzidos para ações práticas.
- **Uso com uma mão:** abas principais ficam acessíveis no rodapé, seguindo padrão mobile conhecido.
- **Baixa carga cognitiva:** dados extensos de editais são resumidos em cartões com valor, órgão, UF, prazo e indicação de oportunidade favorável.

## Decisões por área

| Área | Decisão | Motivo |
|---|---|---|
| Navegação | Tabs para RF01-RF05 | As funcionalidades principais precisam estar sempre visíveis no MVP. |
| Autenticação | Redirecionamento automático por token | Evita telas indevidas e reduz fricção no retorno ao app. |
| Editais | Cartões escaneáveis | O MEI precisa comparar oportunidades rapidamente. |
| Checklist | Barra/progresso e itens marcáveis | Transforma requisito legal em tarefa acompanhável. |
| Documentos | Upload por seletor nativo | Usa comportamento familiar do celular e reduz erro de arquivo. |
| Alertas | Formulário curto por CNAE, UF e valor | Evita configuração longa demais para o primeiro uso. |
| Histórico | Resumo por status | Ajuda o usuário a entender resultados sem abrir cada participação. |
| Plano premium | Paywall contextual | Limites aparecem no momento em que afetam a ação do usuário. |

## Acessibilidade e legibilidade

- Contraste alto entre texto e fundo.
- Ícones nas abas para reforçar reconhecimento visual.
- Textos curtos em botões e estados de erro.
- Alertas nativos para feedback imediato.
- Layout vertical compatível com telas pequenas.

## Validação qualitativa

O roteiro de validação com usuários deve observar:

- Se o MEI entende qual edital é favorável.
- Se consegue abrir e concluir itens do checklist.
- Se entende a diferença entre documento enviado e pendente.
- Se consegue criar um alerta sem explicação externa.
- Se o histórico ajuda a lembrar participações anteriores.

