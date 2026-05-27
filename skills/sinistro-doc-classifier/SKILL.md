---
name: sinistro-doc-classifier
description: "Classifica documentos de sinistro da 88i Seguradora Digital em categorias fechadas, define relevância, qualidade de imagem e campos-alvo mínimos para extração. Use SEMPRE que receber imagem, PDF ou foto de um documento de sinistro e for preciso decidir o tipo documental ANTES de extrair conteúdo. Trigger em: 'classificar documento', 'que tipo de documento é esse', 'é BO ou aviso', 'documento de sinistro', 'recebemos esse doc', 'o segurado mandou isso', upload de imagem/PDF no contexto de sinistro, triagem documental, pipeline de análise documental. NÃO use para extração de campos (use sinistro-doc-forensics) nem para decisão de cobertura (use sinistro-claim-adjudicator)."
---

# Triador Documental Sênior — Sinistros 88i Seguradora Digital

Skill de classificação documental de primeira camada. Sua função é identificar o tipo documental com precisão máxima, evitar leitura desnecessária de conteúdo irrelevante, e encaminhar a próxima etapa com o menor custo possível.

> **Pipeline:** Esta skill é a ETAPA 1 de 3 → `classifier` → `forensics` → `adjudicator`
> **Complementar a:** `sinistro-doc-forensics` (extração), `sinistro-claim-adjudicator` (decisão)
> **Conhecimento de produto:** `olga-analista-seguros-88i` (regras de cobertura, docs obrigatórios)

---

## NUNCA FAÇA

- Não extraia todos os campos do documento — isso é trabalho da skill `forensics`.
- Não decida cobertura, fraude ou elegibilidade.
- Não invente valores ausentes.
- Não classifique como `police_report` se os elementos mínimos não estiverem presentes.
- Não classifique fotos de dano veicular/celular como `irrelevant_document` — são evidências válidas.

---

## TAXONOMIA FECHADA (v2)

Escolha exatamente UM `document_type` principal:

### Documentos oficiais
| Tipo | Descrição | Elementos mínimos |
|------|-----------|-------------------|
| `police_report` | BO emitido por autoridade competente | nº registro + órgão + data fato + narrativa formal |
| `traffic_accident_report` | BRAT — Boletim de Registro de Acidente de Trânsito | nº registro + órgão trânsito + veículos + croqui/narrativa |
| `non_location_certificate` | Certidão de não localização de veículo | delegacia + nº BO ref + declaração de não localização |

### Documentos médicos
| Tipo | Descrição | Elementos mínimos |
|------|-----------|-------------------|
| `medical_report` | Laudo/relatório médico com descrição clínica | paciente + profissional + CRM/UF + descrição clínica |
| `medical_certificate` | Atestado médico (afastamento/aptidão) | paciente + CRM/UF + período + CID opcional |

### Documentos de identificação e comprovação
| Tipo | Descrição | Elementos mínimos |
|------|-----------|-------------------|
| `identity_document` | RG, CNH, CPF, passaporte | nome + número + foto (quando aplicável) |
| `proof_of_address` | Comprovante de residência (≤90 dias) | nome/endereço + data emissão |
| `vehicle_document` | CRLV, CRV ou documento do veículo | proprietário + placa + RENAVAM |
| `invoice_receipt` | Nota fiscal (NF-e c/ chave SEFAZ) ou cupom fiscal | itens + valores + chave de acesso/CNPJ emissor |

### Documentos do sinistro
| Tipo | Descrição | Elementos mínimos |
|------|-----------|-------------------|
| `claim_form` | Aviso/formulário de sinistro preenchido | segurado + data evento + descrição |
| `incident_notice` | Comunicação do evento (sem elementos de BO) | segurado + data + narrativa informal |
| `authorization_form` | Procuração, termo de autorização, cessão | partes + objeto + assinatura |
| `work_period_proof` | Comprovante de período de trabalho (screenshot app, log) | motorista + data/hora + plataforma |
| `repair_estimate` | Orçamento ou laudo de oficina | veículo + defeitos + prazo + valor |
| `damage_photo` | Foto dos danos ao veículo, celular ou bagagem | evidência visual do dano |
| `imei_block_proof` | Comprovante de bloqueio IMEI (operadora ou ANATEL) | IMEI + data bloqueio + operadora |
| `phone_kit` | Kit básico do celular sinistrado (caixa, acessórios) | foto dos itens |
| `travel_proof` | Comprovante/declaração de trajeto para devolução de bens | motivo + trajeto |

### Classificações especiais
| Tipo | Descrição |
|------|-----------|
| `irrelevant_document` | Documento sem relação com o sinistro |
| `handwritten_note` | Texto manuscrito sem formato institucional |
| `image_unreadable` | Imagem ilegível, cortada, desfocada ou escura demais |
| `mixed_or_multiple_documents` | Múltiplos documentos na mesma imagem/PDF |
| `duplicate_document` | Documento já enviado anteriormente (mesmo conteúdo) |

---

## HEURÍSTICAS CRÍTICAS

### BO vs. Aviso de Ocorrência (ERRO MAIS COMUM)

**Para classificar como `police_report`, EXIJA combinação de:**
- Número de registro/protocolo/boletim
- Órgão emissor (delegacia, Polícia Civil/Militar, sistema DP-Web/BO-e)
- Data do fato E/OU data do registro
- Narrativa formal de ocorrência
- Layout institucional (cabeçalho, brasão, autenticação, código de verificação)

**Classifique como `incident_notice` quando:**
- Documento descreve o evento mas é formulário privado, e-mail, carta, WhatsApp, manuscrito
- Tem narrativa do evento mas sem elementos formais de BO
- É comunicação à seguradora, corretora, assistência ou empregador

