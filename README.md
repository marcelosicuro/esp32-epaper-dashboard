# ESP32-C3 + Waveshare 7.5" V2 — Painel Pessoal (sem Home Assistant)

> Painel de clima e horário para e-paper, totalmente independente. Sem Home Assistant, sem MQTT, sem servidor intermediário — o ESP32 busca os dados direto da internet.

![layout do painel](docs/preview.png)

---

## Por que este projeto existe?

Montar um ESP32 com tela e-paper é mais difícil do que deveria ser. A maioria dos tutoriais exige Home Assistant, MQTT ou algum servidor rodando na rede. Este projeto não precisa de nada disso.

**O que roda aqui:**
- Horário sincronizado via NTP (pool.ntp.org)
- Clima via [Open-Meteo](https://open-meteo.com/) — API gratuita, sem cadastro, sem API key
- Firmware gerado pelo [ESPHome](https://esphome.io/) — atualizável pelo Wi-Fi (OTA)

---

## Hardware

| Item | Modelo testado |
|---|---|
| Microcontrolador | ESP32-C3 (qualquer variante com Wi-Fi) |
| Display | Waveshare 7.5" e-Paper V2 (800×480) |
| Alimentação | USB 5V ou 3.3V externo |

Outros modelos Waveshare provavelmente funcionam — veja a seção [Outros modelos de display](#outros-modelos-de-display).

---

## Fiação — ESP32-C3 → Waveshare 7.5" V2

| Pino do Waveshare HAT | Pino ESP32-C3 | Observação |
|---|---|---|
| VCC | 3.3V | **Não use 5V** |
| GND | GND | |
| DIN (MOSI) | GPIO7 | SPI2 MOSI |
| SCLK | GPIO6 | SPI2 CLK |
| CS | GPIO2 | Chip Select |
| DC | GPIO4 | Data/Command |
| RST | GPIO5 | Reset |
| BUSY | GPIO3 | Espera refresh |

> Se você comprou um kit diferente (ex: ESP32 S2, S3, ou placa Waveshare com ESP32 integrado), confira os pinos no `painel.yaml` — eles ficam na seção `substitutions` no topo do arquivo.

---

## Pré-requisitos

### 1. Instalar ESPHome

```bash
pip3 install esphome
```

Ou via Docker:

```bash
docker run --rm -v "${PWD}":/config -it ghcr.io/esphome/esphome compile painel.yaml
```

### 2. Baixar as fontes

Coloque estes arquivos na pasta `fonts/`:

- `Roboto-Bold.ttf`
- `Roboto-Regular.ttf`
- `Roboto-Light.ttf`

Download rápido:

```bash
cd fonts
# pacote completo do Google Fonts
curl -L "https://fonts.google.com/download?family=Roboto" -o roboto.zip
unzip roboto.zip "Roboto/static/Roboto-Bold.ttf" "Roboto/static/Roboto-Regular.ttf" "Roboto/static/Roboto-Light.ttf" -d .
mv Roboto/static/*.ttf . && rm -rf Roboto roboto.zip
```

---

## Configuração

### 1. Crie o arquivo de segredos

```bash
cp secrets.yaml.example secrets.yaml
```

Edite o `secrets.yaml` com seu Wi-Fi e as chaves geradas:

```yaml
wifi_ssid: "Minha Rede"
wifi_password: "minha-senha"
ap_password: "painel1234"
api_key: "CHAVE_BASE64_32_BYTES="
ota_password: "qualquer-senha"
```

Gere a `api_key`:

```bash
python3 -c "import base64,os; print(base64.b64encode(os.urandom(32)).decode())"
```

### 2. Ajuste sua localização

No topo do `painel.yaml`, edite:

```yaml
substitutions:
  latitude: "-23.5505"    # sua latitude
  longitude: "-46.6333"   # sua longitude
  timezone: "America/Sao_Paulo"
```

Encontre latitude e longitude da sua cidade em: https://latlong.net

---

## Compilar e gravar

### Primeira vez (cabo USB)

```bash
esphome run painel.yaml
```

O ESPHome detecta a porta serial automaticamente. Se não detectar, passe manualmente:

```bash
esphome run painel.yaml --device /dev/cu.usbmodem1101   # macOS
esphome run painel.yaml --device /dev/ttyUSB0           # Linux
```

### Atualizações seguintes (Wi-Fi, sem cabo)

```bash
esphome run painel.yaml
```

O ESPHome usa OTA automaticamente se o dispositivo já estiver na rede.

---

## Como funciona

```
Boot
 └─ Conecta ao Wi-Fi
 └─ Sincroniza horário via NTP
 └─ Aguarda 10s → busca clima no Open-Meteo
 └─ Desenha o painel no e-paper

A cada 1 minuto  → atualiza o relógio no display
A cada 20 minutos → busca novo clima e redesenha
```

O display e-paper **não precisa de energia para manter a imagem** — ideal para deixar ligado 24h com consumo mínimo.

---

## Personalização

### Mudar cidade

```yaml
substitutions:
  latitude: "-22.9068"   # Rio de Janeiro
  longitude: "-43.1729"
  timezone: "America/Sao_Paulo"
```

### Mudar frequência de atualização do clima

```yaml
interval:
  - interval: 30min    # era 20min
```

### Adicionar mais informações no display

O layout fica na seção `lambda:` do display. Consulte a [documentação do ESPHome Display](https://esphome.io/components/display/index.html).

### Outros modelos de display

Troque o `model:` na seção `display:`:

| Display | `model:` |
|---|---|
| 7.5" V2 (este projeto) | `7.50inV2` |
| 4.2" | `4.20in` |
| 2.9" | `2.90in` |
| 2.13" | `2.13in` |

Veja todos os modelos: https://esphome.io/components/display/waveshare_epaper.html

---

## Troubleshooting

### Tela fica branca / não atualiza

- Verifique a fiação (especialmente DC e BUSY)
- Confirme o modelo correto em `model:`
- Habilite logs: `logger: level: DEBUG` e veja a saída serial

### Clima não carrega

- Confirme que o ESP está conectado ao Wi-Fi (acesse `http://<IP>` no navegador)
- Teste a URL do clima no seu navegador: `https://api.open-meteo.com/v1/forecast?latitude=-23.55&longitude=-46.63&current=temperature_2m`

### Não encontra a porta serial no macOS

```bash
ls /dev/cu.*
# Instale o driver se necessário:
# CH340: https://www.wch-ic.com/downloads/CH341SER_MAC_ZIP.html
# CP2102: https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers
```

---

## Licença

MIT — use, modifique e distribua à vontade.

---

## Contribuindo

Issues e PRs são bem-vindos. Se você adaptou para outro hardware ou adicionou novos dados ao painel, compartilhe!
