# Etiquetas de Laudos

Sistema para importar PDFs de laudos do SISCAN, extrair dados dos pacientes, revisar a lista e gerar etiquetas para impressão em PDF e DOCX.

Na tela de revisao, o operador pode ordenar os registros por data de realizacao ou numero do exame antes de selecionar as etiquetas para impressao. Tambem pode selecionar automaticamente um intervalo de numeros de exame e excluir do banco os registros selecionados.

## Dados extraídos

- Numero do exame
- Paciente
- Municipio da unidade solicitante quando ele for diferente do municipio do paciente; nesse caso a etiqueta fica sem bairro
- Municipio do paciente e bairro quando os municipios forem iguais
- Endereco no lugar do bairro quando o bairro for `ZONA RURAL`
- Data de nascimento
- Data da realizacao

Duplicados sao bloqueados quando `paciente + data de nascimento + data da realizacao` forem exatamente iguais.

## Layout das etiquetas

Folha adesiva com 21,5 cm x 28 cm e 14 etiquetas:

- 2 colunas x 7 linhas
- Margens laterais: 0,5 mm
- Margens superior e inferior: 2,2 cm
- Espaco entre colunas: 0,5 cm
- Sem espaco vertical entre etiquetas
- Cabecalho de cada etiqueta com logo CIS-VERDE e nome `MAMOGRAFIA CIS VERDE`

## Rodar localmente

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Acesse `http://localhost:8000`.

Para rodar localmente com Docker, use:

```bash
docker compose -f docker-compose.local.yml up --build
```

## Docker / Portainer

No Portainer, use o arquivo `docker-compose.yml` deste repositorio ou cole esta stack:

```yaml
services:
  etiquetas-laudos:
    image: ghcr.io/wittemberg/etiquetas-laudos:latest
    networks:
      - interna
    environment:
      TZ: America/Sao_Paulo
      ETIQUETAS_PASSWORD: ${ETIQUETAS_PASSWORD:?Defina ETIQUETAS_PASSWORD antes do primeiro deploy}
      ETIQUETAS_DB_PATH: "/app/data/etiquetas.sqlite3"
    volumes:
      - /root/etiquetas-laudos/data:/app/data
      - /root/etiquetas-laudos/uploads:/app/uploads
      - /root/etiquetas-laudos/outputs:/app/outputs
    deploy:
      replicas: 1
      update_config:
        order: start-first
        failure_action: rollback
      rollback_config:
        order: stop-first
      restart_policy:
        condition: any
      labels:
        - "traefik.enable=true"
        - "traefik.docker.network=interna"
        - "traefik.http.routers.etiquetas-laudos.rule=Host(`etiquetas-de-laudos.wrtec.com.br`)"
        - "traefik.http.routers.etiquetas-laudos.entrypoints=websecure"
        - "traefik.http.routers.etiquetas-laudos.tls=true"
        - "traefik.http.routers.etiquetas-laudos.tls.certresolver=letsencryptresolver"
        - "traefik.http.services.etiquetas-laudos.loadbalancer.server.port=8000"

networks:
  interna:
    external: true
```

## Observacao sobre dados sensiveis

Os PDFs importados e o banco SQLite podem conter dados pessoais de saude. Nao envie PDFs reais, bancos `data/` ou arquivos gerados para o GitHub. Em producao, publique atras de um proxy com HTTPS e controle de acesso.

Se `ETIQUETAS_PASSWORD` estiver definida, o sistema exige login HTTP Basic com usuario `admin`.