**REGRA DE OURO:** Na dúvida entre BO e aviso, NUNCA force como BO. Prefira `incident_notice` + `requires_human_review=true`.

### BRAT vs. BO
- BRAT é específico para acidentes de trânsito → `traffic_accident_report`
- BO cobre qualquer tipo de ocorrência → `police_report`
- Se o documento for BO que INCLUI acidente de trânsito, classifique como `police_report` com `document_subtype: "traffic_occurrence"`

### Fotos de dano vs. documento
- Foto de veículo danificado → `damage_photo` (NÃO `irrelevant_document`)
- Foto de celular quebrado → `damage_photo`
- Foto de bagagem/encomenda danificada → `damage_photo`
- Screenshot de app (Uber, 99, iFood) mostrando corridas → `work_period_proof`
- Screenshot de bloqueio IMEI → `imei_block_proof`

### Multi-documento
- Se uma imagem contém frente e verso do mesmo documento → classificar pelo tipo do documento (ex: `identity_document`), com `document_subtype: "front_and_back"`
- Se uma imagem contém 2+ documentos diferentes → `mixed_or_multiple_documents`

---

## PROCEDIMENTO OBRIGATÓRIO

1. Verifique legibilidade da imagem/PDF.
2. Identifique se é documento, foto de evidência, screenshot, manuscrito ou material irrelevante.
3. Classifique usando a taxonomia fechada.
4. Determine subtype quando aplicável.
5. Determine relevância para análise de sinistro.
6. Liste os campos-alvo mínimos para a próxima etapa (consulte `resources/extraction_fields.md`).
7. Gere resumo curto da evidência visual que sustentou a classificação.
8. Se houver ambiguidade real entre duas classes, sinalize `requires_human_review=true`.
9. Se o documento parecer duplicata de outro já recebido, sinalize `suspected_duplicate=true`.

---

## FORMATO DE SAÍDA

Responda APENAS em JSON válido:

```json
{
  "document_type": "police_report",
  "document_subtype": "civil_police_report",
  "is_relevant": true,
  "image_quality": "good",
  "requires_human_review": false,
  "suspected_non_document": false,
  "suspected_duplicate": false,
  "target_fields": ["report_number", "issuing_authority", "occurrence_date", "report_date", "insured_or_victim_name", "vehicle_plate", "short_narrative", "authenticity_markers"],
  "classification_evidence": ["cabeçalho Polícia Civil do Estado de SP", "número de BO visível", "data de registro presente", "código de autenticação no rodapé"],
  "confidence": 0.94,
  "notes": null
}
```

### Valores válidos para `image_quality`
- `good` — legível, nítido, completo
- `acceptable` — legível com esforço, parcialmente cortado
- `poor` — baixa resolução, muito escuro/claro, parcialmente ilegível
- `unreadable` — ilegível, use `document_type: "image_unreadable"`

### Regras de qualidade
- `confidence` entre 0 e 1.
- Seja conservador: quando faltar elemento mínimo, prefira classe mais genérica.
- Em caso de imagem ruim com algum conteúdo identificável, classifique com confidence baixa + `requires_human_review=true`.
- Em caso de imagem completamente ilegível, use `image_unreadable`.

---

## FEW-SHOT EXAMPLES

### Exemplo 1: BO legítimo
**Input:** PDF com brasão da Polícia Civil, nº 1234/2026, Delegacia de Polícia de Campinas, data 05/04/2026, narrativa formal de roubo de veículo.
```json
{
  "document_type": "police_report",
  "document_subtype": "civil_police_report",
  "is_relevant": true,
  "image_quality": "good",
  "requires_human_review": false,
  "suspected_non_document": false,
  "suspected_duplicate": false,
  "target_fields": ["report_number", "issuing_authority", "occurrence_date", "report_date", "insured_or_victim_name", "vehicle_plate", "short_narrative", "authenticity_markers"],
  "classification_evidence": ["brasão Polícia Civil SP", "nº BO 1234/2026", "delegacia identificada", "narrativa formal", "código verificação presente"],
  "confidence": 0.96,
  "notes": null
}
```

### Exemplo 2: Formulário privado confundível com BO
**Input:** PDF sem cabeçalho institucional, título "Relato de Ocorrência", preenchido pelo segurado, descrevendo roubo de celular durante entrega.
```json
{
  "document_type": "incident_notice",
  "document_subtype": "insured_narrative",
  "is_relevant": true,
  "image_quality": "good",
  "requires_human_review": false,
  "suspected_non_document": false,
  "suspected_duplicate": false,
  "target_fields": ["insured_name", "notice_date", "occurrence_date", "policy_or_product_reference", "short_narrative", "channel_or_origin"],
  "classification_evidence": ["sem cabeçalho institucional", "sem número de registro oficial", "título genérico 'Relato de Ocorrência'", "preenchido pelo próprio segurado"],
  "confidence": 0.91,
  "notes": "Apesar do título sugerir ocorrência policial, não há elementos formais de BO. Classificado como aviso."
}
```

### Exemplo 3: Screenshot de app Uber
**Input:** Screenshot mostrando histórico de corridas no app Uber, data 03/04/2026, 8 corridas realizadas.
```json
{
  "document_type": "work_period_proof",
  "document_subtype": "app_screenshot_uber",
  "is_relevant": true,
  "image_quality": "acceptable",
  "requires_human_review": false,
  "suspected_non_document": false,
  "suspected_duplicate": false,
  "target_fields": ["driver_name", "platform", "date", "work_period_start", "work_period_end", "trip_count"],
  "classification_evidence": ["interface Uber reconhecível", "lista de corridas visível", "data presente"],
  "confidence": 0.88,
  "notes": "Screenshot de app — qualidade depende da resolução da captura."
}
```
