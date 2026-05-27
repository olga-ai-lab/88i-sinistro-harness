-- ============================================================
-- Migration 001 — 88i Sinistro Harness
-- Tabelas: raw_inbox, sinistros, hitl_tarefas, shadow_runs
-- Auditável SUSEP: todas as tabelas têm created_at e são append-only
-- ============================================================

-- raw_inbox: recebe webhook da Evolution API ANTES de processar
-- Garante auditoria SUSEP mesmo se o agente cair
create table if not exists raw_inbox (
  id           uuid primary key default gen_random_uuid(),
  source       text not null default 'whatsapp',  -- whatsapp | api | test
  payload      jsonb not null,
  narrativa    text,
  segurado_id  text,
  processed    boolean not null default false,
  processed_at timestamptz,
  created_at   timestamptz not null default now()
);

create index if not exists raw_inbox_processed_idx on raw_inbox(processed, created_at);
create index if not exists raw_inbox_segurado_idx  on raw_inbox(segurado_id);

-- sinistros: registro de cada sinistro processado
create table if not exists sinistros (
  id                    uuid primary key default gen_random_uuid(),
  protocolo             text unique not null,   -- 88i-YYYY-XXXXXXXX
  segurado_id           text,
  narrativa_original    text not null,
  tipo_sinistro         text,
  plataforma            text,
  proxima_acao          text not null,          -- pronto_para_analise | solicitar_esclarecimento | escalar_humano
  cobertura             text,
  elegivel              boolean,
  fraud_score           integer default 0,
  extracao_json         jsonb,
  veredicto_json        jsonb,
  status                text not null default 'aberto',
  timestamp_recebimento timestamptz,
  created_at            timestamptz not null default now(),
  updated_at            timestamptz not null default now()
);

create index if not exists sinistros_protocolo_idx    on sinistros(protocolo);
create index if not exists sinistros_segurado_idx     on sinistros(segurado_id);
create index if not exists sinistros_status_idx       on sinistros(status);
create index if not exists sinistros_tipo_idx         on sinistros(tipo_sinistro);
create index if not exists sinistros_created_idx      on sinistros(created_at);

-- apolices: cadastro de apólices dos segurados (stub; em produção via CloudWalk API)
create table if not exists apolices (
  id                uuid primary key default gen_random_uuid(),
  segurado_id       text not null,
  produto           text not null,        -- A | B | C
  coberturas        text[] not null,
  vigencia_inicio   date not null,
  vigencia_fim      date not null,
  carencia_ativa    boolean not null default false,
  status            text not null default 'ativa',
  created_at        timestamptz not null default now()
);

create index if not exists apolices_segurado_idx on apolices(segurado_id, status);

-- hitl_tarefas: fila de revisão humana para a Rosi
create table if not exists hitl_tarefas (
  id                          uuid primary key default gen_random_uuid(),
  protocolo                   text not null references sinistros(protocolo),
  segurado_id                 text,
  motivo                      text not null,
  prioridade                  text not null check (prioridade in ('critica','alta','media','baixa')),
  status                      text not null default 'pendente'
                              check (status in ('pendente','em_revisao','resolvida','expirada')),
  narrativa_original          text,
  tipo_sinistro               text,
  plataforma                  text,
  cobertura                   text,
  red_flags                   jsonb default '[]',
  alerta_operacional          text,
  fraud_score                 integer default 0,
  fraud_findings              text[],
  veredicto_cobertura_status  text,
  veredicto_motivo_recusa     text,
  -- resolução
  resolvida_em                timestamptz,
  analista                    text,
  decisao                     text check (decisao in ('aprovar','recusar','solicitar_docs','escalar_juridico')),
  justificativa               text,
  docs_solicitados            text[],
  created_at                  timestamptz not null default now()
);

create index if not exists hitl_status_prioridade_idx on hitl_tarefas(status, prioridade, created_at);
create index if not exists hitl_protocolo_idx          on hitl_tarefas(protocolo);

-- shadow_runs: log de divergências OCTA vs novo agente
create table if not exists shadow_runs (
  id                  uuid primary key default gen_random_uuid(),
  modo                text not null,    -- shadow | canary_octa | canary_novo | cutover
  narrativa_hash      text,             -- hash da narrativa (não guardar texto por privacidade)
  concordancia        boolean not null,
  score_concordancia  numeric(4,3),
  divergencias        jsonb default '[]',
  rota_octa           text,
  rota_novo           text,
  tipo_octa           text,
  tipo_novo           text,
  created_at          timestamptz not null default now()
);

create index if not exists shadow_concordancia_idx on shadow_runs(concordancia, created_at);
create index if not exists shadow_modo_idx          on shadow_runs(modo, created_at);

-- RLS: habilitar em produção para segurança
-- alter table sinistros    enable row level security;
-- alter table hitl_tarefas enable row level security;
-- alter table raw_inbox     enable row level security;
