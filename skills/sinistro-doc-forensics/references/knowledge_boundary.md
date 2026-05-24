# Fronteira de Conhecimento — Skills, Resources, Supabase e Gold Set

## Em resources .md (estáticos, no contexto da skill)
- Taxonomia documental (classes, heurísticas, regras de classificação)
- Campos mínimos de extração por tipo de documento
- Sinais forenses (plausibilidade e suspeita)
- Regras de validação cruzada entre documentos
- Matriz de scoring de fraude (categorias, pesos, faixas)
- Política de decisão (árvore decisória, status válidos)
- Instruções de formato de saída

## Em skills SKILL.md (procedimentos, no contexto quando triggered)
- Pipeline de processamento (classifier → forensics → adjudicator)
- Procedimentos obrigatórios por etapa
- Few-shot examples de classificação
- Regras de qualidade e formato JSON
- Heurísticas críticas (BO vs. aviso, BRAT vs. BO)
- Referências cruzadas entre skills

## No Supabase (dados vivos, consultados via MCP/SQL)
- Dados do sinistro (claims, claim_documents)
- Classificações e extrações anteriores (document_classifications, document_extractions)
- Decisões operacionais (claim_decisions)
- Regras por produto e cobertura (knowledge_rules)
- Documentos obrigatórios por regra (em knowledge_rules.required_documents)
- Corner cases curados para recuperação seletiva (knowledge_examples)
- Histórico do segurado (sinistros anteriores, padrões)

## No gold set (avaliação, SEPARADO de produção)
- Casos rotulados para avaliação de qualidade (gold_cases)
- Valores esperados por campo (gold_labels)
- Decisão esperada por caso
- Dificuldade e observações do avaliador
- Métricas de regressão entre versões

## Regra essencial
O gold set NÃO é memória de produção do agente. Serve EXCLUSIVAMENTE para:
1. Medir qualidade das skills (accuracy, precision, recall)
2. Detectar regressão entre versões
3. Treinar novos analistas humanos com gabarito
4. Calibrar limiares de fraud_score

## Na skill `olga-analista-seguros-88i` (conhecimento de produto)
- Condições gerais dos produtos 88i
- Coberturas, exclusões, documentos obrigatórios
- Regras de franquia, carência, LMI, cooldown
- Condições particulares Uber
- Esta skill é OBRIGATÓRIA para o adjudicator tomar decisões de cobertura
