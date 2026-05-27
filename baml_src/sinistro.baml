// ============================================================
// 88i Seguradora Digital - Extração de Sinistro
// Semana 1: BAML schema + prompt de ingestão
// Semana 4.5: adicionado Plataforma para suporte multi-cliente
// ============================================================

// --- Enums ---

enum TipoSinistro {
  MA         @description("Morte Acidental")
  IPA        @description("Invalidez Permanente por Acidente")
  DITA       @description("Diária por Incapacidade Temporária por Acidente")
  DMHO       @description("Despesas Médico-Hospitalares")
  MAC        @description("Morte por Qualquer Causa")
  IAT        @description("Impedimento ao Trabalho")
  AF         @description("Auxílio Funeral")
  BAGAGEM    @description("Bagagens e Encomendas (delivery/Last Mile)")
  INDEFINIDO @description("Não foi possível identificar com confiança")
}

enum Urgencia {
  BAIXA   @description("Sem vítimas, sem urgência temporal")
  MEDIA   @description("Há feridos leves ou prazo de 48h")
  ALTA    @description("Feridos graves, urgência operacional")
  CRITICA @description("Vítimas fatais ou risco iminente")
}

enum TipoVeiculo {
  MOTO
  CARRO
  BIKE
  CAMINHAO
  NAO_MENCIONADO
}

enum Plataforma {
  UBER             @description("Uber / Uber Eats / Uber Flash / Uber Envios")
  NOVENTA_E_NOVE   @description("99 / 99Entrega / 99Pop")
  IFOOD            @description("iFood / iFood Entregadores")
  RAPPI            @description("Rappi")
  LOGGI            @description("Loggi")
  LALAMOVE         @description("Lalamove")
  OUTRA_PLATAFORMA @description("Outra plataforma de mobilidade/delivery mencionada")
  NAO_MENCIONADA   @description("Plataforma não identificada na narrativa")
}

// --- Classes aninhadas ---

class Veiculo {
  placa           string?     @description("formato AAA0A00 se mencionada")
  tipo            TipoVeiculo
  descricao_livre string?     @description("marca/modelo/cor se citado")
}

class PessoaEnvolvida {
  papel     "segurado" | "terceiro" | "testemunha" | "vitima" | "desconhecido"
  descricao string?  @description("texto curto identificando a pessoa")
  ferido    bool
}

class CampoFaltante {
  campo         string @description("nome do campo ausente")
  criticidade   "bloqueante" | "importante" | "opcional"
  justificativa string @description("por que esse campo é necessário")
}

class RedFlag {
  tipo       "timing" | "contradicao" | "detalhe_suspeito" | "historico" | "outro"
  descricao  string
  severidade "baixa" | "media" | "alta"
}

// --- Classe principal de saída ---

class ExtracaoSinistro {
  // Classificação
  tipo_sinistro         TipoSinistro
  urgencia              Urgencia
  plataforma_mencionada Plataforma @description("plataforma de mobilidade/delivery citada na narrativa. Use NAO_MENCIONADA se não houver referência explícita.")

  // Temporal e geográfico
  data_ocorrencia  string? @description("ISO 8601 YYYY-MM-DD se mencionada; null caso contrário. Nunca inventar.")
  hora_aproximada  string? @description("HH:MM se mencionada")
  local_ocorrencia string? @description("cidade, rua, ou descrição textual")

  // Narrativa
  descricao_evento string @description("resumo objetivo em até 300 caracteres, em terceira pessoa")

  // Entidades
  veiculo Veiculo?
  pessoas PessoaEnvolvida[]

  // Flags rápidas para roteamento
  ha_vitimas_fatais bool
  ha_feridos        bool
  envolve_terceiros bool

  // Documentos citados pelo segurado
  documentos_mencionados string[] @description("BO, atestado, CNH, CRLV, nota fiscal, fotos, etc")

  // Metadados de qualidade (CRÍTICO)
  confianca             float           @description("0.0 a 1.0 - sua certeza REAL na extração. Use < 0.5 se narrativa ambígua.")
  campos_faltantes      CampoFaltante[] @description("lista estruturada de gaps para abrir o sinistro")
  red_flags             RedFlag[]       @description("sinais de inconsistência, fraude potencial, ou narrativa atípica")
  requer_esclarecimento bool            @description("true APENAS se o EVENTO em si não ficou claro. NÃO use true só porque faltam documentos.")
  perguntas_sugeridas   string[]        @description("perguntas objetivas para o bot fazer ao segurado, se requer_esclarecimento=true")
}

