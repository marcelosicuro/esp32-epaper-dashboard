# ESP32-C3 + Waveshare 7.5" V2 — Painel Pessoal

> Painel e-paper com clima, cotações e tarefas — totalmente independente. Sem Home Assistant, sem MQTT, sem servidor intermediário. O ESP32 busca os dados direto da internet.

![Painel em funcionamento](IMG_0528.png)

---

## O que exibe

| Seção | Conteúdo |
|---|---|
| Horário e data | NTP sincronizado, timezone configurável |
| Clima atual | Temperatura, sensação térmica, umidade, vento |
| Previsão | 3 dias com condição e min/máx |
| Tarefas | Até 3 tarefas de hoje via Todoist |
| Rodapé | USD/BRL, BTC/BRL e horário da última atualização |

---

## Hardware testado

| Item | Modelo |
|---|---|
| Microcontrolador | **Seeed XIAO ESP32-C3** |
| Display | **Waveshare 7.5" e-Paper V2** (800×480) |
| Alimentação | Carregador USB 5V/1A ou superior |

> **Importante:** use um carregador USB comum (500 mA+). A porta USB de notebooks pode não fornecer corrente suficiente durante a inicialização do Wi-Fi, causando reset em loop.

---

## Fiação — Seeed XIAO ESP32-C3 → Waveshare 7.5" V2

| Waveshare | XIAO ESP32-C3 | GPIO |
|---|---|---|
| VCC | 3.3V | — |
| GND | GND | — |
| DIN (MOSI) | D10 | GPIO10 |
| SCLK (CLK) | D8 | GPIO8 |
| CS | D1 | GPIO3 |
| DC | D3 | GPIO5 |
| RST | D0 | GPIO2 |
| BUSY | D2 | GPIO4 |

---

## Pré-requisitos

### 1. ESPHome

```bash
pip3 install esphome
```

### 2. Fontes Roboto

Coloque na pasta `fonts/`:
- `Roboto-Bold.ttf`
- `Roboto-Regular.ttf`
- `Roboto-Light.ttf`

```bash
cd fonts
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

Edite `secrets.yaml`:

```yaml
wifi_ssid: "Minha Rede"
wifi_password: "minha-senha"
ap_password: "painel1234"
api_key: "CHAVE_BASE64_32_BYTES="   # gerada abaixo
ota_password: "qualquer-senha"
todoist_token: ""                   # opcional — veja seção Tarefas
```

Gere a `api_key`:

```bash
python3 -c "import base64,os; print(base64.b64encode(os.urandom(32)).decode())"
```

### 2. Ajuste sua localização

No topo do `painel.yaml`:

```yaml
substitutions:
  latitude:  "-23.5505"
  longitude: "-46.6333"
  timezone:  "America/Sao_Paulo"
```

---

## Tarefas via Todoist (opcional)

1. Crie uma conta em [todoist.com](https://todoist.com) (gratuito)
2. Acesse **Settings → Integrations → Developer** e copie o API token
3. Adicione em `secrets.yaml`:

```yaml
todoist_token: "seu_token_aqui"
```

O painel exibe tarefas com vencimento para hoje ou atrasadas. Se o campo ficar vazio, a seção mostra "Nenhuma tarefa para hoje".

---

## Compilar e gravar

### Primeira vez (USB)

```bash
python3 -m esphome upload painel.yaml --device /dev/cu.usbmodem1101   # macOS
python3 -m esphome upload painel.yaml --device /dev/ttyUSB0           # Linux
```

### Atualizações seguintes (Wi-Fi, sem cabo)

```bash
python3 -m esphome upload painel.yaml --device painel-pessoal.local
```

---

## Como funciona

```
Boot
 └─ Conecta ao Wi-Fi
 └─ Sincroniza horário via NTP
 └─ Aguarda 12s → busca clima, cotações e tarefas
 └─ Desenha o painel no e-paper

A cada 60 segundos  → atualiza o display
A cada 20 minutos   → busca novos dados da internet
```

---

## Integrações

| Dado | API | Custo |
|---|---|---|
| Clima | [Open-Meteo](https://open-meteo.com/) | Gratuito, sem cadastro |
| Cotações | [AwesomeAPI](https://docs.awesomeapi.com.br/) | Gratuito, sem cadastro |
| Tarefas | [Todoist REST API v1](https://developer.todoist.com/rest/v1/) | Gratuito (plano pessoal) |

---

## Personalização

### Mudar frequência de atualização

```yaml
interval:
  - interval: 30min    # padrão: 20min
```

### Ajustar layout

O layout fica na seção `lambda:` do componente `display`. Consulte a [documentação do ESPHome Display](https://esphome.io/components/display/index.html).

---

## Troubleshooting

### Tela não atualiza / fica branca

- Verifique a fiação (especialmente DC e BUSY)
- Confirme `model: 7.5inV2rev2` no `painel.yaml`
- Habilite logs: `logger: level: DEBUG`

### Clima/cotações não carregam (ESPHome 2025.2.2)

O ESPHome 2025.2.2 tem um bug: APIs que usam `Transfer-Encoding: chunked` (sem `Content-Length`) resultam em body vazio. Open-Meteo e AwesomeAPI usam chunked.

**Fix:** aplique o patch nos dois arquivos do pacote instalado:

**`http_request.h`** — troque a linha com `max_length`:
```cpp
// De:
size_t max_length = std::min(content_length, this->max_response_buffer_size_);

// Para:
size_t max_length = content_length > 0
    ? std::min(content_length, this->max_response_buffer_size_)
    : this->max_response_buffer_size_;
```

E adicione `if (read <= 0) break;` dentro do loop de leitura, antes de `read_index += read`.

**`http_request_idf.cpp`** — troque a linha com `bufsize`:
```cpp
// De:
int bufsize = std::min(max_len, this->content_length - this->bytes_read_);

// Para:
int bufsize = this->content_length > 0
    ? (int)std::min(max_len, this->content_length - this->bytes_read_)
    : (int)max_len;
```

E troque `this->bytes_read_ += read_len;` por `if (read_len > 0) this->bytes_read_ += read_len;`.

Os arquivos ficam em:
```
$(python3 -c "import esphome; print(esphome.__path__[0])")/components/http_request/
```

### Device não responde na porta USB

O XIAO tem uma porta USB-C. Use um **carregador USB** para alimentação normal e o cabo USB-C de dados apenas para gravar o firmware. Notebook USB pode causar brownout durante a inicialização do Wi-Fi.

### Tarefas retornam erro 410

A API Todoist v2 (`/rest/v2/tasks`) foi depreciada. Use a v1 (`/api/v1/tasks`) — já configurada neste repositório.

---

## Licença

MIT — use, modifique e distribua à vontade.
