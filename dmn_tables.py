"""
dmn_tables.py — Tabelas de decisão (inspirado em DMN) para regras 88i (Semana 3)

Estrutura: cada tabela é um dict/list Python auditável — sem XML, sem biblioteca externa.
Facilita auditoria SUSEP e permite exportação futura para BPMN/DMN se necessário.

Fonte: Condições Gerais 88i março/2026 + skill olga-analista-seguros-88i.
NÃO alterar sem atualizar as referências na skill e nos testes.

Convenções:
  - produto: "A" | "B" | "C" | "TODOS"
  - tipo_sinistro (BAML): DITA | IPA | MA | DMHO | MAC | IAT | AF | BAGAGEM | INDEFINIDO
  - cobertura (interno): "A_COB_I" | "A_COB_II" | "B_DITA" | "C_COB_A" | "C_COB_B"
  - plataforma: "UBER" | "OUTRA" | None
"""

from __future__ import annotations


# ============================================================
# Tabela 1: mapeamento tipo_sinistro → cobertura 88i
# ============================================================
# Dado o tipo extraído pelo BAML + plataforma, qual cobertura se aplica?
# Retorna lista porque um tipo pode mapear para múltiplas coberturas.

TIPO_SINISTRO_COBERTURA: list[dict] = [
    # Produto A — Impedimento ao Trabalho
    {
        "tipo_sinistro": "DITA",
        "plataforma": "UBER",
        "produto": "B",
        "cobertura": "B_DITA",
        "descricao": "Diária por Incapacidade Temporária por Acidente — única cobertura AP Uber",
    },
    {
        "tipo_sinistro": "IAT",
        "plataforma": "UBER",
        "produto": "A",
        "cobertura": "A_COB_II",
        "descricao": "Colisão do Veículo de Trabalho — impedimento ao trabalho Uber",
        "restricao": "somente_automovel",
    },
    {
        "tipo_sinistro": "IAT",
        "plataforma": "UBER",
        "produto": "A",
        "cobertura": "A_COB_I",
        "descricao": "Roubo/Furto do Veículo de Trabalho — impedimento ao trabalho Uber",
        "restricao": "somente_automovel",
    },
    # Produto B — Acidentes Pessoais (Uber: somente DITA)
    {
        "tipo_sinistro": "IPA",
        "plataforma": "UBER",
        "produto": "B",
        "cobertura": None,
        "descricao": "IPA NÃO se aplica ao bilhete Uber (Cond. Particulares 1.1)",
        "elegivel": False,
        "motivo_recusa": "D7: IPA não cobre bilhete Uber — somente DITA é válida",
    },
    {
        "tipo_sinistro": "MA",
        "plataforma": "UBER",
        "produto": "B",
        "cobertura": None,
        "descricao": "MA NÃO se aplica ao bilhete Uber",
        "elegivel": False,
        "motivo_recusa": "D7: MA não cobre bilhete Uber — somente DITA é válida",
    },
    {
        "tipo_sinistro": "DMHO",
        "plataforma": "UBER",
        "produto": "B",
        "cobertura": None,
        "descricao": "DMHO NÃO se aplica ao bilhete Uber",
        "elegivel": False,
        "motivo_recusa": "D7: DMHO não cobre bilhete Uber — somente DITA é válida",
    },
    # Produto C — Bagagens/Encomendas
    {
        "tipo_sinistro": "BAGAGEM",
        "plataforma": "UBER",
        "produto": "C",
        "cobertura": "C_COB_A",
        "descricao": "Roubo/Furto de Encomenda — Uber Envios",
    },
    {
        "tipo_sinistro": "BAGAGEM",
        "plataforma": "UBER",
        "produto": "C",
        "cobertura": "C_COB_B",
        "descricao": "Danos Materiais à Encomenda — Uber Envios",
    },
]


