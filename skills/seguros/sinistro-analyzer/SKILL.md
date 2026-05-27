---
name: sinistro-analyzer
description: "Extrai e estrutura campos de documentos de sinistro 88i (boletim, laudo técnico, nota fiscal, CRLV) para análise subsequente. Use quando precisar transformar documentos não-estruturados (PDF, fotos) em dados estruturados (tabela, JSON). Trigger em: 'extrair campos', 'analisar documento', 'documentação do sinistro', 'estruturar dados', 'preparar análise', 'campos do boletim', pipeline de análise."
version: 1.0.0
author: Olga AI Lab
license: MIT
metadata:
  hermes:
    tags: [seguros, sinistros, 88i, extração, análise]
    related_skills: [sinistro-doc-classifier, sinistro-doc-forensics, sinistro-claim-adjudicator]
---

# Extrator de Campos — Sinistros 88i

## Overview

Skill especializada em **extrair e estruturar** campos de documentos de sinistro (boletim, laudo, nota fiscal, CRLV, aviso prévio, etc.) para formato processável (JSON, CSV, tabela Markdown).

Diferente de `sinistro-doc-forensics` (que valida + detecta suspeitas), **sinistro-analyzer** é focado em **transformação estrutural** — converte imagem/PDF em dados tabulares prontos para análise.

## When to Use

- ✅ **Recebeu** documento visual (foto, PDF, screenshot) em contexto de sinistro
- ✅ **Precisa** extrair dados em formato estruturado (JSON/CSV/tabela)
- ✅ **Documento** é de sinistro 88i (BO, laudo, NF, CRLV, aviso, RG, CNH, contrato)
- ✅ **Dados** serão processados por regra ou banco de dados

### Não use para:

- ❌ Validação de autenticidade (use `sinistro-doc-forensics`)
- ❌ Decisão de cobertura (use `sinistro-claim-adjudicator`)
- ❌ Classificação de tipo documental (use `sinistro-doc-classifier`)

## Fluxo Típico

```
Documento (PDF/foto)
    ↓
[sinistro-doc-classifier]  ← Qual tipo?
    ↓
[sinistro-analyzer]        ← Qual estrutura?  ← VOCÊ ESTÁ AQUI
    ↓
[sinistro-doc-forensics]   ← É legítimo?
    ↓
[sinistro-claim-adjudicator] ← Aprova?
```

## Campos Extraíveis por Tipo Documental

### 1. **BOLETIM DE OCORRÊNCIA (BO)**

```json
{
  "tipo_doc": "boletim",
  "numero_bo": "123456789",
  "delegacia": "DP Zona Sul",
  "data_ocorrencia": "2026-05-15",
  "hora_ocorrencia": "14:30",
  "tipo_crime": "roubo",
  "localizacao": {
    "endereco": "Av. Paulista, 1000",
    "municipio": "São Paulo",
    "estado": "SP",
    "cep": "01311-100"
  },
  "descricao_fato": "Furto de motocicleta Honda CB500...",
  "vitima": {
    "nome": "João Silva",
    "cpf": "12345678901",
    "telefone": "(11) 99999-9999"
  },
  "bens_roubados": [
    {
      "tipo": "motocicleta",
      "marca": "Honda",
      "modelo": "CB500",
      "cor": "preta",
      "placa": "ABC1234",
      "ano": 2024
    }
  ],
  "qualidade_imagem": "boa" | "ok" | "ruim"
}
```

### 2. **LAUDO TÉCNICO / PERÍCIA**

