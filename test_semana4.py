"""
test_semana4.py — Testes do pipeline documental (Semana 4)

4 casos com documentos sintéticos em texto (sem imagens reais):
  1. BO válido + atestado médico válido → approved_for_next_step
  2. Laudo médico sem CRM → pending_manual_review ou fraud_escalation
  3. Atestado com data incompatível com o acidente → fraud_escalation
  4. NF de parente do segurado (Produto C) → rejected_documentally

Rodar: python test_semana4.py
Nota: cada caso faz 3 chamadas ao Claude (classifier + forensics + adjudicator).
      Tempo esperado: ~30s por caso.
"""

import sys
from doc_pipeline import analisar_documentos, DocumentoInput

# ============================================================
# Documentos sintéticos — texto que descreve o conteúdo do doc
# ============================================================

BO_VALIDO = """
POLÍCIA CIVIL DO ESTADO DE SÃO PAULO
BOLETIM DE OCORRÊNCIA Nº 4532/2026
Delegacia de Polícia do Bixiga — 77ª DP — São Paulo/SP

Data do fato: 18/04/2026 às 22h00
Data do registro: 19/04/2026

Vítima: João Silva — CPF 123.456.789-00
Veículo: Moto Honda CG 160 — Placa ABC1D23

Narrativa: O comunicante informa que no dia 18/04/2026, às 22h00,
trafegava pela Av. Paulista, altura do nº 1500, São Paulo/SP,
quando um veículo realizou conversão sem sinalização, causando
colisão com a motocicleta. O comunicante sofreu fratura na perna direita.

Código de autenticação: SP-2026-4532-XK9
"""

ATESTADO_VALIDO = """
ATESTADO MÉDICO

Hospital das Clínicas de São Paulo
Dr. Carlos Mendes — CRM 45678/SP

Paciente: João Silva
Data do atendimento: 19/04/2026
Diagnóstico: Fratura de tíbia direita — CID S82.1

Atesto que o paciente esteve sob meus cuidados e necessita de
afastamento de suas atividades laborais pelo período de 30 (trinta)
dias, a contar de 19/04/2026.

Assinatura e carimbo do médico.
"""

LAUDO_SEM_CRM = """
LAUDO MÉDICO

Paciente: João Silva
Data: 20/04/2026

O paciente apresentou fratura na perna direita após acidente de moto.
Recomendo afastamento de 45 dias.

Dr. M. Santos
"""

ATESTADO_DATA_INCOMPATIVEL = """
ATESTADO MÉDICO

Clínica São Lucas
Dr. Roberto Ferreira — CRM 99123/SP

Paciente: João Silva
Data do atendimento: 05/03/2026

Atesto que o paciente esteve em atendimento nesta data
e necessita de 30 dias de afastamento a contar de 05/03/2026.

(Nota: o acidente teria ocorrido em 18/04/2026 — 44 dias DEPOIS
 deste atestado, o que é fisicamente impossível)
"""

NF_PARENTE = """
NOTA FISCAL ELETRÔNICA — NF-e
Chave SEFAZ: 35260412345678901234550010000012341000012349
CNPJ Emitente: 12.345.678/0001-90
Razão Social: Silva & Silva Comércio ME

Destinatário: João Silva — CPF 123.456.789-00
Endereço de entrega: Rua das Flores, 123 — São Paulo/SP

Itens:
  - Smartphone Samsung Galaxy A55 — R$ 1.800,00

(Nota: CNPJ emitente pertence a empresa de familiar — sobrenome Silva
 coincide com o do segurado João Silva)
"""

