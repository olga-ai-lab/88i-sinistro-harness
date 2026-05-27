---
name: ocr-para-sinistros
description: "Converte imagens/PDFs de sinistro em texto estruturado via OCR (Tesseract, Vision API) com fallback para manual input. Use quando receber documentos em formato visual que precisam virar texto processável. Trigger em: 'reconhecimento de caracteres', 'OCR', 'digitalizar documento', 'converter PDF', 'imagem para texto', 'documento ilegível', 'manuscrito'."
version: 1.0.0
author: Olga AI Lab
license: MIT
metadata:
  hermes:
    tags: [seguros, sinistros, 88i, ocr, processamento-imagem]
    related_skills: [sinistro-analyzer, sinistro-doc-classifier]
---

# OCR Customizado para Sinistros — 88i Seguradora

## Overview

Skill especializada em **conversão de imagem → texto** com **otimizações para sinistros**:

- 📄 Documentos oficiais (BO, CRLV, RG)
- 📋 Formulários estruturados
- 📝 Manuscritos legíveis
- 🔧 Detecção automática de idioma (PT-BR)
- 🎯 Limpeza de caracteres espúrios (OCR ruído)

Integra **Tesseract + Vision Claude + fallback manual** para máxima acurácia.

## When to Use

- ✅ **Documento visual** (JPEG, PNG, PDF)
- ✅ **Precisa** converter em texto estruturado
- ✅ **Qualidade** varia (boa → ruim)
- ✅ **Fallback manual** disponível se OCR falhar

### Não use para:

- ❌ Extração direta de campos (use `sinistro-analyzer` — já faz OCR internamente)
- ❌ Análise de conteúdo (use `sinistro-doc-forensics`)
- ❌ Classificação documental (use `sinistro-doc-classifier`)

## 3 Pipelines de OCR

### Pipeline 1️⃣: **Vision Claude** (melhor qualidade)

```python
# Usar quando: imagem boa + documento complexo
# Tempo: ~3-5s
# Custo: ~0.01 USD/imagem (Vision token)

from anthropic import Anthropic

client = Anthropic()
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=2048,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": base64_image
                    }
                },
                {
                    "type": "text",
                    "text": """
Você é especialista em OCR de documentos seguros.
Extraia TODO o texto visível, mantendo formatação original.
Indique ilegibilidade com [ILEGÍVEL].
Retorne apenas o texto, sem comentários.
                    """
                }
            ]
        }
    ]
)

texto_extraido = response.content[0].text
print(texto_extraido)
```

**Quando usar:**
- ✅ Documento claro (qualidade BOA)
- ✅ Documento oficial (BO, CRLV, RG)
- ✅ Precisão > velocidade
- ✅ Orçamento disponível

### Pipeline 2️⃣: **Tesseract Local** (rápido + offline)

```python
# Usar quando: processamento em lote + offline
# Tempo: ~1-2s
# Custo: ZERO (open source)

import pytesseract
from PIL import Image
import cv2

# Imagem → texto bruto
imagem = Image.open("documento.jpg")

# Pré-processamento (melhora acurácia em 20-30%)
opencv_img = cv2.imread("documento.jpg")
gray = cv2.cvtColor(opencv_img, cv2.COLOR_BGR2GRAY)
_, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
denoised = cv2.fastNlMeansDenoising(thresh)

# OCR
texto_bruto = pytesseract.image_to_string(
    Image.fromarray(denoised),
    lang="por"  # Portuguese
)

# Limpeza
texto_limpo = limpar_ocr_ruido(texto_bruto)
print(texto_limpo)

def limpar_ocr_ruido(texto):
    """Remove artefatos comuns de OCR"""
    # Caracteres espúrios
    texto = texto.replace("O", "0")  # O → 0 em números
    texto = texto.replace("l", "1")  # l → 1 em sequências
    
    # Espaços duplos
    while "  " in texto:
        texto = texto.replace("  ", " ")
    
    # Linhas vazias
    linhas = [l.strip() for l in texto.split("\n") if l.strip()]
    return "\n".join(linhas)
```

**Quando usar:**
- ✅ Processamento em lote (100+ docs)
- ✅ Offline (sem internet)
- ✅ Documentos claros
- ✅ Orçamento zero

