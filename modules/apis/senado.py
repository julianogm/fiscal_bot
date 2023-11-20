from datetime import date

import cssselect
import lxml.html
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from constant import *


def get_senado(url):
    response = requests.get(url, headers={"Accept": "application/json"})
    return response.json()


def lista_senadores():
    ls = get_senado(API_SENADO + "senador/lista/atual")["ListaParlamentarEmExercicio"][
        "Parlamentares"
    ]["Parlamentar"]
    return ls


def botoes_senadores():
    keyboard = [
        [
            InlineKeyboardButton("Por Partido ", callback_data="sen_partido"),
            InlineKeyboardButton("Por Estado", callback_data="sen_estado"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def nomes_senadores(lista=lista_senadores):
    nomes = "\n".join(
        [
            f"{sen['IdentificacaoParlamentar']['NomeParlamentar']} - /sen_{sen['IdentificacaoParlamentar']['CodigoParlamentar']}"
            for sen in lista
        ]
    )
    return nomes


def senador_por_nome(nome):
    lista = lista_senadores()
    nome_normal = nome.lower().translate(NORMALIZAR)
    lf = [
        sen
        for sen in lista
        if nome_normal
        in sen["IdentificacaoParlamentar"]["NomeParlamentar"]
        .lower()
        .translate(NORMALIZAR)
    ]
    return lf


# def senador_por_estado(siglaUF):
#     response = get_senado(API_SENADO + f"senador/lista/atual")
#     lista_sen = response["ListaParlamentarEmExercicio"]["Parlamentares"]["Parlamentar"]

#     ls_filtrada = [
#         sen
#         for sen in lista_sen
#         if sen["IdentificacaoParlamentar"]["UfParlamentar"] == siglaUF
#     ]

#     return ls_filtrada


def senador_por_estado(siglaUF):
    response = get_senado(API_SENADO + f"senador/lista/atual")
    lista_sen = response["ListaParlamentarEmExercicio"]["Parlamentares"]["Parlamentar"]

    return list(
        filter(
            lambda sen: sen["IdentificacaoParlamentar"]["UfParlamentar"] == siglaUF,
            lista_sen,
        )
    )


def senador_por_partido(siglaPartido):
    ls = lista_senadores()
    lf = [
        sen
        for sen in ls
        if sen["IdentificacaoParlamentar"]["SiglaPartidoParlamentar"] == siglaPartido
    ]
    return lf


def senador_por_id(id):
    senador = get_senado(API_SENADO + f"senador/{id}")["DetalheParlamentar"][
        "Parlamentar"
    ]
    return senador


def dados_senador(senador):
    dados = get_senado(
        API_SENADO
        + f"senador/{senador['IdentificacaoParlamentar']['CodigoParlamentar']}"
    )
    return montar_mensagem(senador, dados)


def lista_partidos_senadores():
    ls = lista_senadores()
    lista_partidos = [
        item["IdentificacaoParlamentar"]["SiglaPartidoParlamentar"] for item in ls
    ]
    return lista_partidos


def info_senador(id):
    ano_atual = date.today().year
    resposta = requests.get(
        f"https://www6g.senado.leg.br/transparencia/sen/{id}/?ano={ano_atual}"
    )
    arv = lxml.html.fromstring(resposta.text)

    css_sel_ceap = "#collapse-ceaps > div:nth-child(1) > table:nth-child(1) > tfoot:nth-child(4) > tr:nth-child(1) > td:nth-child(2)"
    css_sel_telefone = ".dl-horizontal > dd:nth-child(10)"

    info = []

    if arv.cssselect(css_sel_ceap):
        info.append("R$ " + arv.cssselect(css_sel_ceap)[0].text_content())
    else:
        info.append("Ainda não há gasto registrado nesse ano")

    if arv.cssselect(css_sel_ceap):
        info.append(arv.cssselect(css_sel_telefone)[0].text_content())
    else:
        info.append("Número não encontrado")

    return info


def montar_mensagem(senador, dados):
    dados_senador = senador["IdentificacaoParlamentar"]
    info = info_senador(dados_senador["CodigoParlamentar"])
    nome_lower = (
        dados_senador["NomeCompletoParlamentar"]
        .replace(" ", "_")
        .translate(NORMALIZAR)
        .lower()
    )
    nome_par_lower = (
        dados_senador["NomeCompletoParlamentar"]
        .replace(" ", "+")
        .translate(NORMALIZAR)
        .lower()
    )

    gasto_ceap = info[0]
    telefone = info[1][:14]

    email = (
        dados_senador.get("EmailParlamentar")
        if dados_senador.get("EmailParlamentar") != None
        else "Sem email cadastrado"
    )

    mensagem = ""
    mensagem += f"Nome civil: {dados_senador['NomeCompletoParlamentar']} \n"
    mensagem += f"Partido: {dados_senador['SiglaPartidoParlamentar']} | "
    mensagem += f"Estado: {dados_senador['UfParlamentar']} \n"
    mensagem += f"Email: {email} \n"
    mensagem += f"Telefone: {telefone} \n\n"
    mensagem += (
        f"Gastos de {dados_senador['NomeParlamentar']} em {date.today().year} \n"
    )
    mensagem += f"CEAPS: {gasto_ceap} \n\n"

    # mensagem += "Verificar processos envolvendo o parlamentar:\n"
    # mensagem += f"/p_{nome_lower} \n\n"

    mensagem += f"Mais sobre o senador(a): {dados_senador['UrlPaginaParlamentar']} \n"
    mensagem += (
        f"https://www.jusbrasil.com.br/artigos-noticias/busca?q={nome_par_lower}"
    )

    return mensagem


def botoes_partidos_senadores():
    ls = lista_senadores()
    siglas = list(
        set(
            [item["IdentificacaoParlamentar"]["SiglaPartidoParlamentar"] for item in ls]
        )
    )
    siglas.sort()
    tam = len(siglas)
    keyboard = []
    i = 0
    ultima_sigla = None

    if tam % 2 == 1:
        ultima_sigla = siglas.pop()
        tam -= 1

    while i < tam:
        keyboard.append(
            [
                InlineKeyboardButton(siglas[i], callback_data="sen_" + siglas[i]),
                InlineKeyboardButton(
                    siglas[i + 1], callback_data="sen_" + siglas[i + 1]
                ),
            ]
        )
        i += 2

    if ultima_sigla != None:
        keyboard.append(
            [
                InlineKeyboardButton(ultima_sigla, callback_data="sen_" + ultima_sigla),
                InlineKeyboardButton("<< Voltar", callback_data="sen_voltar"),
            ],
        )
    else:
        keyboard.append([InlineKeyboardButton("<< Voltar", callback_data="sen_voltar")])

    return InlineKeyboardMarkup(keyboard)


def botoes_estados_senadores():
    keyboard = []
    i = 0
    while i < 26:
        keyboard.append(
            [
                InlineKeyboardButton(UF_NOME[i], callback_data="sen_" + UF_SIGLAS[i]),
                InlineKeyboardButton(
                    UF_NOME[i + 1], callback_data="sen_" + UF_SIGLAS[i + 1]
                ),
            ]
        )
        i += 2
    keyboard.append(
        [
            InlineKeyboardButton(UF_NOME[i], callback_data="sen_" + UF_SIGLAS[i]),
            InlineKeyboardButton("<< Voltar", callback_data="sen_voltar"),
        ]
    )

    return InlineKeyboardMarkup(keyboard)