#!/usr/bin/env python3
"""
Roda o painel numa janela no Mac e recarrega sozinho quando você salva o painel.yaml.

    simulador/rodar.sh              # gera, compila, abre a janela e fica observando
    simulador/rodar.sh --so-gerar   # só gera o painel-sim.generated.yaml
    simulador/rodar.sh --uma-vez    # roda uma vez, sem observar mudanças
"""

import argparse
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

import gerar

RAIZ = gerar.RAIZ
OBSERVAR = [gerar.ORIGEM, RAIZ / "simulador" / "epaper_view.h", RAIZ / "simulador" / "gerar.py"]


def comando_esphome() -> list[str]:
    venv = RAIZ / ".venv-sim" / "bin" / "esphome"
    if venv.exists():
        return [str(venv)]
    achado = shutil.which("esphome")
    if achado:
        return [achado]
    sys.exit("ESPHome não encontrado. Rode simulador/instalar.sh primeiro.")


def assinatura() -> tuple:
    return tuple(p.stat().st_mtime_ns for p in OBSERVAR if p.exists())


def iniciar(esphome: list[str]) -> subprocess.Popen:
    destino = gerar.gerar()
    print(f"\n▶ Compilando e abrindo a janela ({time.strftime('%H:%M:%S')})...", flush=True)
    # Grupo próprio, para encerrar o esphome e a janela juntos.
    return subprocess.Popen([*esphome, "run", str(destino)], cwd=RAIZ, start_new_session=True)


def parar(proc: subprocess.Popen | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--so-gerar", action="store_true", help="apenas gera o YAML do simulador")
    ap.add_argument("--uma-vez", action="store_true", help="não observa mudanças no painel.yaml")
    args = ap.parse_args()

    if args.so_gerar:
        print(gerar.gerar())
        return 0

    # Fechar o terminal (SIGHUP) ou encerrar o processo (SIGTERM) também fecha a janela.
    def _sair(*_):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, _sair)
    signal.signal(signal.SIGHUP, _sair)

    esphome = comando_esphome()
    proc = iniciar(esphome)

    if args.uma_vez:
        try:
            return proc.wait()
        except KeyboardInterrupt:
            parar(proc)
            return 130

    visto = assinatura()
    avisou_fim = False
    print("Observando o painel.yaml. Salve para recarregar. Ctrl+C para sair.")
    try:
        while True:
            time.sleep(1)
            atual = assinatura()
            if atual != visto:
                visto = atual
                avisou_fim = False
                print("\n↻ Mudança detectada, recarregando...", flush=True)
                parar(proc)
                proc = iniciar(esphome)
            elif proc.poll() is not None and not avisou_fim:
                avisou_fim = True
                print(
                    f"\nO simulador terminou (código {proc.returncode}). "
                    "Corrija e salve o painel.yaml para tentar de novo, ou Ctrl+C para sair."
                )
    except KeyboardInterrupt:
        print("\nEncerrando.")
        parar(proc)
        return 0


if __name__ == "__main__":
    sys.exit(main())