### Pipeline 3️⃣: **Manual Input** (fallback)

```python
# Usar quando: OCR falha + documento crítico
# Tempo: ~5-10 min (digitação manual)
# Custo: Labor

async def ocr_com_fallback(
    imagem_path: str,
    qualidade_esperada: str,  # "boa", "ok", "ruim"
    tipo_doc: str  # "boletim", "laudo", etc
):
    """
    Tenta Pipeline 1 → Pipeline 2 → Pipeline 3
    """
    
    # Tentar Vision Claude
    try:
        texto = await ocr_vision_claude(imagem_path)
        if confianca_texto(texto) > 0.85:
            return {"metodo": "vision", "texto": texto, "confianca": 0.95}
    except:
        pass
    
    # Tentar Tesseract
    try:
        texto = ocr_tesseract_local(imagem_path)
        if confianca_texto(texto) > 0.75:
            return {"metodo": "tesseract", "texto": texto, "confianca": 0.82}
    except:
        pass
    
    # Fallback manual
    return {
        "metodo": "manual",
        "texto": None,
        "confianca": 0.0,
        "acao": "solicitar_digitacao_manual",
        "mensagem": f"Documento {tipo_doc} ilegível. Solicitar segurado redigitalizar ou digitar."
    }
```

## Pré-processamento de Imagem

### Melhora de qualidade (antes de OCR):

```python
import cv2
import numpy as np

def preprocessar_imagem(imagem_path):
    """
    Melhora imagem para OCR (aumenta acurácia em 20-40%)
    """
    
    # 1. Ler
    img = cv2.imread(imagem_path)
    
    # 2. Redimensionar se muito pequena
    altura, largura = img.shape[:2]
    if altura < 300:
        img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    
    # 3. Converter para escala de cinza
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 4. Remover ruído
    denoised = cv2.fastNlMeansDenoising(gray, None, 10, 10, 21)
    
    # 5. Binarização (preto/branco)
    _, binary = cv2.threshold(denoised, 150, 255, cv2.THRESH_BINARY)
    
    # 6. Dilation + Erosion (corrige pequenos erros)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    
    # Resultado
    return cleaned

# Usar
imagem_processada = preprocessar_imagem("documento.jpg")
texto = pytesseract.image_to_string(imagem_processada, lang="por")
```

**Melhoria esperada:**
- Imagem BOA: 95-99% acurácia
- Imagem OK: 80-90% acurácia (depois de pré-processamento)
- Imagem RUIM: <70% (requer manual)

## Limpeza Pós-OCR

```python
def limpar_texto_ocr(texto, tipo_doc):
    """
    Remove artefatos de OCR específicos por tipo documental
    """
    
    # Caracteres espúrios comuns
    replacements = {
        "O": "0",      # O-maiúscula → 0 em números
        "l": "1",      # L-minúscula → 1 em sequências
        "|": "1",      # Pipe → 1
        "S": "5",      # S → 5 (cuidado: validar contexto)
        "Z": "2",      # Z → 2 (cuidado)
    }
    
    # BOLETIM: campos numéricos
    if tipo_doc == "boletim":
        # Número BO: sempre numérico
        padrao_bo = r"BO\s*[#:]?\s*([A-Za-z0-9]{9,})"
        texto = re.sub(padrao_bo, lambda m: f"BO: {m.group(1).upper()}", texto)
    
    # CRLV: formato numérico rígido
    if tipo_doc == "crlv":
        # Placa: sempre letras+números
        padrao_placa = r"[A-Z]{3}-?\d{4}"
        # RENAVAM: sempre 11 dígitos
        padrao_renavam = r"\d{11}"
    
    # Limpeza geral
    for old, new in replacements.items():
        texto = texto.replace(old, new)
    
    # Espaços e quebras
    while "  " in texto:
        texto = texto.replace("  ", " ")
    while "\n\n\n" in texto:
        texto = texto.replace("\n\n\n", "\n\n")
    
    return texto.strip()
```

## Avaliação de Confiança

