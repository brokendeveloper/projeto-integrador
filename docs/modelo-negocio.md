# Modelo de Negócio — LicitaME

**Disciplina:** Negócios na Internet
**Projeto:** LicitaME — Plataforma de Apoio à Concorrência Pública para MEIs
**Data:** Junho/2026
**Autores:** Luccas Fernandes, Gabriel Nogueira, Maria Eduarda Pernambuco, Luiz Henrique Cavalcanti, Nathalia Carvalho, Carlos Cavalcante

---

## 1. Problema e Oportunidade

### O Problema

O Brasil possui mais de **15 milhões de MEIs registrados** (dados SEBRAE/2024). A Lei 14.133/2021 (Nova Lei de Licitações) e a LC 123/2006 garantem tratamento diferenciado a micro e pequenas empresas em licitações públicas — incluindo preferência em contratos de até R$ 80.000 e cotas exclusivas.

**Entretanto:**
- 92% dos MEIs nunca participaram de uma licitação (SEBRAE, 2023)
- Os principais obstáculos relatados são: **burocracia documental**, **falta de informação sobre editais** e **complexidade legal**
- O PNCP (Portal Nacional de Contratações Públicas) publica mais de 500 novos contratos/dia, tornando o monitoramento manual inviável

### A Oportunidade

Cada ponto percentual de participação incremental dos MEIs nas licitações públicas representa potencialmente **R$ 1,2 bilhão em novos contratos** para esse segmento. A LicitaME democratiza o acesso a esse mercado.

---

## 2. Proposta de Valor

| Para quem | O que entregamos | Diferencial |
|---|---|---|
| MEI que nunca licitou | Guia passo a passo simplificado, linguagem acessível | Complexidade jurídica traduzida em ações práticas |
| MEI experiente | Monitoramento automatizado de editais por CNAE e região | Economiza horas de varredura manual no PNCP |
| MEI com documentação incompleta | Checklist legal com base na Lei 14.133/2021 | Reduz rejeições por irregularidade documental |

---

## 3. Modelo Freemium

### 3.1 Plano Free (gratuito)

Objetivo: aquisição de usuários e demonstração de valor.

| Funcionalidade | Limite |
|---|---|
| Busca de editais no PNCP | Ilimitada |
| Filtros (CNAE, valor, região) | Ilimitado |
| Checklist Lei 14.133/2021 | Requisitos básicos (6 itens obrigatórios) |
| Upload de documentos | Ilimitado |
| Alertas de novos editais | **Máximo 3 alertas** |
| Histórico de participações | Ilimitado |
| Chatbot Léo (IA) | Ilimitado |

### 3.2 Plano Premium (pago)

Objetivo: monetização com usuários engajados que precisam de mais recursos.

**Preço hipotético: R$ 29,90/mês** (equivale a < 1h de trabalho de um MEI prestador de serviços)

| Funcionalidade | Limite |
|---|---|
| Tudo do plano free | — |
| Checklist completo (itens premium) | Itens avançados da LC 123/2006 |
| Alertas ilimitados | Sem limite |
| Notificações push de prazos | Sim |
| Análise de editais com IA (Léo) | Análise detalhada por edital |
| Exportação de documentos | PDF consolidado |
| Suporte prioritário | Sim |

### 3.3 Justificativa do Limite de 3 Alertas

O limite de 3 alertas no plano free foi escolhido por:

1. **Suficiente para testar o valor**: um MEI típico atua em 1-2 CNAEs e uma ou duas regiões — 3 alertas cobrem esse perfil básico
2. **Conversão orgânica**: quando o MEI percebe que está perdendo editais por falta de alertas adicionais, a conversão para premium é natural (dor clara, solução óbvia)
3. **Custo operacional**: alertas geram processamento em background (varredura do PNCP) — limitar free protege a infraestrutura

---

## 4. Funil de Conversão

```
TOPO: Descoberta
  └─ Canais: Google (SEO "licitação MEI"), grupos WhatsApp/Telegram de MEIs,
             SEBRAE parceiros, redes sociais

    │
    ▼

MEIO: Ativação (onboarding)
  └─ Registro → tour guiado → primeiro alerta configurado → primeiro edital aberto

    │
    ▼

MEIO: Engajamento
  └─ MEI encontra edital favorável → usa checklist → faz upload de documentos
     → toca no 4º alerta e vê o bloqueio premium

    │
    ▼

FUNDO: Conversão
  └─ Clica em "Fazer upgrade" → tela de pagamento → plano premium ativo

    │
    ▼

RETENÇÃO
  └─ Participa de licitação → registra resultado no histórico → recebe análise
     de IA → renova assinatura
```

### 4.1 Métricas do Funil

