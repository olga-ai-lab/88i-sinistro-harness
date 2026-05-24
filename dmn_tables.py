"""
dmn_tables.py — Tabelas de decisão (inspirado em DMN) para regras 88i (Semana 3)

Semana 4.5: refatorado para suporte multi-plataforma.
  - regime "UBER": Condições Particulares Uber (restrições específicas)
  - regime "PADRAO": CG geral (99, iFood, Rappi, Loggi, Lalamove, NAO_MENCIONADA)

Fonte: CGs 88i março/2026 + CG AP 01/02/2024 + skill olga-analista-seguros-88i.
"""

from __future__ import annotations

# Plataformas que usam CG padrão (sem CP Uber)
PLATAFORMAS_PADRAO = {
    "NOVENTA_E_NOVE", "IFOOD", "RAPPI", "LOGGI",
    "LALAMOVE", "OUTRA_PLATAFORMA", "NAO_MENCIONADA",
}

PLATAFORMAS_UBER = {"UBER"}


def resolver_regime(plataforma: str) -> str:
    """Retorna 'UBER' se plataforma com CP Uber, 'PADRAO' caso contrário."""
    if plataforma and plataforma.upper() in PLATAFORMAS_UBER:
        return "UBER"
    return "PADRAO"


# ============================================================
# Tabela 1: tipo_sinistro + regime → cobertura
# ============================================================

TIPO_SINISTRO_COBERTURA: list[dict] = [

    # --- REGIME UBER (Condições Particulares Uber) ---

    {"tipo_sinistro": "DITA",    "regime": "UBER", "produto": "B", "cobertura": "B_DITA",
     "descricao": "DITA — única cobertura AP válida no bilhete Uber"},
    {"tipo_sinistro": "IAT",     "regime": "UBER", "produto": "A", "cobertura": "A_COB_II",
     "descricao": "Colisão do Veículo — Impedimento ao Trabalho Uber", "restricao": "somente_automovel"},
    {"tipo_sinistro": "IAT",     "regime": "UBER", "produto": "A", "cobertura": "A_COB_I",
     "descricao": "Roubo/Furto do Veículo — Impedimento ao Trabalho Uber", "restricao": "somente_automovel"},
    {"tipo_sinistro": "BAGAGEM", "regime": "UBER", "produto": "C", "cobertura": "C_COB_A",
     "descricao": "Roubo/Furto de Encomenda — Uber Envios"},
    {"tipo_sinistro": "BAGAGEM", "regime": "UBER", "produto": "C", "cobertura": "C_COB_B",
     "descricao": "Danos Materiais à Encomenda — Uber Envios"},
    # Coberturas explicitamente bloqueadas no bilhete Uber
    {"tipo_sinistro": "IPA",  "regime": "UBER", "produto": "B", "cobertura": None,
     "elegivel": False, "motivo_recusa": "D7: IPA não cobre bilhete Uber — somente DITA é válida"},
    {"tipo_sinistro": "MA",   "regime": "UBER", "produto": "B", "cobertura": None,
     "elegivel": False, "motivo_recusa": "D7: MA não cobre bilhete Uber — somente DITA é válida"},
    {"tipo_sinistro": "DMHO", "regime": "UBER", "produto": "B", "cobertura": None,
     "elegivel": False, "motivo_recusa": "D7: DMHO não cobre bilhete Uber — somente DITA é válida"},
    {"tipo_sinistro": "MAC",  "regime": "UBER", "produto": "B", "cobertura": None,
     "elegivel": False, "motivo_recusa": "D7: MAC não cobre bilhete Uber — somente DITA é válida"},
    {"tipo_sinistro": "AF",   "regime": "UBER", "produto": "B", "cobertura": None,
     "elegivel": False, "motivo_recusa": "D7: AF não cobre bilhete Uber — somente DITA é válida"},

    # --- REGIME PADRAO (CG geral — 99, iFood, Rappi, Loggi, etc.) ---

    {"tipo_sinistro": "DITA",    "regime": "PADRAO", "produto": "B", "cobertura": "B_DITA",
     "descricao": "DITA — Diária por Incapacidade Temporária por Acidente"},
    {"tipo_sinistro": "IPA",     "regime": "PADRAO", "produto": "B", "cobertura": "B_IPA",
     "descricao": "IPA — Invalidez Permanente Total ou Parcial por Acidente"},
    {"tipo_sinistro": "MA",      "regime": "PADRAO", "produto": "B", "cobertura": "B_MA",
     "descricao": "MA — Morte Acidental"},
    {"tipo_sinistro": "DMHO",    "regime": "PADRAO", "produto": "B", "cobertura": "B_DMHO",
     "descricao": "DMHO — Despesas Médico-Hospitalares e Odontológicas"},
    {"tipo_sinistro": "MAC",     "regime": "PADRAO", "produto": "B", "cobertura": "B_MAC",
     "descricao": "MAC — Morte Acidental por Crime"},
    {"tipo_sinistro": "AF",      "regime": "PADRAO", "produto": "B", "cobertura": "B_AF",
     "descricao": "AF — Auxílio Funeral por Acidente"},
    {"tipo_sinistro": "IAT",     "regime": "PADRAO", "produto": "A", "cobertura": "A_COB_II",
     "descricao": "Colisão do Veículo — Impedimento ao Trabalho (CG padrão)"},
    {"tipo_sinistro": "IAT",     "regime": "PADRAO", "produto": "A", "cobertura": "A_COB_I",
     "descricao": "Roubo/Furto do Veículo — Impedimento ao Trabalho (CG padrão)"},
    {"tipo_sinistro": "BAGAGEM", "regime": "PADRAO", "produto": "C", "cobertura": "C_COB_A",
     "descricao": "Roubo/Furto de Encomenda — Last Mile Delivery"},
    {"tipo_sinistro": "BAGAGEM", "regime": "PADRAO", "produto": "C", "cobertura": "C_COB_B",
     "descricao": "Danos Materiais à Encomenda — Last Mile Delivery"},
]