```python
def confianca_texto(texto, tipo_doc=None):
    """
    Estima qualidade da extração OCR (0.0 - 1.0)
    """
    
    score = 1.0
    
    # Penalidades
    if "[ILEGÍVEL]" in texto:
        score -= 0.15
    
    if len(texto) < 50:
        score -= 0.10  # Muito curto
    
    # Padrões esperados por tipo
    if tipo_doc == "boletim":
        if not re.search(r"BO\s*[:=#]?\s*\d{9,}", texto):
            score -= 0.20  # Número BO não encontrado
        if not re.search(r"\d{4}-\d{2}-\d{2}", texto):
            score -= 0.10  # Data não encontrada
    
    if tipo_doc == "crlv":
        if not re.search(r"[A-Z]{3}-?\d{4}", texto):
            score -= 0.25  # Placa não encontrada
        if not re.search(r"\d{11}", texto):
            score -= 0.15  # RENAVAM ausente
    
    return max(0.0, score)

# Usar
texto = ocr_tesseract(imagem)
confianca = confianca_texto(texto, tipo_doc="boletim")
print(f"Confiança OCR: {confianca:.0%}")
```

## Integração com Pipeline

```python
async def ocr_sinistro(
    imagem_path: str,
    tipo_doc: str,
    qualidade_esperada: str
):
    """
    Orquestra OCR + limpeza + validação
    """
    
    # 1. Pré-processar
    imagem_prep = preprocessar_imagem(imagem_path)
    
    # 2. Escolher método baseado em qualidade esperada
    if qualidade_esperada == "boa":
        # Vision Claude (melhor)
        texto = await ocr_vision_claude(imagem_path)
    elif qualidade_esperada == "ok":
        # Tesseract (rápido)
        texto = ocr_tesseract_local(imagem_prep)
    else:
        # Ruim: fallback manual
        return {
            "acao": "manual",
            "motivo": "Qualidade insuficiente para OCR automático"
        }
    
    # 3. Limpar
    texto_limpo = limpar_texto_ocr(texto, tipo_doc)
    
    # 4. Avaliar confiança
    confianca = confianca_texto(texto_limpo, tipo_doc)
    
    # 5. Retornar
    return {
        "texto": texto_limpo,
        "confianca": confianca,
        "metodo_ocr": "vision" if qualidade_esperada == "boa" else "tesseract",
        "tipo_doc": tipo_doc,
        "validacao": "PASSA" if confianca > 0.75 else "MANUAL_REVIEW"
    }
```

## Common Pitfalls

1. **Confundir OCR com extração de campos**
   - Solução: OCR = texto bruto; extração = estrutura JSON

2. **Usar Tesseract em documento muito pequeno**
   - Solução: redimensionar 2x antes (scale=200%)

3. **Não normalizar idioma**
   - Solução: sempre `lang="por"` para português

4. **Falhar em manuscrito sem fallback**
   - Solução: sempre ter fallback manual documentado

5. **Ignorar ruído de OCR**
   - Solução: sempre limpar texto (replacements + regex)

6. **Não validar formato pós-OCR**
   - Solução: verificar padrões esperados (placa, BO, datas)

## Verification Checklist

- [ ] OCR retornou texto (não vazio)
- [ ] Texto foi limpeza de artefatos
- [ ] Score confiança foi calculado
- [ ] Se confiança < 75%: fallback manual acionado
- [ ] Padrões esperados (placa, BO, datas) validados
- [ ] Tipo documental é conhecido
- [ ] Pronto para `sinistro-analyzer`

## One-Shot Recipe: OCR Boletim

```bash
hermes skill ocr-para-sinistros

# INPUT
imagem: "boletim_foto.jpg"
tipo_doc: "boletim"
qualidade_esperada: "ok"

# EXECUTE
[ocr-para-sinistros]
  1. Pré-processar imagem
  2. OCR via Tesseract
  3. Limpar ruído
  4. Validar padrões (BO, data, crime)
  5. Avaliar confiança

# OUTPUT
{
  "texto": "BOLETIM DE OCORRÊNCIA\nNúmero: 123456789\nData: 15/05/2026\nTipo: Roubo...",
  "confianca": 0.87,
  "metodo": "tesseract",
  "validacao": "PASSA",
  "padroes_encontrados": [
    "numero_bo: 123456789",
    "data: 2026-05-15",
    "tipo_crime: roubo"
  ]
}
```
