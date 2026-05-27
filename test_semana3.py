"""
test_semana3.py — Testes do rules engine (Semana 3)

5 casos cobrindo os cenários críticos das regras D1-D15:
  1. DITA Uber com apólice vigente → elegível, docs pendentes
  2. Recusa por carência ativa (D2)
  3. Recusa moto em Produto A/Uber (D6)
  4. Recusa tipo incompatível Uber (D7 — IPA não cobre Uber)
  5. BAGAGEM com declaração prévia presente → elegível, aprovado

Rodar: python test_semana3.py
Esperado: 5/5 PASS
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from rules_engine import avaliar_cobertura, VeredictoCobertura
from tools import DadosApolice, HistoricoSinistros


# ============================================================
# Stubs de ExtracaoSinistro (sem depender do BAML/LLM)
# ============================================================

@dataclass
class _Veiculo:
    tipo: str
    placa: Optional[str] = None
    descricao_livre: Optional[str] = None


@dataclass
class _RedFlag:
    tipo: str
    descricao: str
    severidade: str


@dataclass
class _ExtracaoStub:
    tipo_sinistro: str          # string simples para testes
    confianca: float = 0.85
    veiculo: Optional[_Veiculo] = None
    documentos_mencionados: list = field(default_factory=list)
    red_flags: list = field(default_factory=list)
    campos_faltantes: list = field(default_factory=list)

    # o motor chama .value — simular com property
    @property
    def tipo_sinistro_value(self):
        return self.tipo_sinistro


# ============================================================
# Fixtures reutilizáveis
# ============================================================

APOLICE_VIGENTE = DadosApolice(
    encontrada=True,
    segurado_id="SEG-001",
    produto="B",
    coberturas=["DITA"],
    vigencia_inicio=date(2025, 1, 1),
    vigencia_fim=date(2026, 12, 31),
    vigente_hoje=True,
    carencia_ativa=False,
)

APOLICE_CARENCIA = DadosApolice(
    encontrada=True,
    segurado_id="SEG-CARENCIA",
    produto="B",
    coberturas=["DITA"],
    vigencia_inicio=date(2026, 5, 1),
    vigencia_fim=date(2027, 4, 30),
    vigente_hoje=True,
    carencia_ativa=True,   # <<< em carência
)

APOLICE_PRODUTO_A = DadosApolice(
    encontrada=True,
    segurado_id="SEG-PROD-A",
    produto="A",
    coberturas=["A_COB_II"],
    vigencia_inicio=date(2025, 1, 1),
    vigencia_fim=date(2026, 12, 31),
    vigente_hoje=True,
    carencia_ativa=False,
)

APOLICE_VIGENTE_C = DadosApolice(
    encontrada=True,
    segurado_id="SEG-BAGAGEM",
    produto="C",
    coberturas=["C_COB_A"],
    vigencia_inicio=date(2025, 6, 1),
    vigencia_fim=date(2026, 12, 31),
    vigente_hoje=True,
    carencia_ativa=False,
)

HISTORICO_LIMPO = HistoricoSinistros(
    encontrado=True,
    segurado_id="SEG-001",
    total_sinistros=0,
    sinistros_12_meses=0,
    alerta_frequencia=False,
)


# ============================================================
# Casos de teste
# ============================================================

CASOS = [
    # 1. DITA Uber — mesmos de antes
    {
        "nome": "1. DITA Uber — elegível com docs pendentes",
        "tipo_sinistro": "DITA",
        "plataforma": "UBER",
        "apolice": APOLICE_VIGENTE,
        "historico": HISTORICO_LIMPO,
        "extracao": _ExtracaoStub(tipo_sinistro="DITA",
            documentos_mencionados=["BO online", "atestado médico"]),
        "esperado_elegivel": True,
        "esperado_status": "pending_documents",
        "esperado_cobertura": "B_DITA",
    },
    # 2. Recusa por carência (D2) — regime UBER
    {
        "nome": "2. DITA Uber — recusa por carência (D2)",
        "tipo_sinistro": "DITA",
        "plataforma": "UBER",
        "apolice": APOLICE_CARENCIA,
        "historico": HISTORICO_LIMPO,
        "extracao": _ExtracaoStub(tipo_sinistro="DITA"),
        "esperado_elegivel": False,
        "esperado_status": "rejected",
        "esperado_regra": "D2",
    },
    # 3. Moto Uber Produto A — recusa D6 (somente automóvel)
    {
        "nome": "3. IAT moto Uber — recusa D6 (somente automóvel)",
        "tipo_sinistro": "IAT",
        "plataforma": "UBER",
        "apolice": APOLICE_PRODUTO_A,
        "historico": HISTORICO_LIMPO,
        "extracao": _ExtracaoStub(tipo_sinistro="IAT", veiculo=_Veiculo(tipo="MOTO")),
        "esperado_elegivel": False,
        "esperado_status": "rejected",
        "esperado_regra": "D6",
    },
    # 4. IPA Uber — recusa D7 (só DITA válida no bilhete Uber)
    {
        "nome": "4. IPA Uber — recusa D7",
        "tipo_sinistro": "IPA",
        "plataforma": "UBER",
        "apolice": APOLICE_VIGENTE,
        "historico": HISTORICO_LIMPO,
        "extracao": _ExtracaoStub(tipo_sinistro="IPA"),
        "esperado_elegivel": False,
        "esperado_status": "rejected",
        "esperado_regra": "D7",
    },
    # 5. BAGAGEM — elegível, todos os docs mencionados
    {
        "nome": "5. BAGAGEM Uber — aprovado",
        "tipo_sinistro": "BAGAGEM",
        "plataforma": "UBER",
        "apolice": APOLICE_VIGENTE_C,
        "historico": HISTORICO_LIMPO,
        "extracao": _ExtracaoStub(tipo_sinistro="BAGAGEM",
            documentos_mencionados=["BO policial", "declaração prévia", "nota fiscal sefaz",
                                    "comprovante de existência", "cnh ativa", "cpf rg do responsável"]),
        "esperado_elegivel": True,
        "esperado_status": "approved",
        "esperado_cobertura": "C_COB_A",
    },
    # 6. IPA 99Entrega — DEVE SER ELEGÍVEL (CG padrão, sem restrição Uber)
    {
        "nome": "6. IPA 99Entrega — elegível (regime PADRAO, sem restrição D7)",
        "tipo_sinistro": "IPA",
        "plataforma": "NOVENTA_E_NOVE",
        "apolice": APOLICE_VIGENTE,
        "historico": HISTORICO_LIMPO,
        "extracao": _ExtracaoStub(tipo_sinistro="IPA"),
        "esperado_elegivel": True,
        "esperado_status": "pending_documents",
        "esperado_cobertura": "B_IPA",
    },
    # 7. MA iFood — DEVE SER ELEGÍVEL (regime PADRAO)
    {
        "nome": "7. MA iFood — elegível (regime PADRAO)",
        "tipo_sinistro": "MA",
        "plataforma": "IFOOD",
        "apolice": APOLICE_VIGENTE,
        "historico": HISTORICO_LIMPO,
        "extracao": _ExtracaoStub(tipo_sinistro="MA"),
        "esperado_elegivel": True,
        "esperado_status": "pending_documents",
        "esperado_cobertura": "B_MA",
    },
    # 8. IAT moto Rappi — DEVE SER ELEGÍVEL (D6 não se aplica no regime PADRAO)
    {
        "nome": "8. IAT moto Rappi — elegível (D6 não se aplica no regime PADRAO)",
        "tipo_sinistro": "IAT",
        "plataforma": "RAPPI",
        "apolice": APOLICE_PRODUTO_A,
        "historico": HISTORICO_LIMPO,
        "extracao": _ExtracaoStub(tipo_sinistro="IAT", veiculo=_Veiculo(tipo="MOTO")),
        "esperado_elegivel": True,
        "esperado_status": "pending_documents",
        "esperado_cobertura": "A_COB_II",
    },
    # 9. DITA plataforma NAO_MENCIONADA — regime PADRAO, elegível
    {
        "nome": "9. DITA plataforma não mencionada — regime PADRAO, elegível",
        "tipo_sinistro": "DITA",
        "plataforma": "NAO_MENCIONADA",
        "apolice": APOLICE_VIGENTE,
        "historico": HISTORICO_LIMPO,
        "extracao": _ExtracaoStub(tipo_sinistro="DITA",
            documentos_mencionados=["atestado médico", "laudo", "comprovante"]),
        "esperado_elegivel": True,
        "esperado_status": "pending_documents",
        "esperado_cobertura": "B_DITA",
    },
]


# ============================================================
# Runner
# ============================================================

def executar():
    total = len(CASOS)
    passes = 0

    for caso in CASOS:
        print("\n" + "█" * 70)
        print(f"CASO {caso['nome']}")
        print("█" * 70)

        # Adapta o stub para ter .tipo_sinistro como objeto com .value
        extracao = caso["extracao"]
        class _TS:
            def __init__(self, v): self.value = v
        extracao.tipo_sinistro = _TS(caso["tipo_sinistro"])

        veredicto = avaliar_cobertura(
            tipo_sinistro=caso["tipo_sinistro"],
            dados_apolice=caso["apolice"],
            historico_sinistros=caso["historico"],
            extracao=extracao,
            plataforma=caso.get("plataforma", "NAO_MENCIONADA"),
        )

        # Verificações
        ok_elegivel = veredicto.elegivel == caso["esperado_elegivel"]
        ok_status = veredicto.status == caso["esperado_status"]
        ok_cobertura = (
            "esperado_cobertura" not in caso
            or veredicto.cobertura == caso["esperado_cobertura"]
        )
        ok_regra = (
            "esperado_regra" not in caso
            or veredicto.regra_violada == caso["esperado_regra"]
        )

        passou = ok_elegivel and ok_status and ok_cobertura and ok_regra
        status_txt = "✅ PASS" if passou else "❌ FAIL"
        if passou:
            passes += 1

        print(f"\n{status_txt}")
        print(f"  elegível:  esperado={caso['esperado_elegivel']}  real={veredicto.elegivel}  {'✓' if ok_elegivel else '✗'}")
        print(f"  status:    esperado={caso['esperado_status']}  real={veredicto.status}  {'✓' if ok_status else '✗'}")
        if "esperado_cobertura" in caso:
            print(f"  cobertura: esperado={caso['esperado_cobertura']}  real={veredicto.cobertura}  {'✓' if ok_cobertura else '✗'}")
        if "esperado_regra" in caso:
            print(f"  regra:     esperado={caso['esperado_regra']}  real={veredicto.regra_violada}  {'✓' if ok_regra else '✗'}")
        if veredicto.motivo_recusa:
            print(f"  motivo:    {veredicto.motivo_recusa}")
        if veredicto.docs_pendentes:
            print(f"  docs pendentes ({len(veredicto.docs_pendentes)}):")
            for d in veredicto.docs_pendentes[:4]:
                print(f"    • {d}")
        print(f"  regras verificadas: {veredicto.regras_verificadas}")

    print("\n" + "=" * 70)
    print(f"RESULTADO FINAL: {passes}/{total} PASS")
    print("=" * 70)
    return passes == total


if __name__ == "__main__":
    import sys
    ok = executar()
    sys.exit(0 if ok else 1)
