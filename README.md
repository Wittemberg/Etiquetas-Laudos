# Etiquetas de Laudos

Sistema para importar PDFs de laudos do SISCAN, extrair dados dos pacientes, revisar a lista e gerar etiquetas para impressão em PDF e DOCX.

Na tela de revisao, o operador pode ordenar os registros por data de realizacao ou numero do exame antes de selecionar as etiquetas para impressao.

## Dados extraídos

- Numero do exame
- Paciente
- Municipio
- Bairro ou endereco, quando o bairro for `ZONA RURAL`
- Data de nascimento
- Data da realizacao

Duplicados sao bloqueados quando `paciente + data de nascimento + data da realizacao` forem exatamente iguais.

## Layout das etiquetas

Folha A4 com 14 etiquetas:

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

## Docker / Portainer

No Portainer, use este compose:

```yaml
services:
  etiquetas-laudos:
    build: .
    ports:
      - "8000:8000"
    environment:
      ETIQUETAS_PASSWORD: "troque-esta-senha"
    volumes:
      - etiquetas_data:/app/data
      - etiquetas_uploads:/app/uploads
      - etiquetas_outputs:/app/outputs
    restart: unless-stopped

volumes:
  etiquetas_data:
  etiquetas_uploads:
  etiquetas_outputs:
```

## Observacao sobre dados sensiveis

Os PDFs importados e o banco SQLite podem conter dados pessoais de saude. Nao envie PDFs reais, bancos `data/` ou arquivos gerados para o GitHub. Em producao, publique atras de um proxy com HTTPS e controle de acesso.

Se `ETIQUETAS_PASSWORD` estiver definida, o sistema exige login HTTP Basic com usuario `admin`.
