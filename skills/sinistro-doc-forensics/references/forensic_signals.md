# Sinais Forenses Documentais — 88i Seguradora Digital (v2)

## Sinais de plausibilidade

### Universais
- Cabeçalho institucional compatível com o tipo documental
- Diagramação e formatação homogêneas
- Dados essenciais presentes e completos
- Datas coerentes entre si
- Assinatura, carimbo, certificação digital ou identificador compatível
- Narrativa e terminologia formais compatíveis com o tipo

### Específicos 88i / delivery / mobilidade
- BO com código de verificação ou autenticação digital (BO-e)
- CRLV com RENAVAM de 11 dígitos e placa em formato válido (AAA-0A00 ou AAA-0000)
- NF-e com chave de acesso de 44 dígitos e autorização SEFAZ
- CRM numérico + UF válida (26 estados + DF)
- Screenshot de app com interface reconhecível da plataforma (Uber, 99, iFood)
- Comprovante IMEI com 15 dígitos
- Certidão de não localização com referência ao BO original
- BRAT com croqui ou descrição de posição dos veículos

---

## Sinais de suspeita

### Visuais / estruturais
- Recorte, colagem ou sobreposição aparente
- Fontes heterogêneas em campos sensíveis (nome, data, valor)
- Espaçamento irregular em áreas críticas
- Desalinhamento de texto em relação ao layout
- Resolução inconsistente entre áreas do documento (parte nítida, parte borrada)
- Margens ou bordas cortadas de forma a ocultar informações

### De conteúdo
- Ausência de campo essencial do tipo documental
- CRM sem UF ou CRM/UF que não correspondem ao profissional
- Narrativa incompatível com o tipo de documento
- Datas conflitantes internamente (emissão < fato)
- Nome do paciente/segurado divergente entre áreas do mesmo doc
- BO sem número de registro ou sem órgão emissor
- NF sem chave SEFAZ ou com chave incompleta (<44 dígitos)
- CRLV com ano modelo > ano exercício

### Específicos delivery / mobilidade
- Screenshot de app com barra de ferramentas de edição visível
- Screenshot com elementos de UI inconsistentes com o app declarado
- Período de trabalho no app incompatível com horário do sinistro
- IMEI no comprovante de bloqueio ≠ IMEI na NF do celular
- Orçamento de oficina com valor desproporcional ao dano visível
- Laudo médico com CID incompatível com a narrativa do acidente
- Certidão de não localização emitida < 15 dias após o fato
- Múltiplos sinistros em < 6 meses com padrão documental similar
- Comprovante de residência com > 90 dias (exigência 88i)
- NF emitida para parente do segurado (vedado em Bagagens/Encomendas)

---

## Política de autenticidade

NUNCA declarar autenticidade jurídica absoluta. Classificar APENAS como:

| Status | Critério |
|--------|----------|
| `plausible` | Sinais positivos presentes, zero sinais de suspeita |
| `suspicious` | 1+ sinais de suspeita identificados |
| `indeterminate` | Qualidade insuficiente OU sinais mistos (positivos + negativos) |

Na dúvida entre `plausible` e `indeterminate`, use `indeterminate`.
Na presença de qualquer sinal de suspeita, use `suspicious` independentemente dos sinais positivos.
