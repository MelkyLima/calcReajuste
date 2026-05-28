from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


MOEDA = Decimal("0.01")
TABELA_IPER = (
    (Decimal("5000.00"), Decimal("0.11")),
    (Decimal("7500.00"), Decimal("0.115")),
    (Decimal("12000.00"), Decimal("0.12")),
    (Decimal("16000.00"), Decimal("0.125")),
    (Decimal("19000.00"), Decimal("0.13")),
    (Decimal("35000.00"), Decimal("0.135")),
)
ALIQUOTA_IPER_ACIMA = Decimal("0.14")
ALIQUOTA_REAJUSTE = Decimal("0.0505")
MESES_RETROATIVOS = 5
DEDUCAO_DEPENDENTE_IRRF = Decimal("189.59")
GATIC_40_VALOR = Decimal("2569.86")


@dataclass(frozen=True)
class ItemContracheque:
    tipo: str
    descricao: str
    valor: Decimal


@dataclass(frozen=True)
class DadosBase:
    vencimento: Decimal | None
    dependentes: int = 0
    itens: tuple[ItemContracheque, ...] = ()
    pensao_valor: Decimal = Decimal("0.00")


@dataclass(frozen=True)
class ResultadoReposicao:
    iper_atual: Decimal
    irrf_atual: Decimal
    novo_vencimento: Decimal
    novo_iper: Decimal
    novo_irrf: Decimal
    diferenca_mensal: Decimal
    retroativo_bruto: Decimal
    iper_retroativo_total: Decimal
    irrf_retroativo: Decimal
    retroativo_liquido: Decimal


@dataclass(frozen=True)
class ResultadoGatic:
    gatic_valor: Decimal
    novo_vencimento: Decimal
    remuneracao_bruta: Decimal
    base_irpf: Decimal
    novo_iper: Decimal
    novo_irpf: Decimal
    remuneracao_liquida: Decimal


def moeda(valor: Decimal | float | int | None) -> Decimal | None:
    if valor is None:
        return None

    return Decimal(str(valor)).quantize(
        MOEDA,
        rounding=ROUND_HALF_UP,
    )


