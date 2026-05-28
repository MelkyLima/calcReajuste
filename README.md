# calcReajuste

Calculadora de reajuste e GATIC para contracheques com extração de dados de PDF.

## Visão geral

O projeto agora está organizado em módulos:

- `app.py`: interface Streamlit e renderização da aplicação
- `calculos.py`: regras de cálculo financeiro
- `pdf_utils.py`: extração de valores e dados do PDF

## Instalação

1. Crie um ambiente virtual Python:

```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

## Uso

Execute a aplicação com:

```bash
streamlit run app.py
```

## Como o cálculo de GATIC está estruturado

- **Remuneração Bruta**: `Novo Vencimento (5,05%) + todos os outros proventos` extraídos do PDF + `2.569,86` de `GATIC 40%`.
- **Base de Cálculo IRPF**: `Novo Vencimento (5,05%) + 2.569,86 (GATIC 40%)`.
- **Novo IRPF**: aplica-se sobre `Base de Cálculo IRPF - IPER - Dependentes - Pensão`.
- **Remuneração Líquida**: `Remuneração Bruta - Novo IRPF - Novo IPER - Geap`.
- A aba foi renomeada para **PORTARIA408** para evitar confusão entre o nome da tela e o valor fixo de GATIC.

O código foi ajustado para que os valores de proventos e descontos sejam obtidos a partir da extração do PDF, enquanto os parâmetros fixos de legislação (`GATIC_40_VALOR`, `ALIQUOTA_REAJUSTE`) permanecem constantes.

## Observações importantes

- `GATIC_40_VALOR` é um valor fixo de `2.569,86` no cálculo da Portaria 408.
- Os `P` e os descontos preservados (como IRRF/IPER substituídos) devem ser extraídos do PDF.
- O módulo `pdf_utils.py` agora centraliza a validação e extração do arquivo.
