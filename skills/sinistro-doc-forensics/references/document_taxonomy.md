# Taxonomia Documental de Sinistro — 88i Seguradora Digital (v2)

## Objetivo
Padronizar a classificação documental para reduzir custo, latência e inconsistência no pipeline de análise de sinistros.

## Classes válidas (v2 — expandida)

### Documentos oficiais
- `police_report` — BO emitido por autoridade competente
- `traffic_accident_report` — BRAT (Boletim de Registro de Acidente de Trânsito)
- `non_location_certificate` — Certidão de não localização de veículo

### Documentos médicos
- `medical_report` — Laudo/relatório médico com descrição clínica
- `medical_certificate` — Atestado médico (afastamento/aptidão)

### Documentos de identificação e comprovação
- `identity_document` — RG, CNH, CPF, passaporte
- `proof_of_address` — Comprovante de residência (≤90 dias para 88i)
- `vehicle_document` — CRLV, CRV
- `invoice_receipt` — Nota fiscal (NF-e c/ chave SEFAZ) ou cupom fiscal

### Documentos do sinistro
- `claim_form` — Aviso/formulário de sinistro preenchido
- `incident_notice` — Comunicação do evento sem elementos de BO
- `authorization_form` — Procuração, termo de autorização
- `work_period_proof` — Comprovante de período de trabalho (screenshot app, log plataforma)
- `repair_estimate` — Orçamento ou laudo de oficina
- `damage_photo` — Foto dos danos (veículo, celular, bagagem)
- `imei_block_proof` — Comprovante de bloqueio IMEI
- `phone_kit` — Foto do kit básico do celular sinistrado
- `travel_proof` — Comprovante de trajeto para devolução de bens

### Classificações especiais
- `irrelevant_document` — Sem relação com o sinistro
- `handwritten_note` — Manuscrito sem formato institucional
- `image_unreadable` — Ilegível
- `mixed_or_multiple_documents` — Múltiplos docs na mesma imagem
- `duplicate_document` — Documento já enviado

---

## Diferença crítica: BO vs. Aviso de Ocorrência

### police_report
Documento emitido por autoridade competente. DEVE ter: nº registro + órgão emissor + data fato + narrativa formal. Preferencialmente com código de verificação/autenticação digital.

### incident_notice
Comunicação do evento à seguradora/corretora/assistência/empregador. NÃO substitui BO quando a regra exigir BO (Coberturas A, I e III da 88i).

### traffic_accident_report (BRAT)
Específico para acidentes de trânsito. Obrigatório para Cobertura II (Colisão) da 88i. NÃO substitui BO para roubo/furto.

## Regra de ouro
Dúvida real entre `police_report` e `incident_notice`? → NÃO forçar BO. Usar `incident_notice` + `requires_human_review=true`.

## Novas classes na v2
As classes `traffic_accident_report`, `non_location_certificate`, `work_period_proof`, `repair_estimate`, `damage_photo`, `imei_block_proof`, `phone_kit`, `travel_proof` e `duplicate_document` foram adicionadas para cobrir documentos específicos do ecossistema delivery/mobilidade da 88i que antes eram forçados em classes genéricas.