def formatar_moeda(
    valor: Decimal | float | int | None
) -> str:

    valor_formatado = moeda(valor)

    if valor_formatado is None:
        return "---"

    return (
        f"R$ {valor_formatado:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def converter_moeda_texto(valor: str) -> Decimal:
    return Decimal(
        valor.replace(".", "").replace(",", ".")
    )


def calcular_iper_progressivo(
    vencimento: Decimal | float | int,
) -> Decimal:
    valor = Decimal(str(vencimento))
    total = Decimal("0.00")
    limite_anterior = Decimal("0.00")

    for limite, aliquota in TABELA_IPER:
        if valor <= limite_anterior:
            break

        parte = min(valor, limite) - limite_anterior
        total += parte * aliquota
        limite_anterior = limite

    if valor > limite_anterior:
        total += (valor - limite_anterior) * ALIQUOTA_IPER_ACIMA

    return moeda(total) or Decimal("0.00")


def calcular_iper(
    vencimento: Decimal | float | int
) -> Decimal:

    return calcular_iper_progressivo(vencimento)


def calcular_irrf(
    base_calculo: Decimal | float | int,
    dependentes: int = 0,
) -> Decimal:

    base = (
        Decimal(str(base_calculo))
        - (
            Decimal(dependentes)
            * DEDUCAO_DEPENDENTE_IRRF
        )
    )

    if base <= Decimal("2259.20"):
        return Decimal("0.00")

    if base <= Decimal("2826.65"):
        imposto = (
            (base * Decimal("0.075"))
            - Decimal("169.44")
        )

    elif base <= Decimal("3751.05"):
        imposto = (
            (base * Decimal("0.15"))
            - Decimal("381.44")
        )

    elif base <= Decimal("4664.68"):
        imposto = (
            (base * Decimal("0.225"))
            - Decimal("662.77")
        )

    else:
        imposto = (
            (base * Decimal("0.275"))
            - Decimal("896.00")
        )

    return max(
        moeda(imposto) or Decimal("0.00"),
        Decimal("0.00"),
    )


def calcular_reposicao(
    vencimento_base: Decimal,
    dependentes_irpf: int,
    pensao_valor: Decimal = Decimal("0.00"),
) -> ResultadoReposicao:

    iper_atual = calcular_iper(
        vencimento_base
    )

    irrf_atual = calcular_irrf(
        vencimento_base
        - iper_atual
        - pensao_valor,
        dependentes_irpf,
    )

    novo_vencimento = (
        moeda(
            vencimento_base
            * (
                Decimal("1")
                + ALIQUOTA_REAJUSTE
            )
        )
        or Decimal("0.00")
    )

    novo_iper = calcular_iper(
        novo_vencimento
    )

    novo_irrf = calcular_irrf(
        novo_vencimento
        - novo_iper
        - pensao_valor,
        dependentes_irpf,
    )

    diferenca_mensal = (
        moeda(
            novo_vencimento
            - vencimento_base
        )
        or Decimal("0.00")
    )

    retroativo_bruto = (
        moeda(
            diferenca_mensal
            * MESES_RETROATIVOS
        )
        or Decimal("0.00")
    )

    iper_retroativo_total = (
        moeda(
            (
                novo_iper
                - iper_atual
            )
            * MESES_RETROATIVOS
        )
        or Decimal("0.00")
    )

    irrf_retroativo = (
        moeda(
            max(
                novo_irrf
                - irrf_atual,
                Decimal("0.00"),
            )
            * MESES_RETROATIVOS
        )
        or Decimal("0.00")
    )

    retroativo_liquido = (
        moeda(
            retroativo_bruto
            - iper_retroativo_total
            - irrf_retroativo
        )
        or Decimal("0.00")
    )

    return ResultadoReposicao(
        iper_atual=iper_atual,
        irrf_atual=irrf_atual,
        novo_vencimento=novo_vencimento,
        novo_iper=novo_iper,
        novo_irrf=novo_irrf,
        diferenca_mensal=diferenca_mensal,
        retroativo_bruto=retroativo_bruto,
        iper_retroativo_total=iper_retroativo_total,
        irrf_retroativo=irrf_retroativo,
        retroativo_liquido=retroativo_liquido,
    )


def calcular_gatic(
    vencimento_base: Decimal | float | int | None,
    dependentes_irpf: int | None,
    pensao_valor: Decimal | float | int | None,
    total_proventos_atual: Decimal | float | int | None,
    geap_valor: Decimal | float | int | None,
    descontos_gerais_atual: Decimal | float | int | None,
) -> ResultadoGatic:
    return calcular_gatic_com_totais(
        vencimento_base=moeda(vencimento_base) or Decimal("0.00"),
        dependentes_irpf=int(dependentes_irpf or 0),
        pensao_valor=moeda(pensao_valor) or Decimal("0.00"),
        total_proventos_atual=moeda(total_proventos_atual) or Decimal("0.00"),
        geap_valor=moeda(geap_valor) or Decimal("0.00"),
        descontos_gerais_atual=moeda(descontos_gerais_atual) or Decimal("0.00"),
    )


def calcular_gatic_com_totais(
    vencimento_base: Decimal,
    dependentes_irpf: int,
    pensao_valor: Decimal,
    total_proventos_atual: Decimal,
    geap_valor: Decimal,
    descontos_gerais_atual: Decimal,
) -> ResultadoGatic:

    # GATIC 40%
    gatic_valor = GATIC_40_VALOR

    # VENCIMENTO COM REAJUSTE
    novo_vencimento = (
        moeda(
            vencimento_base
            * (
                Decimal("1")
                + ALIQUOTA_REAJUSTE
            )
        )
        or Decimal("0.00")
    )

    proventos_vencimento = vencimento_base
    proventos_adicionais = (
        total_proventos_atual - proventos_vencimento
    )
    if proventos_adicionais < Decimal("0.00"):
        proventos_adicionais = Decimal("0.00")

    remuneracao_bruta = (
        moeda(
            novo_vencimento
            + proventos_adicionais
            + gatic_valor
        )
        or Decimal("0.00")
    )

    base_irpf = (
        moeda(
            novo_vencimento
            + gatic_valor
        )
        or Decimal("0.00")
    )

    novo_iper = calcular_iper(base_irpf)

    # IRPF
    novo_irpf = calcular_irrf(
        base_irpf - novo_iper - pensao_valor,
        dependentes_irpf,
    )

    descontos_geap = geap_valor
    descontos_pensao = pensao_valor
    descontos_gerais = descontos_gerais_atual

    # LÍQUIDO
    remuneracao_liquida = (
        moeda(
            remuneracao_bruta
            - novo_irpf
            - novo_iper
            - descontos_geap
            - descontos_pensao
            - descontos_gerais
        )
        or Decimal("0.00")
    )

    return ResultadoGatic(
        gatic_valor=gatic_valor,
        novo_vencimento=novo_vencimento,
        remuneracao_bruta=remuneracao_bruta,
        base_irpf=base_irpf,
        novo_iper=novo_iper,
        novo_irpf=novo_irpf,
        remuneracao_liquida=remuneracao_liquida,
    )