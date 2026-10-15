#!/usr/bin/env python3
"""Guardião de Games — espera a área de trabalho e a TV ligarem antes de
iniciar automaticamente o jogo ativo do dia (útil no boot).

Um único .desktop na pasta vigiada é considerado "o jogo ativo". Se houver
mais de um, nada é iniciado (evita abrir o jogo errado).
"""

import os
import subprocess
import time


def env_path(var, default):
    return os.path.expanduser(os.environ.get(var, default))


AREA_DE_TRABALHO = env_path("GUARDIAO_AREA", "~/Desktop")

# Saída de vídeo que precisa estar conectada (a TV) para liberar o auto-start.
DISPLAY_TV = os.environ.get("GUARDIAO_DISPLAY", "HDMI-A-0")


def encontrar_jogo_ativo():
    """Procura arquivos .desktop diretamente na pasta vigiada.

    Subpastas são ignoradas. Zero ou mais de um .desktop => nenhum jogo.
    """
    try:
        arquivos = os.listdir(AREA_DE_TRABALHO)
    except OSError as erro:
        print(f"[GUARDIÃO] Erro ao acessar a pasta: {erro}")
        return None

    jogos = []

    for arquivo in arquivos:
        caminho = os.path.join(AREA_DE_TRABALHO, arquivo)
        if arquivo.lower().endswith(".desktop") and os.path.isfile(caminho):
            jogos.append(caminho)

    if len(jogos) == 1:
        return jogos[0]

    if len(jogos) > 1:
        print("[GUARDIÃO] Mais de um jogo encontrado:")
        for jogo in jogos:
            print(f"  - {jogo}")
        print("[GUARDIÃO] Nenhum jogo será iniciado.")
        return None

    return None


def processo_ativo(nome):
    """Verifica se existe um processo com o comm igual a `nome`."""
    try:
        for pid in os.listdir("/proc"):
            if not pid.isdigit():
                continue
            try:
                with open(f"/proc/{pid}/comm") as arquivo:
                    if arquivo.read().strip() == nome:
                        return True
            except OSError:
                continue
    except OSError:
        return False
    return False


def tv_conectada():
    """Verifica se a saída definida em GUARDIAO_DISPLAY está conectada."""
    try:
        resultado = subprocess.run(
            ["xrandr", "--query"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        for linha in resultado.stdout.splitlines():
            if linha.startswith(DISPLAY_TV) and "connected" in linha:
                return True
        return False
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def aguardar_tv(limite=60, intervalo=2):
    """Espera a TV ligar (display conectado) antes de iniciar o jogo.

    Evita que jogos com DX12/Vulkan crashem quando a TV está desligada na
    inicialização do PC.
    """
    if tv_conectada():
        return True

    print(f"[GUARDIÃO] TV não detectada ({DISPLAY_TV} disconnected). Aguardando...")

    inicio = time.time()
    while time.time() - inicio < limite:
        if tv_conectada():
            tempo = int(time.time() - inicio)
            print(f"[GUARDIÃO] TV conectada em {tempo}s.")
            return True
        time.sleep(intervalo)

    print(f"[GUARDIÃO] TV não ligou em {limite}s — abortando auto-start.")
    return False


def aguardar_area_de_trabalho(limite=15, intervalo=0.5):
    """Espera a área de trabalho (xfdesktop) carregar.

    Abandona a espera após `limite` segundos (timeout de segurança) para o
    Guardião nunca travar a inicialização.
    """
    inicio = time.time()
    while time.time() - inicio < limite:
        if processo_ativo("xfdesktop"):
            return True
        time.sleep(intervalo)
    return False


def iniciar_jogo():
    # Dá tempo para o XFCE terminar de carregar a sessão (espera inteligente:
    # encerra assim que a área de trabalho aparecer).
    if not aguardar_area_de_trabalho():
        print("[GUARDIÃO] Desktop não detectado em 15s — prosseguindo mesmo assim.")

    # Verifica se a TV está ligada antes de iniciar o jogo.
    if not aguardar_tv():
        print("[GUARDIÃO] Auto-start abortado — TV desligada.")
        return

    jogo = encontrar_jogo_ativo()

    if jogo is None:
        print("[GUARDIÃO] Nenhum jogo ativo encontrado.")
        return

    print(f"[GUARDIÃO] Jogo ativo encontrado: {jogo}")
    print("[GUARDIÃO] Iniciando...")

    subprocess.Popen(
        ["gio", "launch", jogo],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


if __name__ == "__main__":
    iniciar_jogo()