# ============================================================
# Tabela 2: documentos obrigatórios por cobertura
# ============================================================
# "kit_basico" é comum a todos — listado separadamente para não repetir.

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
        "Comprovante de dias desconectado da plataforma (app Uber)",
        "BO (se houver) e peças do inquérito",
    ],
    "A_COB_I": [
        "BO (original ou autenticado) com local, descrição, bem sinistrado, data e hora",
        "CRLV do veículo",
        "Comprovante de retorno ao trabalho",
        # Certidão de Não Localização NÃO se aplica à Uber
    ],
    "A_COB_II": [
        "BRAT (Boletim de Registro de Acidente de Trânsito)",
        "Fotos dos danos ao veículo",
        "Laudo de vistoria de oficina com prazo de conserto",
        "Relatório da oficina com reparos realizados e datas",
        "Fotos dos reparos",
        # CRLV e comprovante de retorno NÃO se aplicam à Uber
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
# Tabela 3: regras D1-D15 com metadados para auditoria
# ============================================================

REGRAS_D: list[dict] = [
    {
        "codigo": "D1",
        "descricao": "Apólice/bilhete vigente na data do fato",
        "produto": "TODOS",
        "consequencia_falha": "rejected",
        "campo_verificado": "dados_apolice.vigente_hoje",
    },
    {
        "codigo": "D2",
        "descricao": "Evento fora do período de carência",
        "produto": "TODOS",
        "consequencia_falha": "rejected",
        "campo_verificado": "dados_apolice.carencia_ativa",
    },
    {
        "codigo": "D3",
        "descricao": "Evento durante período de trabalho / com seguro ativado",
        "produto": "A_C",
        "consequencia_falha": "pending_documents",
        "campo_verificado": "extracao.documentos_mencionados",
    },
    {
        "codigo": "D4",
        "descricao": "Cooldown respeitado: 90d (Prod.A), 30d (Prod.B/Uber) após mesmo evento",
        "produto": "A_B",
        "consequencia_falha": "rejected",
        "campo_verificado": "historico_sinistros.ultimo_sinistro_data",
    },
    {
        "codigo": "D6",
        "descricao": "Tipo de veículo válido: SOMENTE automóvel para Prod.A/Uber",
        "produto": "A",
        "consequencia_falha": "rejected",
        "campo_verificado": "extracao.veiculo.tipo",
    },
    {
        "codigo": "D7",
        "descricao": "Coberturas III e IV NÃO se aplicam ao bilhete Uber",
        "produto": "A",
        "plataforma": "UBER",
        "consequencia_falha": "rejected",
        "campo_verificado": "tipo_sinistro_mapeado",
    },
    {
        "codigo": "D8",
        "descricao": "Evento enquadra em risco coberto",
        "produto": "TODOS",
        "consequencia_falha": "rejected",
        "campo_verificado": "cobertura_aplicavel",
    },
    {
        "codigo": "D11",
        "descricao": "NF NÃO é de parente do segurado",
        "produto": "C",
        "consequencia_falha": "rejected",
        "campo_verificado": "extracao.red_flags",
    },
    {
        "codigo": "D12",
        "descricao": "Encomenda constava em declaração prévia",
        "produto": "C",
        "consequencia_falha": "rejected",
        "campo_verificado": "extracao.documentos_mencionados",
    },
    {
        "codigo": "D14",
        "descricao": "Tratamento médico iniciado em até 30 dias do acidente",
        "produto": "B",
        "consequencia_falha": "rejected",
        "campo_verificado": "extracao.data_ocorrencia",
    },
    {
        "codigo": "D15",
        "descricao": "Condutor com CNH ativa no momento do sinistro",
        "produto": "A_B",
        "consequencia_falha": "rejected",
        "campo_verificado": "extracao.documentos_mencionados",
    },
]


# ============================================================
# Tabela 4: valores máximos e cooldowns por cobertura
# ============================================================
# Valores são placeholders — em produção viriam do bilhete/apólice no Supabase.

PARAMETROS_COBERTURA: dict[str, dict] = {
    "B_DITA": {
        "valor_diaria_placeholder": "baseado na classificação do motorista no Uber",
        "cooldown_dias": 30,
        "franquia": "definida no bilhete",
        "carencia_dias": 0,  # zero carência para acidentes pessoais
        "limite_dias_afastamento": "menor entre laudo e dias offline no app",
    },
    "A_COB_I": {
        "valor_diaria_placeholder": "renda média dos últimos 28 dias no Uber",
        "cooldown_dias": 90,
        "franquia": "data do roubo",
        "carencia_dias": None,  # verificar bilhete
        "limite_dias_afastamento": "menor entre dias reais e dias sem corridas",
    },
    "A_COB_II": {
        "valor_diaria_placeholder": "renda média dos últimos 28 dias no Uber",
        "cooldown_dias": 90,
        "franquia": "data de análise por mecânico",
        "carencia_dias": None,
        "limite_dias_afastamento": "menor entre dias reais e dias sem corridas",
        "restricao_veiculo": "somente_automovel",
    },
    "C_COB_A": {
        "valor_maximo": "menor entre NF e LMI do bilhete (sem NF: R$ 300,00)",
        "cooldown_dias": None,
        "franquia": "definida no bilhete",
    },
    "C_COB_B": {
        "valor_maximo": "menor entre NF e LMI do bilhete",
        "cooldown_dias": None,
        "franquia": "definida no bilhete",
    },
}