# ============================================================
# Tabela 2: documentos obrigatórios por cobertura
# ============================================================

KIT_BASICO = [
    "RG (cópia)",
    "CPF (cópia)",
    "CNH ativa (cópia)",
    "Comprovante de residência (máx. 90 dias)",
    "Aviso de Sinistro preenchido",
]

DOCS_POR_COBERTURA: dict[str, list[str]] = {
    "B_DITA": [
        "Laudo médico com CRM e período de afastamento",
        "Atestado médico",
        "Receituário médico",
        "Relatório do médico assistente com diagnóstico e CID",
        "Comprovante de dias desconectado da plataforma (app)",
        "BO (se houver) e peças do inquérito",
    ],
    "B_IPA": [
        "Laudo de invalidez com CRM",
        "Relatório médico com descrição das sequelas permanentes",
        "BO ou BRAT (se acidente de trânsito)",
        "Exames de imagem (raio-x, ressonância) confirmando a lesão",
    ],
    "B_MA": [
        "Certidão de óbito",
        "Laudo necroscópico ou relatório do IML",
        "BO (quando aplicável)",
        "Documentos do beneficiário (RG, CPF, comprovante de vínculo)",
    ],
    "B_DMHO": [
        "Notas fiscais/recibos das despesas médicas",
        "Relatório médico justificando os procedimentos",
        "Laudos e exames realizados",
        "BO ou BRAT (se acidente de trânsito)",
    ],
    "B_MAC": [
        "Certidão de óbito",
        "Boletim de Ocorrência com descrição do crime",
        "Laudo necroscópico ou relatório do IML",
        "Documentos do beneficiário",
    ],
    "B_AF": [
        "Certidão de óbito",
        "Notas fiscais do serviço funerário",
        "Documentos do beneficiário",
    ],
    "A_COB_I": [
        "BO (original ou autenticado) com local, descrição, bem sinistrado, data e hora",
        "CRLV do veículo",
        "Comprovante de retorno ao trabalho",
    ],
    "A_COB_II": [
        "BRAT (Boletim de Registro de Acidente de Trânsito)",
        "Fotos dos danos ao veículo",
        "Laudo de vistoria de oficina com prazo de conserto",
        "Relatório da oficina com reparos realizados e datas",
        "Fotos dos reparos",
    ],
    "C_COB_A": [
        "BO (original ou autenticado) com descrição da encomenda",
        "Declaração prévia do bem (tipo, características, valor)",
        "Comprovante de existência da encomenda no início do deslocamento",
        "Nota Fiscal com chave SEFAZ (NF de parentes NÃO é aceita)",
        "CNH ativa do entregador",
        "Nome completo, CPF e RG do responsável pela entrega",
    ],
    "C_COB_B": [
        "Declaração prévia do bem",
        "Comprovante de existência da encomenda no início do deslocamento",
        "Nota Fiscal com chave SEFAZ",
        "Orçamento e laudo técnico com causa e consequências",
        "Fotos dos itens danificados",
        "CNH ativa do entregador",
        "Nome completo, CPF e RG do responsável pela entrega",
    ],
}


