#!/usr/bin/env python3
"""Gera simulador.yaml a partir do painel.yaml.

Reaproveita globals, scripts, fontes e o lambda da tela do painel.yaml e troca só
o hardware (e-Paper -> janela SDL 800x480 com tinta preta/papel branco).
Edite a tela no painel.yaml; o simulador sempre reflete o que está lá.
"""
import re
from pathlib import Path

base = Path(__file__).parent
texto = (base / "painel.yaml").read_text()

secoes, atual = {}, None
for linha in texto.splitlines():
    m = re.match(r"^([a-z_0-9]+):", linha)
    if m:
        atual = m.group(1)
        secoes[atual] = []
    if atual:
        secoes[atual].append(linha)

def indent(l):
    return len(l) - len(l.lstrip())

def troca_http(linhas):
    """Troca cada `- http_request.get:` por um lambda que usa curl."""
    out, i = [], 0
    while i < len(linhas):
        l = linhas[i]
        if l.strip() != "- http_request.get:":
            out.append(l); i += 1; continue
        base_ind = indent(l)
        j = i + 1
        while j < len(linhas) and (not linhas[j].strip() or indent(linhas[j]) > base_ind):
            j += 1
        bl = linhas[i + 1:j]
        url = next(x.split("url:", 1)[1].strip().strip('"') for x in bl if x.strip().startswith("url:"))
        k = next(n for n, x in enumerate(bl) if x.strip() == "- lambda: |-")
        lam_ind = indent(bl[k + 1])
        corpo = []
        for x in bl[k + 1:]:
            if x.strip() and indent(x) < lam_ind:
                break
            corpo.append(x)
        pad = " " * lam_ind
        out.append(" " * base_ind + "- lambda: |-")
        out.append(pad + "int http_status = 0;")
        out.append(pad + f'std::string body = sim_http_get("{url}", &http_status);')
        out.append(pad + "struct { int status_code; } resp_s{http_status};")
        out.append(pad + "auto *response = &resp_s;")
        out.extend(corpo)
        i = j
    return out

def bloco(nome):
    return "\n".join(secoes[nome])

# lambda da tela = corpo depois de "lambda: |-" na seção display
disp = secoes["display"]
i = next(n for n, l in enumerate(disp) if l.strip().startswith("lambda:"))
corpo = disp[i + 1:]
corpo_ind = indent(next(l for l in corpo if l.strip()))
pad = " " * corpo_ind
lambda_tela = "\n".join(
    ["    lambda: |-",
     pad + "it.fill(esphome::Color(255, 255, 255));",
     pad + "EpPreview real{it};",
     pad + "[&](EpPreview &it) {"]
    + corpo
    + [pad + "}(real);"]
)

out = f"""# GERADO por gerar_simulador.py a partir do painel.yaml — não edite aqui.
{bloco("substitutions")}

esphome:
  name: simulador-painel
  includes:
    - sim_http.h
    - sim_epaper.h
  on_boot:
    priority: -100
    then:
      - delay: 2s
      - script.execute: fetch_all

host:

logger:
  level: INFO

json:

time:
  - platform: host
    id: sntp_time

interval:
  - interval: 20min
    then:
      - script.execute: fetch_all

# sensores do hardware simulados com valores fixos
sensor:
  - platform: template
    id: cpu_temp_sensor
    lambda: 'return 42.0;'
  - platform: template
    id: wifi_rssi_sensor
    lambda: 'return -58.0;'
  - platform: uptime
    id: uptime_sensor
    unit_of_measurement: "s"

{bloco("globals")}

{chr(10).join(troca_http(secoes["script"]))}

{bloco("font")}

display:
  - platform: sdl
    id: epaper_display
    dimensions:
      width: 800
      height: 480
    update_interval: 60s
{lambda_tela}
"""
(base / "simulador.yaml").write_text(out)
print("simulador.yaml gerado")
