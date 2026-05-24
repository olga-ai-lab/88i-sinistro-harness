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
    # ----------------------------------------------------------
    # 1. DITA Uber válido — elegível, mas com docs pendentes
    # ----------------------------------------------------------
    {
        "nome": "1. DITA Uber — elegível com docs pendentes",
        "tipo_sinistro": "DITA",
        "apolice": APOLICE_VIGENTE,
        "historico": HISTORICO_LIMPO,
        "extracao": _ExtracaoStub(
            tipo_sinistro="DITA",
            documentos_mencionados=["BO online", "atestado médico"],
            # não mencionou: laudo médico, comprovante app Uber
        ),
        "esperado_elegivel": True,
        "esperado_status": "pending_documents",
        "esperado_cobertura": "B_DITA",
    },

    # ----------------------------------------------------------
    # 2. Recusa por carência (D2)
    # ----------------------------------------------------------
    {
        "nome": "2. DITA Uber — recusa por carência (D2)",
        "tipo_sinistro": "DITA",
        "apolice": APOLICE_CARENCIA,
        "historico": HISTORICO_LIMPO,
        "extracao": _ExtracaoStub(tipo_sinistro="DITA"),
        "esperado_elegivel": False,
        "esperado_status": "rejected",
        "esperado_regra": "D2",
    },

    # ----------------------------------------------------------
    # 3. Produto A / moto → recusa D6 (somente automóvel)
    # ----------------------------------------------------------
    {
        "nome": "3. IAT moto Uber — recusa D6 (somente automóvel)",
        "tipo_sinistro": "IAT",
        "apolice": APOLICE_PRODUTO_A,
        "historico": HISTORICO_LIMPO,
        "extracao": _ExtracaoStub(
            tipo_sinistro="IAT",
            veiculo=_Veiculo(tipo="MOTO"),
        ),
        "esperado_elegivel": False,
        "esperado_status": "rejected",
        "esperado_regra": "D6",
    },

    # ----------------------------------------------------------
    # 4. IPA Uber → recusa D7 (só DITA válida no bilhete Uber)
    # ----------------------------------------------------------
    {
        "nome": "4. IPA Uber — recusa D7 (cobertura não disponível no bilhete Uber)",
        "tipo_sinistro": "IPA",
        "apolice": APOLICE_VIGENTE,
        "historico": HISTORICO_LIMPO,
        "extracao": _ExtracaoStub(tipo_sinistro="IPA"),
        "esperado_elegivel": False,
        "esperado_status": "rejected",
        "esperado_regra": "D7",
    },

    # ----------------------------------------------------------
    # 5. BAGAGEM com docs mencionados → aprovado sem pendências
    # ----------------------------------------------------------
    {
        "nome": "5. BAGAGEM Uber Envios — elegível, todos os docs mencionados",
        "tipo_sinistro": "BAGAGEM",
        "apolice": APOLICE_VIGENTE_C,
        "historico": HISTORICO_LIMPO,
        "extracao": _ExtracaoStub(
            tipo_sinistro="BAGAGEM",
            documentos_mencionados=[
                "BO policial",
                "declaração prévia",
                "nota fiscal sefaz",
                "comprovante de existência",
                "cnh ativa",
                "cpf rg do responsável",
            ],
        ),
        "esperado_elegivel": True,
        "esperado_status": "approved",
        "esperado_cobertura": "C_COB_A",
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
        # Rules engine chama hasattr(ts, "value") — o stub usa string direta
        # Patch: criar objeto com .value
        class _TS:
            def __init__(self, v): self.value = v
        extracao.tipo_sinistro = _TS(caso["tipo_sinistro"])

        veredicto = avaliar_cobertura(
            tipo_sinistro=caso["tipo_sinistro"],
            dados_apolice=caso["apolice"],
            historico_sinistros=caso["historico"],
            extracao=extracao,
            plataforma="UBER",
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