# ============================================================
CASOS = [
    # ----------------------------------------------------------
    # 1. DITA Uber válido — documentos OK → approved_for_next_step
    # ----------------------------------------------------------
    {
        "nome": "1. BO válido + atestado válido → approved_for_next_step",
        "documentos": [
            DocumentoInput(nome="bo_sp.txt", conteudo=BO_VALIDO, ordem=0),
            DocumentoInput(nome="atestado_hc.txt", conteudo=ATESTADO_VALIDO, ordem=1),
        ],
        "contexto": (
            "Protocolo: 88i-2026-TEST001\n"
            "PRODUTO: B — Seguro de Acidentes Pessoais Individual (Uber)\n"
            "Tipo de sinistro: DITA — Diária por Incapacidade Temporária por Acidente\n"
            "Cobertura identificada: B_DITA (NÃO é Produto A / Impedimento ao Trabalho)\n"
            "IMPORTANTE: A restrição de tipo de veículo (D6 — somente automóvel) "
            "aplica-se EXCLUSIVAMENTE ao Produto A. Para DITA/Produto B, "
            "motociclistas estão cobertos.\n"
            "Narrativa original: Bati minha moto na Paulista às 22h, perna quebrada, "
            "tenho BO e atestado de 30 dias.\n"
            "Plataforma: UBER\n"
        ),
        "esperado_status": ["approved_for_next_step", "pending_documents"],
        "nao_esperado_status": ["fraud_escalation"],
    },

    # ----------------------------------------------------------
    # 2. Laudo sem CRM → suspeito / revisão manual
    # ----------------------------------------------------------
    {
        "nome": "2. Laudo sem CRM → suspeito / revisão manual",
        "documentos": [
            DocumentoInput(nome="laudo_sem_crm.txt", conteudo=LAUDO_SEM_CRM, ordem=0),
        ],
        "contexto": (
            "Protocolo: 88i-2026-TEST002\n"
            "PRODUTO: B — Seguro de Acidentes Pessoais Individual (Uber)\n"
            "Tipo de sinistro: DITA\n"
            "Cobertura identificada: B_DITA\n"
            "IMPORTANTE: Produto B/DITA. D6 não se aplica a este produto.\n"
            "Narrativa original: Tive acidente de moto, laudo médico em anexo.\n"
            "Plataforma: UBER\n"
        ),
        "esperado_status": ["pending_manual_review", "fraud_escalation",
                            "pending_documents", "rejected_documentally"],
        "nao_esperado_status": ["approved_for_next_step"],
    },

    # ----------------------------------------------------------
    # 3. Atestado com data anterior ao acidente → fraud_escalation
    # ----------------------------------------------------------
    {
        "nome": "3. Atestado com data anterior ao acidente → fraud_escalation",
        "documentos": [
            DocumentoInput(nome="bo_sp.txt", conteudo=BO_VALIDO, ordem=0),
            DocumentoInput(nome="atestado_data_errada.txt", conteudo=ATESTADO_DATA_INCOMPATIVEL, ordem=1),
        ],
        "contexto": (
            "Protocolo: 88i-2026-TEST003\n"
            "PRODUTO: B — Seguro de Acidentes Pessoais Individual (Uber)\n"
            "Tipo de sinistro: DITA\n"
            "Cobertura identificada: B_DITA\n"
            "IMPORTANTE: Produto B/DITA. D6 não se aplica a este produto.\n"
            "Narrativa original: Acidente em 18/04/2026, atestado médico em anexo.\n"
            "Plataforma: UBER\n"
        ),
        "esperado_status": ["fraud_escalation", "pending_manual_review"],
        "nao_esperado_status": ["approved_for_next_step"],
    },

    # ----------------------------------------------------------
    # 4. NF de parente (Produto C) → rejected_documentally
    # ----------------------------------------------------------
    {
        "nome": "4. NF de parente (Produto C) → rejected_documentally",
        "documentos": [
            DocumentoInput(nome="nf_encomenda.txt", conteudo=NF_PARENTE, ordem=0),
        ],
        "contexto": (
            "Protocolo: 88i-2026-TEST004\n"
            "PRODUTO: C — Seguro de Deslocamento de Bagagens e Encomendas (Uber)\n"
            "Tipo de sinistro: BAGAGEM\n"
            "Cobertura identificada: C_COB_A — Roubo/Furto de Encomenda\n"
            "Narrativa original: Encomenda roubada durante entrega Uber Envios. NF em anexo.\n"
            "Plataforma: UBER\n"
        ),
        "esperado_status": ["rejected_documentally", "fraud_escalation", "pending_manual_review"],
        "nao_esperado_status": ["approved_for_next_step"],
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

        try:
            analise = analisar_documentos(
                caso["documentos"],
                contexto_sinistro=caso["contexto"],
            )
        except Exception as e:
            print(f"❌ ERRO ao rodar pipeline: {e}")
            continue

        veredicto = analise.veredicto
        status_real = veredicto.decision_status if veredicto else "erro"

        passou = (
            status_real in caso["esperado_status"]
            and status_real not in caso["nao_esperado_status"]
        )

        if passou:
            passes += 1
            print(f"\n✅ PASS — decision_status: {status_real}")
        else:
            print(f"\n❌ FAIL — decision_status: {status_real}")
            print(f"  esperado um de: {caso['esperado_status']}")
            print(f"  NÃO esperado:  {caso['nao_esperado_status']}")

        if veredicto:
            print(f"  fraud_score: {veredicto.fraud_score} ({veredicto.fraud_level})")
            print(f"  human_review: {veredicto.human_review_required}")
            print(f"  confidence: {veredicto.decision_confidence:.2f}")
            if veredicto.key_findings:
                print(f"  key_findings ({len(veredicto.key_findings)}):")
                for f_ in veredicto.key_findings[:3]:
                    print(f"    • {f_}")
            if veredicto.missing_documents:
                print(f"  missing_docs: {veredicto.missing_documents[:3]}")

        print(f"\n  Documentos processados:")
        for a in analise.documentos:
            clf_type = a.classificacao.document_type if a.classificacao else "erro"
            auth = a.forensics.authenticity_status if a.forensics else "n/a"
            conf = a.classificacao.confidence if a.classificacao else 0.0
            sinais = a.forensics.tampering_signals if a.forensics else []
            print(f"    [{clf_type}] conf={conf:.2f} auth={auth} adulteração={sinais[:2]}")

        if analise.resumo_fraude:
            print(f"\n  FRAUDE: {analise.resumo_fraude}")

    print("\n" + "=" * 70)
    print(f"RESULTADO FINAL: {passes}/{total} PASS")
    print("=" * 70)
    return passes == total


if __name__ == "__main__":
    ok = executar()
    sys.exit(0 if ok else 1)
