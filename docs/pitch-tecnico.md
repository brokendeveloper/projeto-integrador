# Pitch Técnico Mobile — LicitaME

**Disciplina:** Desenvolvimento Mobile - Projeto Integrador (2026.1)  
**Stack:** React Native, Expo, Expo Router, Axios, Expo Secure Store, Expo Document Picker, Expo Notifications  
**Participantes:** Luccas Fernandes, Gabriel Nogueira, Maria Eduarda Pernambuco, Luiz Henrique Cavalcanti, Nathalia Carvalho, Carlos Cavalcante

---

## Problema

Microempreendedores Individuais têm direito a tratamento favorecido em licitações públicas, especialmente em oportunidades de menor valor, mas enfrentam barreiras práticas: dificuldade para encontrar editais, linguagem jurídica complexa, insegurança sobre documentos exigidos e falta de controle de prazos. A Lei nº 14.133/2021 moderniza o processo licitatório, mas o acesso continua pouco amigável para pequenos empreendedores.

## Solução

O **LicitaME** é um app mobile em React Native/Expo que centraliza busca de editais, checklist de habilitação, organização de documentos, alertas e histórico de participações. A proposta é transformar o processo de participação em licitações em uma jornada guiada, acessível e pensada para o uso diário no celular.

## Arquitetura do app

- **Expo Router:** navegação baseada em arquivos, com Stack para autenticação e telas auxiliares.
- **Tabs:** acesso rápido às cinco funcionalidades do MVP.
- **AuthContext:** estado global de autenticação e redirecionamento conforme token salvo.
- **Expo Secure Store:** persistência segura do token JWT.
- **Axios:** camada de integração com a API, usando `EXPO_PUBLIC_API_URL`.
- **Expo Document Picker:** seleção de documentos para upload de habilitação.
- **Expo Notifications:** base técnica para alertas e notificações mobile.

## Demonstração das funcionalidades RF01-RF05

| RF | Funcionalidade | Como aparece no app | Status |
|---|---|---|---|
| RF01 | Busca e filtro de editais abertos por região, valor e CNAE | Aba `Editais`, listagem paginada e busca textual integrada à API | ✅ Implementada |
| RF02 | Análise automática de requisitos | Aba `Checklist`, progresso por edital e marcação de itens | ✅ Implementada |
| RF03 | Organização de documentos | Aba `Documentos`, upload via seletor nativo e listagem por edital | ✅ Implementada |
| RF04 | Alertas e notificações de prazos/preferências | Aba `Alertas`, criação por CNAE, UF e valor máximo | ✅ Implementada |
| RF05 | Dashboard de histórico de participações | Aba `Histórico`, resumo por status e registro de participação | ✅ Implementada |

## Diferenciais técnicos

- Integração mobile-first com backend por API REST.
- Persistência segura de sessão com token JWT.
- Navegação protegida para impedir acesso não autenticado às abas.
- Upload de documentos usando componente nativo compatível com Expo.
- Estrutura preparada para notificações push e regras de plano gratuito/premium.
- Assistente Léo como extensão inteligente para apoio ao MEI.

## Métricas de sucesso

| Métrica | Meta para o MVP |
|---|---|
| Tempo para encontrar um edital favorável | Menos de 2 minutos |
| Conclusão do checklist | Pelo menos 80% dos itens compreendidos pelo usuário |
| Registro de participação | Menos de 1 minuto após escolha do edital |
| Criação de alerta | Até 3 campos e confirmação imediata |
| Retenção em teste piloto | Usuário consegue retornar ao histórico sem suporte da equipe |

## Desafios superados

- Traduzir requisitos legais em uma experiência simples de checklist.
- Manter o app útil mesmo com grande volume de editais.
- Integrar autenticação, upload e chamadas assíncronas sem quebrar a experiência mobile.
- Organizar a navegação para que as cinco RFs fiquem acessíveis sem excesso de telas.

## Fechamento

O LicitaME entrega um MVP mobile funcional para reduzir a distância entre MEIs e compras públicas, com foco em clareza, autonomia e acompanhamento contínuo da jornada de licitação.