```json
{
  "tipo_doc": "laudo",
  "numero_laudo": "LT-2026-001",
  "perito": "Carlos Mendes (CREA 123456)",
  "data_inspecao": "2026-05-16",
  "veiculo": {
    "placa": "ABC1234",
    "marca": "Honda",
    "modelo": "CB500",
    "ano": 2024,
    "chassis": "JHMCF5314LC100000",
    "odometro": "15000",
    "combustivel": "1/2"
  },
  "danos": [
    {
      "local": "painel frontal",
      "tipo": "amassado",
      "severidade": "grave",
      "reparavel": true,
      "valor_reparo_estimado": 8500.00
    }
  ],
  "causa_sinistro": "colisão",
  "inutilizacao": false,
  "opiniao_perito": "Veículo em condições de reparação, valor estimado...",
  "qualidade_imagem": "boa" | "ok" | "ruim"
}
```

### 3. **NOTA FISCAL / RECIBO**

```json
{
  "tipo_doc": "nota_fiscal",
  "numero_nf": "000123",
  "serie": "A",
  "emitente": {
    "nome": "Oficina Silva Ltda",
    "cnpj": "12345678000190",
    "endereco": "Rua X, 100"
  },
  "data_emissao": "2026-05-16",
  "descricao_servico": "Reparo de painel frontal",
  "valor_total": 8500.00,
  "forma_pagamento": "Cartão",
  "observacoes": "Peças: tinta, massa, mão de obra...",
  "chave_nfe": null, // Se digital
  "qualidade_imagem": "boa"
}
```

### 4. **CRLV (Certificado Registro Licenciamento Veículo)**

```json
{
  "tipo_doc": "crlv",
  "veiculo": {
    "placa": "ABC1234",
    "renavam": "12345678901234",
    "marca": "Honda",
    "modelo": "CB500",
    "ano": 2024,
    "cilindrada": "500",
    "cor": "preta",
    "combustivel": "gasolina"
  },
  "proprietario": {
    "nome": "João Silva",
    "cpf": "12345678901",
    "endereco": "Rua Y, 200"
  },
  "vigencia": {
    "data_inicio": "2026-01-01",
    "data_vencimento": "2026-12-31"
  },
  "impostos_pagos": true,
  "multas": false,
  "qualidade_imagem": "boa"
}
```

### 5. **RG / CNH (Identidade)**

```json
{
  "tipo_doc": "rg" | "cnh",
  "numero": "123456789",
  "orgao_emissor": "SSP-SP",
  "data_emissao": "2020-01-15",
  "data_validade": "2030-01-15",
  "titular": {
    "nome": "João Silva",
    "cpf": "12345678901",
    "data_nascimento": "1990-05-10",
    "sexo": "M",
    "nacionalidade": "Brasileira"
  },
  "valido": true,
  "qualidade_imagem": "boa"
}
```

## Extração em 3 Passos

### 1️⃣ **Upload & Conversão**

```bash
# Terminal/browser já fez:
# $ upload_image("boletim.pdf")
# Hermes converte para imagem (se PDF)
```

### 2️⃣ **Classificação** (já feita por `sinistro-doc-classifier`)

```
Tipo: BOLETIM → Estrutura JSON conhecida
Qualidade: BOA → Confiança alta em OCR
Campos-alvo: número_bo, data, tipo_crime, vítima, bens
```

### 3️⃣ **Extração com Vision + Fallback**

```python
# Seu código (ou use tools/code_execution)

from baml_client import baml

# Opção A: Vision nativa (Claude)
resultado = await baml.extrator_boletim(
    imagem_base64=base64.b64encode(pdf_bytes).decode(),
    tipo_doc="boletim"
)

# Opção B: Fallback via OCR (se Vision falhar)
texto_ocr = pytesseract.image_to_string(imagem)
resultado = await baml.extrator_boletim_texto(texto_ocr)

print(json.dumps(resultado, indent=2, ensure_ascii=False))
```

## Qualidade de Imagem & Confiança

| Qualidade | Confiança | Usar | Ação |
|-----------|-----------|------|------|
| **BOA** | 90-100% | ✅ Sempre | Extrai direto |
| **OK** | 70-90% | ⚠️ Condicional | Valida com `sinistro-doc-forensics` |
| **RUIM** | <70% | ❌ Não recomendado | Solicitar recaptura / manual review |

