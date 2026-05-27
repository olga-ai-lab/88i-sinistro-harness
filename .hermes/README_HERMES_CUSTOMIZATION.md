# 🎯 Customizações do Hermes para Olga — 88i Sinistros

Este diretório `.hermes/` contém as customizações específicas do **Hermes Agent** para o agente **Octa** de sinistros da **88i Seguradora Digital**.

## 📂 Estrutura

```
.hermes/
├── skills/olga/88i-sinistro-agent/
│   └── SKILL.md                    ← Definição da skill Hermes
│
├── config/
│   └── olga.yaml                   ← Profile customizado para Olga
│
└── plugins/olga/
    ├── inngest-event-handler/      ← (a implementar)
    ├── langfuse-tracer/            ← (a implementar)
    └── prometheus-metrics/         ← (a implementar)
```

## 🚀 Como Usar

### 1. Carregar a Skill Olga

```bash
cd ~/Projects/88i-sinistro-harness

# Se estiver usando Hermes localmente
hermes skills load olga-88i-sinistro-agent
```

### 2. Usar o Profile Olga

```bash
# Via linha de comando
hermes --profile olga run "Analisar sinistro #12345"

# Ou via variável de ambiente
export HERMES_PROFILE=olga
hermes run "Analisar sinistro #12345"
```

### 3. Configurar Variáveis de Ambiente

```bash
# Adicione ao seu .env (local ou Railway Variables)
ANTHROPIC_API_KEY=sk-ant-xxx
INNGEST_API_KEY=evt-xxx
LANGFUSE_PUBLIC_KEY=pk-xxx
LANGFUSE_SECRET_KEY=sk-xxx
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJxxx
```

## 🔧 Customizações Disponíveis

### SKILL: olga-88i-sinistro-agent

Define o agente de sinistros com:
- Extração automática (BAML)
- Detecção de fraude (150ms SLA)
- Injeção de contexto (50ms SLA)
- Roteamento inteligente (AP/DITA/Impedimento)

**Arquivo:** `.hermes/skills/olga/88i-sinistro-agent/SKILL.md`

### PROFILE: olga

Define a configuração específica para Olga:
- Serviços: Anthropic, Inngest, Langfuse, Supabase, Prometheus
- SLAs: extract 100ms, fraud 150ms, context 50ms
- Segurança: AES-256, rate limiting 1000 req/min
- Routing rules: AP, DITA, Impedimento ao Trabalho

**Arquivo:** `.hermes/config/olga.yaml`

## 🔄 Integração com o Projeto

Este projeto **88i-sinistro-harness** é o harness principal que contém:
- Fases 1-7 completas (27k+ LOC, 200+ arquivos)
- Testes, documentação, scripts de deployment
- Configuração de Inngest, Supabase, Langfuse

As customizações do Hermes em `.hermes/` complementam este harness, permitindo que você:
1. Use Hermes CLI para rodar o agente localmente
2. Carregue a skill olga-88i-sinistro-agent em Hermes
3. Processe sinistros via Hermes (CLI, gateway, subagent)

## 📚 Próximos Passos

1. **Implementar plugins** em `.hermes/plugins/olga/`
   - inngest-event-handler
   - langfuse-tracer
   - prometheus-metrics

2. **Criar scripts** para integração
   - extract_claim_data.py
   - fraud_detection.py
   - context_injection.py
   - inngest_handler.py

3. **Adicionar testes** para a skill
   - test_extract.py
   - test_fraud.py
   - test_routing.py

4. **Deploy** com as customizações Hermes
   - Render.com com .hermes/config/olga.yaml
   - GitHub Actions para CI/CD

## 🆘 Referências

- **SKILL.md:** Definição completa da skill (.hermes/skills/olga/88i-sinistro-agent/SKILL.md)
- **olga.yaml:** Configuração do profile (.hermes/config/olga.yaml)
- **Documentação do Harness:** docs/ (no raiz do projeto)
- **Hermes Docs:** https://hermes-agent.nousresearch.com/docs

---

**Versão:** 1.0.0
**Last Updated:** 27 mai 2026
**Status:** 🟢 Production-Ready (skilldef + profile + base config)