| Etapa | Métrica | Meta MVP |
|---|---|---|
| Descoberta | Visitantes únicos/mês | — |
| Ativação | Taxa de registro após visita | > 15% |
| Engajamento | DAU/MAU (stickiness) | > 20% |
| Conversão | Taxa free → premium | > 5% |
| Retenção | Churn mensal | < 10% |

---

## 5. Indicadores de Engajamento

### 5.1 Métricas Primárias (North Star)

- **Editais acompanhados por usuário ativo por mês** — mede entrega de valor central
- **Taxa de conclusão do checklist** — indica preparação para participar de licitação

### 5.2 Métricas de Produto

| Métrica | Como medir | Frequência |
|---|---|---|
| Usuários ativos diários (DAU) | Requisições autenticadas/dia | Diária |
| Usuários ativos mensais (MAU) | Usuários únicos com login/mês | Mensal |
| Tempo médio até 1ª busca de edital | Timestamp registro → 1ª chamada `GET /editais` | Por coorte |
| Alertas criados por usuário | Contagem em `db.alertas` | Mensal |
| Taxa de upload de documentos | Usuários com ≥ 1 doc / total | Mensal |
| Participações registradas no histórico | Contagem em `db.historico` | Mensal |

### 5.3 Métricas de Negócio

| Métrica | Definição |
|---|---|
| MRR (Monthly Recurring Revenue) | Assinantes premium × R$ 29,90 |
| CAC (Custo de Aquisição de Cliente) | Gasto em marketing / novos assinantes premium |
| LTV (Lifetime Value) | MRR médio por cliente × meses de retenção médios |
| NPS (Net Promoter Score) | Pesquisa trimestral: "Você recomendaria a LicitaME?" |

---

## 6. Hipóteses de Monetização

### 6.1 Hipótese Principal — Freemium (validar primeiro)

- **Hipótese**: MEIs que encontrarem editais favoráveis pelo menos 1x por mês, e que esgotarem o limite de 3 alertas, converterão para premium
- **Experimento**: medir o momento exato em que o usuário toca no bloqueio de alerta e o tempo até a conversão (se houver)
- **Critério de validação**: taxa de conversão ≥ 5% em 90 dias

### 6.2 Hipótese Secundária — Assessoria por Demanda

- **Hipótese**: MEIs que ganharem uma licitação estarão dispostos a pagar por consultoria de formalização
- **Experimento**: após registro de status "Vencida" no histórico, exibir CTA "Precisa de ajuda com a assinatura do contrato?"
- **Parceiro hipotético**: escritórios de contabilidade especializados em MEI (modelo de referral)

### 6.3 Hipótese Terciária — B2B (SEBRAE, prefeituras)

- **Hipótese**: entidades de apoio ao empreendedorismo pagariam por acesso a dados agregados (quais CNAEs mais participam, quais regiões, ticket médio)
- **Produto**: relatório mensal de inteligência de mercado
- **Validação**: entrevistas com analistas do SEBRAE estadual

---

## 7. Análise de Concorrência

| Concorrente | Proposta | Diferencial LicitaME |
|---|---|---|
| ComprasNet / PNCP (gov) | Portal oficial, sem IA, sem mobile | UX simplificada, mobile-first, checklist automatizado |
| BLL (Bolsa de Licitações) | Focado em empresas médias/grandes, pago | Exclusivo para MEI, freemium, preço acessível |
| LicitaWeb | B2B, pacotes caros | Gratuito para começar, chatbot com IA |
| Planilhas e controle manual | Sem custo, alto esforço | Automatiza monitoramento e checklist |

---

## 8. Projeção Financeira (Cenário Conservador — 12 meses)

| Mês | Usuários free | Conv. Premium | MRR |
|---|---|---|---|
| 1-3 | 200 | 5 | R$ 150 |
| 4-6 | 800 | 30 | R$ 897 |
| 7-9 | 2.000 | 80 | R$ 2.392 |
| 10-12 | 5.000 | 200 | R$ 5.980 |

*Taxa de conversão assumida: 4%. Custos de infraestrutura no período: ~R$ 200/mês (MongoDB Atlas M10 + servidor VPS).*

---

## 9. Telas de Conversão Implementadas no MVP

### 9.1 Bloqueio de Alerta (RF04)
```
┌─────────────────────────────────────────┐
│  3/3 alertas (plano gratuito)           │
│                                         │
│  🔒 Limite atingido. Faça upgrade para  │
│     o plano Premium e crie alertas      │
│     ilimitados.                         │
│                                         │
│  [Fazer upgrade →]                      │
└─────────────────────────────────────────┘
```

### 9.2 Itens Premium no Checklist (RF02)
```
┌─────────────────────────────────────────┐
│  🔒  Declaração avançada LC 123/2006   │
│      [PREMIUM]                          │
│      (item desabilitado, opaco)         │
└─────────────────────────────────────────┘
```

Ambas as telas são pontos de conversão naturais — o usuário só as vê quando já está engajado com a plataforma e sente a limitação do plano gratuito.
