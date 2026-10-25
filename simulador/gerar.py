#!/usr/bin/env python3
"""
Gera o painel-sim.generated.yaml a partir do painel.yaml.

O layout (a lambda do display), as fontes, os globals e os scripts de busca
de dados são copiados do painel.yaml. Só o que depende do hardware é trocado:

  - display Waveshare   ->  janela SDL 800x480
  - SNTP                ->  relógio do Mac
  - CPU temp / Wi-Fi    ->  valores fixos (abaixo)
  - Wi-Fi, OTA, API...  ->  removidos

Assim existe um único lugar para editar o layout: o painel.yaml.
"""

import sys
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
ORIGEM = RAIZ / "painel.yaml"
DESTINO = RAIZ / "painel-sim.generated.yaml"

LARGURA = 800
ALTURA = 480

# Valores fixos para os sensores que só existem no hardware.
CPU_TEMP_SIM = 45.0
WIFI_RSSI_SIM = -58.0

# Com que frequência a janela redesenha (no aparelho real são 60s).
ATUALIZACAO_JANELA = "5s"


class _Loader(yaml.SafeLoader):
    pass


def _tag_desconhecida(loader, tag_suffix, node):
    # !secret, !lambda, !include... Só usados em blocos que o simulador descarta.
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    return loader.construct_mapping(node)


_Loader.add_multi_constructor("!", _tag_desconhecida)


class _Dumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


def _str(dumper, data):
    if "\n" in data:
        # Sem espaços no fim das linhas, para o PyYAML aceitar o estilo literal (|).
        limpo = "\n".join(linha.rstrip() for linha in data.split("\n"))
        return dumper.represent_scalar("tag:yaml.org,2002:str", limpo, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


_Dumper.add_representer(str, _str)


def _indentar(texto: str, espacos: int) -> str:
    prefixo = " " * espacos
    return "\n".join((prefixo + linha) if linha.strip() else "" for linha in texto.split("\n"))


def _sensores(originais: list) -> list:
    """Mantém os mesmos ids; troca os sensores de hardware por valores fixos."""
    fixos = {
        "internal_temperature": (CPU_TEMP_SIM, "°C"),
        "wifi_signal": (WIFI_RSSI_SIM, "dBm"),
    }
    saida = []
    for s in originais:
        plataforma = s.get("platform")
        if plataforma in fixos:
            valor, unidade = fixos[plataforma]
            saida.append(
                {
                    "platform": "template",
                    "id": s["id"],
                    "name": s.get("name", s["id"]),
                    "unit_of_measurement": unidade,
                    "update_interval": s.get("update_interval", "60s"),
                    "lambda": f"return {valor};",
                }
            )
        else:
            saida.append(s)
    return saida


def _adaptar_http(obj):
    """O ESPHome novo (necessário para http_request em host) renomeou
    `headers` para `request_headers` nas ações http_request.*."""
    if isinstance(obj, dict):
        for chave, valor in obj.items():
            if str(chave).startswith("http_request.") and isinstance(valor, dict) and "headers" in valor:
                valor["request_headers"] = valor.pop("headers")
            _adaptar_http(valor)
    elif isinstance(obj, list):
        for item in obj:
            _adaptar_http(item)
    return obj


def gerar() -> Path:
    with open(ORIGEM, encoding="utf-8") as f:
        painel = yaml.load(f, Loader=_Loader)

    telas = [d for d in painel.get("display", []) if d.get("platform") == "waveshare_epaper"]
    if not telas:
        sys.exit("Não achei um display waveshare_epaper no painel.yaml.")
    tela = telas[0]

    modelo = str(tela.get("model", ""))
    if not modelo.startswith("7.50"):
        print(f"Aviso: modelo {modelo!r}. O simulador assume 800x480 (7.50).", file=sys.stderr)

    corpo = tela["lambda"]
    lambda_sim = (
        "it.fill(Color(255, 255, 255));\n"
        "painel_sim::EpaperView epaper(&it);\n"
        "auto desenhar = [&](esphome::display::Display &it) {\n"
        f"{_indentar(corpo, 2)}\n"
        "};\n"
        "desenhar(epaper);"
    )

    on_boot = painel.get("esphome", {}).get("on_boot", {})
    sim = {
        "substitutions": painel.get("substitutions", {}),
        "esphome": {
            "name": "painel-simulador",
            "includes": ["simulador/epaper_view.h"],
            "on_boot": {
                "priority": on_boot.get("priority", -100),
                "then": [{"delay": "3s"}, {"script.execute": "fetch_all"}],
            },
        },
        "host": {"mac_address": "02:AA:BB:CC:DD:EE"},
        "logger": {"level": "INFO"},
        "http_request": {
            "useragent": painel.get("http_request", {}).get("useragent", "esphome/painel-simulador"),
            "timeout": painel.get("http_request", {}).get("timeout", "15s"),
        },
        "time": [{"platform": "host", "id": "sntp_time"}],
        "sensor": _sensores(painel.get("sensor", [])),
        "globals": painel.get("globals", []),
        "script": _adaptar_http(painel.get("script", [])),
        "interval": painel.get("interval", []),
        "font": painel.get("font", []),
        "display": [
            {
                "platform": "sdl",
                "id": tela.get("id", "epaper_display"),
                "dimensions": {"width": LARGURA, "height": ALTURA},
                "auto_clear_enabled": False,
                "update_interval": ATUALIZACAO_JANELA,
                "lambda": lambda_sim,
            }
        ],
    }

    cabecalho = (
        "# GERADO por simulador/gerar.py a partir do painel.yaml. Não edite este arquivo.\n"
        "# Para mudar o layout, edite o painel.yaml e rode o simulador de novo.\n\n"
    )
    with open(DESTINO, "w", encoding="utf-8") as f:
        f.write(cabecalho)
        yaml.dump(sim, f, Dumper=_Dumper, allow_unicode=True, sort_keys=False, width=1000)
    return DESTINO


if __name__ == "__main__":
    print(gerar())