## Casos Especiais

### ❓ Documento Manual/Manuscrito

```json
{
  "tipo_doc": "aviso_prévio",
  "documento_manuscrito": true,
  "qualidade_imagem": "ruim",
  "recomendacao": "Solicitar cópia digitalizada ou digitação manual"
}
```

### ❓ Múltiplas Páginas

Processar página por página:

```bash
# Para cada página:
extrair_campos("boletim_page1.pdf")
extrair_campos("boletim_page2.pdf")
# Depois: merge estruturado
```

### ❓ Documento com Carimbo/Assinatura

Incluir na extração:

```json
{
  "carimbo_presente": true,
  "carimbo_legivel": true,
  "assinatura_presente": true,
  "assinatura_legivel": false,
  "qualidade_imagem": "ok"
}
```

## Integração com BAML

### Arquivo: `baml_src/sinistro_extractors.baml`

```baml
function extrator_boletim(
  imagem_base64: string,
  tipo_doc: "boletim" | "laudo" | "nf" | "crlv" | "rg"
) -> BoletimExtraido {
  client "claude-opus"
  prompt #"
    Você é perito documental especializado em sinistros seguros.
    Analise a imagem do {{ tipo_doc }} e extraia TODOS os campos.
    
    Retorne JSON estruturado com campos rigorosamente tipados.
    Se campo não estiver visível, marque como null.
    Avalie qualidade_imagem: "boa", "ok" ou "ruim".
  "#
}

type BoletimExtraido {
  numero_bo: string?
  delegacia: string?
  data_ocorrencia: string? // ISO 8601
  tipo_crime: string?
  // ... outros campos
  qualidade_imagem: "boa" | "ok" | "ruim"
  confianca_extracao: float // 0.0 - 1.0
}
```

## Common Pitfalls

1. **Assumir OCR perfeito de imagem ruim**
   - Solução: sempre validar `qualidade_imagem` antes de usar dados

2. **Não normalizar datas/valores monetários**
   - Solução: converter para ISO 8601 / padrão numérico

3. **Misturar extração com validação**
   - Solução: `sinistro-analyzer` = extrae; `sinistro-doc-forensics` = valida

4. **Não preservar documento original**
   - Solução: guardar hash MD5 / referência ao PDF original

5. **Confundir com classificação documental**
   - Solução: tipos documentais vêm do `sinistro-doc-classifier`

6. **PDF com múltiplas páginas = 1 chamada**
   - Solução: processar página a página, depois mesclar

## Verification Checklist

- [ ] Documento foi classificado por `sinistro-doc-classifier` primeiro
- [ ] Tipo documental é conhecido (BO, laudo, NF, CRLV, RG, CNH)
- [ ] Qualidade de imagem foi avaliada
- [ ] JSON estruturado contém todos os campos esperados
- [ ] Valores monetários foram normalizados (pt-BR → float)
- [ ] Datas estão em ISO 8601 (YYYY-MM-DD)
- [ ] `confianca_extracao` score está documentado
- [ ] Hash MD5 do documento original está salvo
- [ ] Pronto para enviar para `sinistro-doc-forensics`

## One-Shot Recipe: Extrair Boletim

```bash
# 1. Assumindo documento já classificado como BOLETIM

hermes skill sinistro-analyzer
# Dentro do skill:
## INPUT
documento: "boletim.pdf"
tipo_doc: "boletim"

## TOOLS
# browser_vision(question="Extrair número BO, data, tipo crime, vítima, bens roubados")
# code_execution(python: enviar para BAML)

## OUTPUT
{
  "numero_bo": "123456789",
  "data_ocorrencia": "2026-05-15",
  "tipo_crime": "roubo",
  "vitima": {"nome": "João Silva", "cpf": "12345678901"},
  "bens_roubados": [...],
  "qualidade_imagem": "boa",
  "confianca_extracao": 0.95
}
```
