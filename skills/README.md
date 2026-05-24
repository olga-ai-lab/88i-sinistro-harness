# Guia de Skills — 88i Sinistro Harness

As 4 skills desta pasta são usadas pelo Hermes Agent no pipeline documental.
Copie para o diretório de skills do Hermes para ativar.

## Instalação

```bash
mkdir -p ~/.hermes/skills/insurance

cp -r olga-analista-seguros-88i   ~/.hermes/skills/insurance/
cp -r sinistro-doc-classifier     ~/.hermes/skills/insurance/
cp -r sinistro-doc-forensics      ~/.hermes/skills/insurance/
cp -r sinistro-claim-adjudicator  ~/.hermes/skills/insurance/
```

## Pipeline de 3 Etapas

```
documento recebido (imagem / PDF / texto)
    │
    ▼ Etapa 1
sinistro-doc-classifier
  → classifica tipo: police_report | medical_certificate | invoice_receipt | ...
  → define campos-alvo para extração
    │
    ▼ Etapa 2
sinistro-doc-forensics
  → extrai campos obrigatórios por tipo
  → analisa autenticidade (plausible | suspicious | indeterminate)
  → detecta sinais de adulteração (font inconsistency, datas impossíveis, CRM ausente)
  → cross-validation entre documentos (data BO vs data atestado, etc.)
    │
    ▼ Etapa 3
sinistro-claim-adjudicator
  → 7 fases: enquadramento → checklist D1-D10 → suficiência documental
             → coerência temporal → cross-doc → fraud scoring → decisão
  → fraud scoring: 5 categorias (documental, temporal, narrativo, comportamental, cross-doc)
  → decision_status: approved_for_next_step | pending_documents |
                     pending_manual_review | fraud_escalation | rejected_documentally
```

## Conhecimento de Produto

`olga-analista-seguros-88i` contém:
- 3 produtos: A (Impedimento), B (AP Individual), C (Bagagens)
- Condições Particulares Uber: restrições D6/D7
- 15 regras determinísticas D1-D15
- Documentos obrigatórios por cobertura
- 9 sinais de fraude delivery/Uber
- Prazos operacionais
