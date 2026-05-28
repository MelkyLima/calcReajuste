from __future__ import annotations

from decimal import Decimal
from io import BytesIO
import re
from typing import BinaryIO

import streamlit as st
from PyPDF2 import PdfReader

from calculos import DadosBase, ItemContracheque, converter_moeda_texto

MAX_PDF_MB = 8
MAX_PDF_PAGINAS = 6

PADRAO_VALOR = r"\d{1,3}(?:\.\d{3})*,\d{2}"
PADRAO_ITEM_LINHA = re.compile(
    rf"^\s*([PD])\s+(.+?)\s+({PADRAO_VALOR})\s*$",
    re.IGNORECASE,
)
PADRAO_VALOR_EXATO = re.compile(rf"^({PADRAO_VALOR})$")
PADRAO_VALOR_FINAL = re.compile(rf"^(.*?)\s+({PADRAO_VALOR})\s*$")
PADRAO_VENCIMENTO = re.compile(r"VENCIMENTO\s+([\d\.]+,\d{2})", re.IGNORECASE)
PADRAO_DEPENDENTES = re.compile(
    r"N[\u00ba\u00b0]\s*DEPENDENTES\s*IRRF\s+(\d+)",
    re.IGNORECASE,
)


def validar_pdf(arquivo_pdf: BinaryIO) -> None:
    try:
        tamanho_mb = arquivo_pdf.size / (1024 * 1024)
    except AttributeError:
        pos_atual = arquivo_pdf.tell()
        arquivo_pdf.seek(0, 2)
        tamanho_mb = arquivo_pdf.tell() / (1024 * 1024)
        arquivo_pdf.seek(pos_atual)

    if tamanho_mb > MAX_PDF_MB:
        raise ValueError(f"O PDF deve ter no máximo {MAX_PDF_MB} MB.")


def normalizar_descricao(descricao: str) -> str:
    return " ".join(descricao.split()).strip().upper().rstrip(".")


def extrair_itens_contracheque(texto: str) -> tuple[ItemContracheque, ...]:
    linhas = [linha.strip() for linha in texto.splitlines() if linha.strip()]
    itens: list[ItemContracheque] = []

    for linha in linhas:
        item_match = PADRAO_ITEM_LINHA.match(linha)
        if item_match:
            tipo, descricao, valor = item_match.groups()
            itens.append(
                ItemContracheque(
                    tipo=tipo.upper(),
                    descricao=normalizar_descricao(descricao),
                    valor=converter_moeda_texto(valor),
                )
            )

    if itens:
        return tuple(itens)

    indice = 0
    while indice < len(linhas):
        tipo = linhas[indice].upper()
        if tipo not in {"P", "D"}:
            indice += 1
            continue

        partes_descricao: list[str] = []
        indice += 1

        while indice < len(linhas):
            valor_exato = PADRAO_VALOR_EXATO.match(linhas[indice])
            if valor_exato:
                descricao = normalizar_descricao(" ".join(partes_descricao))
                if descricao:
                    itens.append(
                        ItemContracheque(
                            tipo=tipo,
                            descricao=descricao,
                            valor=converter_moeda_texto(valor_exato.group(1)),
                        )
                    )
                indice += 1
                break

            valor_linha = PADRAO_VALOR_FINAL.match(linhas[indice])
            if valor_linha:
                descricao_na_linha, valor = valor_linha.groups()
                if descricao_na_linha:
                    partes_descricao.append(descricao_na_linha)

                descricao = normalizar_descricao(" ".join(partes_descricao))
                if descricao:
                    itens.append(
                        ItemContracheque(
                            tipo=tipo,
                            descricao=descricao,
                            valor=converter_moeda_texto(valor),
                        )
                    )
                indice += 1
                break

            if linhas[indice].upper() in {"P", "D"}:
                break

            partes_descricao.append(linhas[indice])
            indice += 1

    return tuple(itens)


def obter_vencimento_base(texto: str, itens: tuple[ItemContracheque, ...]) -> Decimal | None:
    for item in itens:
        if item.tipo == "P" and item.descricao == "VENCIMENTO":
            return item.valor

    vencimento_match = PADRAO_VENCIMENTO.search(texto)
    return converter_moeda_texto(vencimento_match.group(1)) if vencimento_match else None


def totalizar_itens(itens: tuple[ItemContracheque, ...], tipo: str) -> Decimal:
    return sum((item.valor for item in itens if item.tipo == tipo), Decimal("0.00"))


def totalizar_descontos_por_descricao(
    itens: tuple[ItemContracheque, ...],
    descricoes: set[str],
) -> Decimal:
    descricoes_normalizadas = {normalizar_descricao(descricao) for descricao in descricoes}

    return sum(
        (
            item.valor
            for item in itens
            if item.tipo == "D"
            and any(
                termo in normalizar_descricao(item.descricao)
                for termo in descricoes_normalizadas
            )
        ),
        Decimal("0.00"),
    )


@st.cache_data(show_spinner=False)
def extrair_dados_pdf(conteudo_pdf: bytes) -> DadosBase:
    reader = PdfReader(BytesIO(conteudo_pdf))

    if reader.is_encrypted:
        raise ValueError("PDF protegido por senha não pode ser processado.")

    if len(reader.pages) > MAX_PDF_PAGINAS:
        raise ValueError(f"O PDF deve ter no máximo {MAX_PDF_PAGINAS} páginas.")

    texto = "\n".join((pagina.extract_text() or "") for pagina in reader.pages)
    itens = extrair_itens_contracheque(texto)
    dependentes_match = PADRAO_DEPENDENTES.search(texto)

    pensao_valor = totalizar_descontos_por_descricao(
        itens,
        {"PENSÃO", "PENSAO"},
    )

    return DadosBase(
        vencimento=obter_vencimento_base(texto, itens),
        dependentes=int(dependentes_match.group(1)) if dependentes_match else 0,
        itens=itens,
        pensao_valor=pensao_valor,
    )
