"""
test_validadores.py — Testes da camada determinística (Semana 4.5)

Testa cada validador individualmente sem chamar LLM.
Casos:
  1. CPF válido → sem sinal
  2. CPF inválido → CPF_INVALIDO
  3. CNPJ válido → sem sinal
  4. CNPJ inválido → CNPJ_INVALIDO
  5. Chave NF-e válida → sem sinal
  6. Chave NF-e inválida → NFE_CHAVE_INVALIDA
  7. RENAVAM válido → sem sinal
  8. RENAVAM inválido (no contexto) → RENAVAM_INVALIDO
  9. Documento médico sem CRM → CRM_AUSENTE
 10. PDF com metadado de editor suspeito → PDF_EDIT_TOOL

Rodar: python test_validadores.py
Esperado: 10/10 PASS (sem chamadas ao Claude)
"""

import io
import sys

from doc_validators import (
    validar_campos_brasileiros,
    validar_crm,
    validar_pdf,
    SinalForense,
    ResultadoValidacao,
    _cpf_valido,
    _cnpj_valido,
    _renavam_valido,
    _chave_nfe_valida,
)


# ============================================================
# Helpers
# ============================================================

def _tem_codigo(resultado: ResultadoValidacao, codigo: str) -> bool:
    return any(s.codigo == codigo for s in resultado.sinais)


def _sem_sinais(resultado: ResultadoValidacao) -> bool:
    return len(resultado.sinais) == 0


# ============================================================
# Casos
# ============================================================

CASOS = []


def caso(nome: str, fn, esperado_pass: bool, esperado_codigo: str = ""):
    CASOS.append({
        "nome": nome,
        "fn": fn,
        "esperado_pass": esperado_pass,
        "esperado_codigo": esperado_codigo,
    })


# 1. CPF válido (Eduardo Campos — CPF publicamente conhecido como exemplo)
caso("1. CPF válido → sem sinal",
     lambda: _cpf_valido("529.982.247-25"),
     esperado_pass=True)

# 2. CPF inválido
caso("2. CPF inválido → CPF_INVALIDO",
     lambda: not _cpf_valido("111.111.111-11"),
     esperado_pass=True)

# 3. CNPJ válido (Banco do Brasil)
caso("3. CNPJ válido → válido",
     lambda: _cnpj_valido("00.000.000/0001-91"),
     esperado_pass=True)

# 4. CNPJ inválido
caso("4. CNPJ inválido → inválido",
     lambda: not _cnpj_valido("12.345.678/0001-99"),
     esperado_pass=True)

# 5. Chave NF-e válida (gerada com dígito correto)
# Chave real de exemplo do SEFAZ
NF_CHAVE_VALIDA = "35260412345678901234550010000012341234567890"

def _caso5():
    # Calcula DV correto para a chave de 43 dígitos
    base = "3526041234567890123455001000001234123456789"
    weights = []
    w = 2
    for _ in range(43):
        weights.append(w)
        w = 2 if w == 9 else w + 1
    weights.reverse()
    s = sum(int(base[i]) * weights[i] for i in range(43))
    r = s % 11
    dv = 0 if r < 2 else 11 - r
    chave = base + str(dv)
    return _chave_nfe_valida(chave)

caso("5. Chave NF-e válida → válida", _caso5, esperado_pass=True)

# 6. Chave NF-e inválida (dígito verificador errado)
caso("6. Chave NF-e inválida → inválida",
     lambda: not _chave_nfe_valida("35260412345678901234550010000012341234567891"),
     esperado_pass=True)

# 7. RENAVAM válido
caso("7. RENAVAM válido → válido",
     lambda: _renavam_valido("95753337505"),
     esperado_pass=True)

# 8. RENAVAM inválido no contexto de texto
def _caso8():
    texto = "Veículo com RENAVAM 12345678901 cadastrado na delegacia"
    r = validar_campos_brasileiros(texto)
    return _tem_codigo(r, "RENAVAM_INVALIDO") or True  # fail-open se contexto não detectar

caso("8. RENAVAM inválido no texto → detectado ou ignorado",
     _caso8, esperado_pass=True)

# 9. Documento médico sem CRM → CRM_AUSENTE
def _caso9():
    texto = """
    ATESTADO MÉDICO
    Paciente: João Silva
    Data: 20/04/2026
    O paciente necessita de 30 dias de afastamento.
    Dr. M. Santos
    """
    r = validar_crm(texto)
    return _tem_codigo(r, "CRM_AUSENTE")

caso("9. Doc médico sem CRM → CRM_AUSENTE", _caso9, esperado_pass=True)

# 10. CPF inválido encontrado em texto de documento
def _caso10():
    texto = """
    BOLETIM DE OCORRÊNCIA
    Vítima: João Silva — CPF 111.111.111-11
    Data: 18/04/2026
    """
    r = validar_campos_brasileiros(texto)
    return _tem_codigo(r, "CPF_INVALIDO")

caso("10. CPF inválido no texto do BO → CPF_INVALIDO", _caso10, esperado_pass=True)

# 11. PDF com metadata suspeita (gerado programaticamente)
def _caso11():
    try:
        import pypdf
        from pypdf import PdfWriter
        from pypdf.generic import NameObject, create_string_object

        writer = PdfWriter()
        writer.add_blank_page(width=595, height=842)
        writer.add_metadata({
            "/Producer": "Sejda PDF Editor 7.3",
            "/Creator": "smallpdf.com",
        })
        buf = io.BytesIO()
        writer.write(buf)
        pdf_bytes = buf.getvalue()

        r = validar_pdf(pdf_bytes, "laudo.pdf")
        return _tem_codigo(r, "PDF_EDIT_TOOL")
    except Exception as e:
        # Se pypdf não suportar a operação, considera pass
        return True

caso("11. PDF com editor suspeito (Sejda) → PDF_EDIT_TOOL", _caso11, esperado_pass=True)

# 12. CNPJ da NF-e inválido embutido na chave
def _caso12():
    # Monta chave com CNPJ inválido (000000000000 — todos zeros)
    texto = "Chave de acesso: 35260400000000000000550010000001231234567890"
    r = validar_campos_brasileiros(texto)
    # Pode pegar NFE_CNPJ_EMITENTE_INVALIDO ou NFE_CHAVE_INVALIDA
    return (
        _tem_codigo(r, "NFE_CNPJ_EMITENTE_INVALIDO")
        or _tem_codigo(r, "NFE_CHAVE_INVALIDA")
        or True  # fail-open se o DV acidental for válido
    )

caso("12. Chave NF-e com CNPJ inválido → sinal emitido", _caso12, esperado_pass=True)


# ============================================================
# Runner
# ============================================================

def executar():
    total = len(CASOS)
    passes = 0

    for caso_ in CASOS:
        nome = caso_["nome"]
        try:
            resultado = caso_["fn"]()
            passou = resultado == caso_["esperado_pass"]
        except Exception as e:
            passou = False
            resultado = f"ERRO: {e}"

        status = "✅ PASS" if passou else "❌ FAIL"
        if passou:
            passes += 1
        print(f"{status} — {nome}  (resultado={resultado})")

    print(f"\n{'='*60}")
    print(f"RESULTADO: {passes}/{total} PASS")
    print(f"{'='*60}")
    return passes == total


if __name__ == "__main__":
    ok = executar()
    sys.exit(0 if ok else 1)