# ============================================================
# Tabela 3: regras D com metadados de auditoria
# ============================================================

REGRAS_D: list[dict] = [
    {"codigo": "D1",  "descricao": "Apólice vigente na data do fato",                        "produto": "TODOS", "consequencia_falha": "rejected"},
    {"codigo": "D2",  "descricao": "Evento fora do período de carência",                     "produto": "TODOS", "consequencia_falha": "rejected"},
    {"codigo": "D4",  "descricao": "Cooldown respeitado (90d padrão, 30d DITA/Uber)",        "produto": "A_B",   "consequencia_falha": "rejected"},
    {"codigo": "D6",  "descricao": "Somente automóvel para Prod.A/Uber (não se aplica no regime PADRAO)", "produto": "A", "regime": "UBER", "consequencia_falha": "rejected"},
    {"codigo": "D7",  "descricao": "Coberturas restritas NÃO cobrem bilhete Uber",           "produto": "B",     "regime": "UBER",   "consequencia_falha": "rejected"},
    {"codigo": "D8",  "descricao": "Evento enquadra em risco coberto",                       "produto": "TODOS", "consequencia_falha": "rejected"},
    {"codigo": "D11", "descricao": "NF NÃO é de parente do segurado",                        "produto": "C",     "consequencia_falha": "rejected"},
    {"codigo": "D12", "descricao": "Encomenda constava em declaração prévia",                "produto": "C",     "consequencia_falha": "rejected"},
    {"codigo": "D14", "descricao": "Tratamento médico iniciado em até 30 dias do acidente",  "produto": "B",     "consequencia_falha": "rejected"},
    {"codigo": "D15", "descricao": "Condutor com CNH ativa no momento do sinistro",          "produto": "A_B",   "consequencia_falha": "rejected"},
]


# ============================================================
# Tabela 4: parâmetros por cobertura
# ============================================================

PARAMETROS_COBERTURA: dict[str, dict] = {
    "B_DITA": {
        "valor_diaria_placeholder": "baseado na classificação do motorista na plataforma",
        "cooldown_dias": 30,          # Uber: 30 dias (CP Uber)
        "cooldown_dias_padrao": 90,   # CG geral: 90 dias
        "franquia": "definida no bilhete",
        "carencia_dias": 0,
        "limite_dias_afastamento": "menor entre laudo e dias offline no app",
    },
    "B_IPA":  {"cooldown_dias": None, "carencia_dias": 0},
    "B_MA":   {"cooldown_dias": None, "carencia_dias": 0},
    "B_DMHO": {"cooldown_dias": None, "carencia_dias": 0},
    "B_MAC":  {"cooldown_dias": None, "carencia_dias": 0},
    "B_AF":   {"cooldown_dias": None, "carencia_dias": 0},
    "A_COB_I":  {
        "valor_diaria_placeholder": "renda média dos últimos 28 dias na plataforma",
        "cooldown_dias": 90,
        "franquia": "data do roubo",
        "restricao_veiculo_uber": "somente_automovel",
    },
    "A_COB_II": {
        "valor_diaria_placeholder": "renda média dos últimos 28 dias na plataforma",
        "cooldown_dias": 90,
        "franquia": "data de análise por mecânico",
        "restricao_veiculo_uber": "somente_automovel",
    },
    "C_COB_A": {"valor_maximo": "menor entre NF e LMI do bilhete (sem NF: R$ 300,00)", "cooldown_dias": None},
    "C_COB_B": {"valor_maximo": "menor entre NF e LMI do bilhete", "cooldown_dias": None},
}
