# Third-party dependencies

Este diretório é reservado para dependências externas versionadas localmente quando necessário.

## Hermes Agent

Para criar uma cópia local completa do Hermes e iniciar a customização da Olga:

```bash
./scripts/setup_olga_from_hermes.sh
```

Comandos opcionais:

```bash
HERMES_REPO_URL=https://github.com/NousResearch/hermes-agent ./scripts/setup_olga_from_hermes.sh third_party/hermes-agent
```

> Observação: este script requer acesso de rede ao GitHub.
