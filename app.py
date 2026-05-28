from __future__ import annotations

from decimal import Decimal
from html import escape

import streamlit as st

from calculos import (
    DadosBase,
    GATIC_40_VALOR,
    calcular_gatic,
    calcular_gatic_com_totais,
    calcular_reposicao,
    converter_moeda_texto,
    formatar_moeda,
    moeda,
)
from pdf_utils import (
    extrair_dados_pdf,
    totalizar_descontos_por_descricao,
    totalizar_itens,
    validar_pdf,
)



def render_card(titulo: str, valor: str, classe: str = "mini-card") -> None:
    st.markdown(
        f"""
        <div class="{escape(classe)}">
            <div>{escape(titulo)}</div>
            <div class="valor">{escape(valor)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def configurar_pagina() -> None:
    st.set_page_config(
        page_title="Calculadora de Retroativo",
        page_icon=":moneybag:",
        layout="wide",
    )

    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(135deg, #0f172a, #111827);
            color: white;
        }

        h1 {
            color: white;
            text-align: center;
            font-weight: 700;
            margin-bottom: 0.35rem;
        }

        .subtitle {
            text-align: center;
            color: #cbd5e1;
            font-size: 0.98rem;
            margin-bottom: 1.2rem;
        }

        h2 {
            color: #e5e7eb;
            text-align: left;
            font-size: 1.2rem;
            font-weight: 600;
            margin-top: 1.6rem;
            margin-bottom: 0.8rem;
        }

        .mini-card,
        .retro-card {
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            gap: 6px;
            justify-content: center;
            min-height: 110px;
            overflow-wrap: anywhere;
            padding: 16px;
            text-align: center;
        }

        .mini-card {
            background-color: #1e293b;
        }

        .valor {
            color: #38bdf8;
            font-size: clamp(1rem, 1.9vw, 1.4rem);
            font-weight: 700;
            line-height: 1.2;
            word-break: break-word;
        }

        .retro-card {
            background: linear-gradient(160deg, #0b1220, #172554);
            border: 1px solid #3b82f6;
            box-shadow: 0 10px 24px rgba(59, 130, 246, 0.22);
        }

        .retro-card .valor {
            color: #93c5fd;
        }

        .retro-card--highlight {
            background: linear-gradient(135deg, #14532d, #166534);
            border-color: #22c55e;
            box-shadow: 0 12px 26px rgba(34, 197, 94, 0.30);
        }

        .retro-card--highlight .valor {
            color: #dcfce7;
        }

        .retro-card--warn {
            box-shadow: 0 8px 20px rgba(251, 191, 36, 0.14);
        }

        .retro-card--warn .valor {
            color: #f7c572;
        }

        .retro-card--row2 {
            margin-top: 14px;
        }

        [data-testid="stFileUploaderDropzoneInstructions"] {
            display: none;
        }

        [data-testid="stFileUploaderDropzone"] button {
            position: relative;
        }

        [data-testid="stFileUploaderDropzone"] button span,
        [data-testid="stFileUploaderDropzone"] button p,
        [data-testid="stFileUploaderDropzone"] button [data-testid="stMarkdownContainer"] {
            display: none !important;
        }

        [data-testid="stFileUploaderDropzone"] button::after {
            content: "Inserir Contracheque PDF";
            font-size: 0.95rem;
            line-height: 1;
        }

        @media (max-width: 900px) {
            h1 {
                font-size: 1.15rem !important;
                line-height: 1.2 !important;
                margin-bottom: 0.35rem !important;
            }

            .subtitle {
                font-size: 0.78rem !important;
                line-height: 1.25 !important;
                margin-bottom: 0.75rem !important;
                padding: 0 4px;
            }

            h2,
            h4 {
                font-size: 0.92rem !important;
                line-height: 1.22 !important;
            }

            .mini-card,
            .retro-card {
                border-radius: 8px;
                margin-bottom: 10px;
                min-height: 96px;
                padding: 14px;
            }

            .valor {
                font-size: 1.05rem !important;
                line-height: 1.15 !important;
            }

            .mini-card div:first-child,
            .retro-card div:first-child {
                font-size: 0.8rem !important;
                line-height: 1.2 !important;
            }

            .retro-card--row2 {
                margin-top: 10px;
            }

            div[data-testid="stHorizontalBlock"] {
                display: flex !important;
                flex-direction: row !important;
                flex-wrap: wrap !important;
                gap: 0.65rem !important;
            }

            div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
                flex: 0 0 calc(50% - 0.35rem) !important;
                max-width: calc(50% - 0.35rem) !important;
                min-width: calc(50% - 0.35rem) !important;
                width: calc(50% - 0.35rem) !important;
            }

            div[data-testid="column"] > div {
                margin-bottom: 10px !important;
            }

            div[role="radiogroup"] {
                gap: 0.55rem !important;
            }

            div[role="radiogroup"] label {
                line-height: 1.25;
                margin-right: 0 !important;
            }

            [data-testid="stFileUploaderDropzone"] {
                padding: 10px !important;
            }

            [data-testid="stFileUploaderDropzone"] button {
                justify-content: center !important;
                width: 100% !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_itens_extraidos(dados_base: DadosBase) -> None:
    if not dados_base.itens:
        return

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h4>Itens Lidos do Contracheque</h4>", unsafe_allow_html=True)

    linhas = [
        {
            "Tipo": "Provento" if item.tipo == "P" else "Desconto",
            "Descrição": item.descricao,
            "Valor": formatar_moeda(item.valor),
        }
        for item in dados_base.itens
    ]
    st.dataframe(linhas, hide_index=True, use_container_width=True)


def obter_entrada_base() -> DadosBase:
    modo_entrada = st.radio(
        "Selecione uma opção",
        ["Extrair do Holerite (PDF)", "Informar dados manualmente"],
        horizontal=True,
        key="modo_entrada",
    )

    if modo_entrada == "Extrair do Holerite (PDF)":
        pdf_file = st.file_uploader(
            "Inserir Contracheque PDF",
            type=["pdf"],
            label_visibility="collapsed",
            key="uploader_pdf",
        )

        if not pdf_file:
            return DadosBase(vencimento=None)

        try:
            validar_pdf(pdf_file)
            dados_pdf = extrair_dados_pdf(pdf_file.getvalue())
            if dados_pdf.vencimento is None:
                st.warning("Não encontrei o vencimento no PDF. Informe os dados manualmente.")
            else:
                st.success("Dados extraídos do PDF com sucesso.")
            render_itens_extraidos(dados_pdf)
            return dados_pdf
        except ValueError as erro:
            st.error(str(erro))
        except Exception:
            st.error("Não foi possível processar este PDF. Confira o arquivo e tente novamente.")

        return DadosBase(vencimento=None)

    manual_col1, manual_col2 = st.columns(2)
    with manual_col1:
        vencimento_manual = st.number_input(
            "Vencimento Base",
            min_value=0.0,
            value=0.0,
            step=100.0,
            format="%.2f",
            key="vencimento_manual",
        )
    with manual_col2:
        dependentes_manual = st.number_input(
            "Dependentes IRPF",
            min_value=0,
            value=0,
            step=1,
            key="dependentes_manual",
        )

    return DadosBase(
        vencimento=moeda(vencimento_manual) if vencimento_manual > 0 else None,
        dependentes=int(dependentes_manual),
        pensao_valor=Decimal("0.00"),
    )


def render_dados_principais(
    vencimento_base: Decimal | None,
    dependentes_irpf: int,
    irrf_atual: Decimal | None = None,
    iper_atual: Decimal | None = None,
    pensao_valor: Decimal | None = None,
) -> None:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h4>Dados Principais</h4>", unsafe_allow_html=True)

    itens = [
        ("Vencimento Base", formatar_moeda(vencimento_base)),
        ("Dependentes IRPF", str(dependentes_irpf) if vencimento_base else "---"),
    ]

    if irrf_atual is not None:
        itens.append(("IRRF Atual (Estimado)", formatar_moeda(irrf_atual) if vencimento_base else "---"))
    if iper_atual is not None:
        itens.append(("IPER Atual (Estimado)", formatar_moeda(iper_atual) if vencimento_base else "---"))
    if pensao_valor is not None:
        itens.append(("Pensão", formatar_moeda(pensao_valor)))

    for coluna, (titulo, valor) in zip(st.columns(len(itens)), itens):
        with coluna:
            render_card(titulo, valor)


def render_detalhes_calc_gatic(
    dados_base: DadosBase,
    total_proventos: Decimal,
    total_descontos: Decimal,
    geap_valor: Decimal,
    resultado: ResultadoGatic,
    pensao_valor: Decimal,
) -> None:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h4>Resumo dos Dados Extraídos</h4>", unsafe_allow_html=True)

    itens = [
        ("Total de Proventos", formatar_moeda(total_proventos)),
        ("Total de Descontos", formatar_moeda(total_descontos)),
        ("Desconto GEAP", formatar_moeda(geap_valor)),
        ("Pensão", formatar_moeda(pensao_valor)),
    ]

    for coluna, item in zip(st.columns(len(itens)), itens):
        with coluna:
            render_card(item[0], item[1])


def render_reposicao() -> None:
    st.markdown("<h1>Retroativo da Reposição 5,05%</h1>", unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Reajuste: <strong>5,05%</strong> | Meses Retroativos: <strong>5</strong></div>',
        unsafe_allow_html=True,
    )

    dados_base = obter_entrada_base()
    vencimento_base = dados_base.vencimento
    pensao_valor = dados_base.pensao_valor
    tem_pensao_pdf = pensao_valor > Decimal("0.00")

    if not tem_pensao_pdf:
        tem_pensao = st.radio(
            "Pensão",
            ["Não informar pensão", "Informar valor de pensão"],
            horizontal=True,
            key="tem_pensao_reposicao",
        )

        if tem_pensao == "Informar valor de pensão":
            pensao_valor = moeda(
                st.number_input(
                    "Valor da Pensão",
                    min_value=0.0,
                    value=0.0,
                    step=50.0,
                    format="%.2f",
                    key="pensao_valor_reposicao_input",
                )
            ) or Decimal("0.00")
    else:
        st.markdown(
            '<div class="subtitle">Pensão extraída do PDF</div>',
            unsafe_allow_html=True,
        )

    resultado = (
        calcular_reposicao(vencimento_base, dados_base.dependentes, pensao_valor)
        if vencimento_base
        else None
    )
    render_dados_principais(
        vencimento_base,
        dados_base.dependentes,
        resultado.irrf_atual if resultado else Decimal("0.00"),
        resultado.iper_atual if resultado else Decimal("0.00"),
        pensao_valor if (tem_pensao_pdf or (tem_pensao == "Informar valor de pensão")) else None,
    )

    if resultado is None:
        return

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h4>Valores Após Reajuste de 5,05%</h4>", unsafe_allow_html=True)
    for coluna, item in zip(
        st.columns(3),
        [
            ("Novo Vencimento", resultado.novo_vencimento),
            ("Novo IRRF (Estimado)", resultado.novo_irrf),
            ("Novo IPER (Estimado)", resultado.novo_iper),
        ],
    ):
        with coluna:
            render_card(item[0], formatar_moeda(item[1]))

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h4>Retroativos</h4>", unsafe_allow_html=True)
    cards = [
        ("Diferença Mensal", resultado.diferenca_mensal, "retro-card"),
        ("Retroativo Bruto", resultado.retroativo_bruto, "retro-card"),
        ("IPER Retroativo", resultado.iper_retroativo_total, "retro-card"),
        ("IRRF Retroativo (Adicional)", resultado.irrf_retroativo, "retro-card"),
        ("Retroativo Líquido", resultado.retroativo_liquido, "retro-card retro-card--highlight"),
    ]

    for coluna, (titulo, valor, classe) in zip(st.columns(5), cards):
        with coluna:
            render_card(titulo, formatar_moeda(valor), classe)


def render_gatic_40() -> None:
    st.markdown(
        "<h1>Remuneração com GATIC 40%</h1>",
        unsafe_allow_html=True,
    )

    dados_base = obter_entrada_base()
    pensao_valor = dados_base.pensao_valor
    tem_pensao_pdf = pensao_valor > Decimal("0.00")
    dependentes_irpf = int(dados_base.dependentes or 0)
    pensao_valor = moeda(pensao_valor) or Decimal("0.00")

    if not tem_pensao_pdf:
        tem_pensao = st.radio(
            "Pensão",
            ["Não informar pensão", "Informar valor de pensão"],
            horizontal=True,
            key="tem_pensao",
        )

        if tem_pensao == "Informar valor de pensão":
            pensao_valor = moeda(
                st.number_input(
                    "Valor da Pensão",
                    min_value=0.0,
                    value=0.0,
                    step=50.0,
                    format="%.2f",
                    key="pensao_valor_input",
                )
            ) or Decimal("0.00")
    else:
        st.markdown(
            '<div class="subtitle">Pensão extraída do PDF</div>',
            unsafe_allow_html=True,
        )

    resultado = None
    geap_valor = Decimal("0.00")
    total_proventos = dados_base.vencimento or Decimal("0.00")
    total_descontos = Decimal("0.00")

    if dados_base.vencimento:
        try:
            if dados_base.itens:
                total_proventos = totalizar_itens(dados_base.itens, "P")
                total_descontos = totalizar_itens(dados_base.itens, "D")
                geap_valor = totalizar_descontos_por_descricao(
                    dados_base.itens,
                    {"GEAP"},
                )
                desconto_irrf_atual = totalizar_descontos_por_descricao(
                    dados_base.itens,
                    {"IRRF"},
                )
                desconto_iper_atual = totalizar_descontos_por_descricao(
                    dados_base.itens,
                    {"IPER"},
                )
                descontos_gerais = (
                    total_descontos
                    - geap_valor
                    - dados_base.pensao_valor
                    - desconto_irrf_atual
                    - desconto_iper_atual
                )
                if descontos_gerais < Decimal("0.00"):
                    descontos_gerais = Decimal("0.00")

                resultado = calcular_gatic(
                    dados_base.vencimento,
                    dependentes_irpf,
                    pensao_valor,
                    total_proventos,
                    geap_valor,
                    descontos_gerais,
                )
            else:
                resultado = calcular_gatic(
                    dados_base.vencimento,
                    dependentes_irpf,
                    pensao_valor,
                    dados_base.vencimento,
                    Decimal("0.00"),
                    Decimal("0.00"),
                )
        except Exception as erro:
            st.error("Não foi possível calcular GATIC 40%. Verifique os dados e tente novamente.")
            st.exception(erro)
            return

    if resultado is not None:
        render_detalhes_calc_gatic(
            dados_base,
            total_proventos,
            total_descontos,
            geap_valor,
            resultado,
            pensao_valor,
        )

    render_dados_principais(
        dados_base.vencimento,
        dados_base.dependentes,
        pensao_valor=pensao_valor if (tem_pensao_pdf or (tem_pensao == "Informar valor de pensão")) else None,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h4>Novos Valores</h4>", unsafe_allow_html=True)
    res1, res2, res3 = st.columns(3)
    res4, res5, res6, res7 = st.columns(4)

    gatic_valor = resultado.gatic_valor if resultado else GATIC_40_VALOR
    cards_linha_1 = [
        (res1, "Base de Cálculo IRPF", resultado.base_irpf if resultado else None, "retro-card retro-card--warn"),
        (res2, "Novo IRPF", resultado.novo_irpf if resultado else None, "retro-card retro-card--warn"),
        (res3, "Novo IPER", resultado.novo_iper if resultado else None, "retro-card retro-card--warn"),
    ]
    cards_linha_2 = [
        (res4, "Novo Vencimento (5,05%)", resultado.novo_vencimento if resultado else None, "retro-card retro-card--row2"),
        (res5, "Remuneração Bruta", resultado.remuneracao_bruta if resultado else None, "retro-card retro-card--row2"),
        (res6, "GATIC 40%", gatic_valor, "retro-card retro-card--row2"),
        (
            res7,
            "Remuneração Líquida",
            resultado.remuneracao_liquida if resultado else None,
            "retro-card retro-card--highlight retro-card--row2",
        ),
    ]

    for coluna, titulo, valor, classe in [*cards_linha_1, *cards_linha_2]:
        with coluna:
            render_card(titulo, formatar_moeda(valor), classe)


def main() -> None:
    configurar_pagina()

    tela = st.sidebar.radio(
        "Telas",
        ["LC 376/2026", "PORTARIA 408/2026", "GATIC (retroativa)"],
    )

    if tela == "LC 376/2026":
        render_reposicao()
    elif tela == "PORTARIA 408/2026":
        render_gatic_40()
    else:
        st.markdown(f"<h2>{escape(tela)}</h2>", unsafe_allow_html=True)
        st.info("Tela em construção.")

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.caption("***Cálculos estimados.")


if __name__ == "__main__":
    main()