// --- Função principal ---

function ExtrairSinistro(narrativa: string) -> ExtracaoSinistro {
  client Claude
  prompt #"
    Você é um analista sênior de sinistros da 88i Seguradora Digital.
    Sua função é extrair dados estruturados da narrativa livre de um segurado.

    REGRAS DE EXTRAÇÃO (seguir literalmente):

    1. Se uma informação NÃO estiver explícita no texto, retorne null.
       NUNCA invente, infira ou complete com "o provável".

    2. O campo `confianca` deve refletir sua certeza real:
       - 0.9-1.0: narrativa clara, todos os campos críticos presentes
       - 0.6-0.9: narrativa clara mas com lacunas não-bloqueantes
       - 0.3-0.6: narrativa ambígua ou com contradições
       - 0.0-0.3: narrativa insuficiente para classificar

    3. `campos_faltantes` — classificação por criticidade:
       - "bloqueante": informação que SÓ O SEGURADO pode fornecer
         e é essencial para classificar o sinistro.
         NÃO use "bloqueante" para dados consultáveis em sistema.
       - "importante": dado útil que será cruzado/validado em etapa posterior.
       - "opcional": nice-to-have para análise mais rica.

    4. `red_flags`: identifique sinais como timing atípico, contradições,
       detalhes suspeitos ou valores incomuns.

    5. `perguntas_sugeridas`: apenas se requer_esclarecimento=true.
       Máximo 3 perguntas, objetivas, em português claro.

    6. `tipo_sinistro`: se a narrativa não permite classificar com confiança,
       use INDEFINIDO em vez de chutar.

    7. `requer_esclarecimento` é sobre COMPREENSÃO DO EVENTO, não documentação:
       - TRUE se não ficou claro o que aconteceu
       - FALSE se entendeu o evento, mesmo que faltem documentos

    8. `plataforma_mencionada`: identifique a plataforma pelo nome:
       - "uber", "uber eats", "uber flash", "uber envios" → UBER
       - "99", "99entrega", "99pop" → NOVENTA_E_NOVE
       - "ifood" → IFOOD
       - "rappi" → RAPPI
       - "loggi" → LOGGI
       - "lalamove" → LALAMOVE
       - outra plataforma nomeada → OUTRA_PLATAFORMA
       - nenhuma plataforma citada → NAO_MENCIONADA

    Narrativa do segurado:
    ---
    {{ narrativa }}
    ---

    {{ ctx.output_format }}
  "#
}

// --- Cliente LLM ---

client<llm> Claude {
  provider anthropic
  options {
    model "claude-sonnet-4-5"
    api_key env.ANTHROPIC_API_KEY
    max_tokens 2500
    temperature 0.0
  }
}

// --- Testes embutidos ---

test caso_colisao_moto_uber {
  functions [ExtrairSinistro]
  args {
    narrativa #"
      oi boa tarde, meu nome é joão silva, sou motorista de app uber eats.
      ontem a noite por volta das 22h bati minha moto honda cg 160 preta placa
      ABC1D23 na av paulista com um carro que virou sem dar seta. to com a perna
      direita quebrada, fui no hospital das clinicas e o medico me deu atestado
      de 30 dias parado. ja fiz o BO na delegacia online. preciso da diaria.
    "#
  }
}

test caso_colisao_moto_99 {
  functions [ExtrairSinistro]
  args {
    narrativa #"
      bom dia, faço entregas pela 99Entrega. ontem bati minha moto num buraco
      na rua e quebrei o braço. to com atestado de 45 dias. preciso abrir sinistro.
    "#
  }
}

test caso_ambiguo_bagagem {
  functions [ExtrairSinistro]
  args {
    narrativa #"
      sumiu minha encomenda
    "#
  }
}

test caso_suspeito {
  functions [ExtrairSinistro]
  args {
    narrativa #"
      tive um acidente semana passada, acho que foi terça ou quarta. caí da moto
      sozinho numa rua que não lembro o nome. não tem BO nem foto, mas quebrei o
      braço. o medico disse 90 dias parado. preciso do valor maximo do seguro
    "#
  }
}
