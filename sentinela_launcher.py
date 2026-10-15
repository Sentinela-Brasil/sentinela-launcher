#!/usr/bin/env python3
"""Sentinela Launcher — inicia um jogo (Wine/Proton via UMU, ou nativo no Cemu)
preparando o ambiente do projeto Sentinela (layer de FPS + coleta).

Uso:
    sentinela_launcher.py <jogo.exe|jogo.wux> [nome] [proton] [args...]

Todos os caminhos que apontavam para o autor agora vêm de variáveis de
ambiente, com um padrão sensato. Veja o README.
"""

import os
import shutil
import subprocess
import sys
import time


def env_path(var, default):
    """Lê `var` do ambiente, expande `~`; cai no `default` se ausente."""
    return os.path.expanduser(os.environ.get(var, default))


# ---------------------------------------------------------------
# CAMINHOS / CONFIGURAÇÃO (via ambiente)
# ---------------------------------------------------------------

UMU = env_path(
    "SENTINELA_UMU",
    "~/.local/share/lutris/runtime/umu/umu-run",
)

PREFIXO = env_path(
    "SENTINELA_WINEPREFIX",
    "~/.local/share/Steam/steamapps/compatdata/umu-default/pfx",
)

COMPATTOOLS = env_path(
    "SENTINELA_COMPATTOOLS",
    "~/.local/share/Steam/compatibilitytools.d",
)

PROTON_PADRAO = os.environ.get("SENTINELA_PROTON", "UMU-Proton-10.0-4")

# Layer de FPS do Sentinela (opcional). Se não existir, não é usada.
SENTINELA_FPS = os.environ.get("SENTINELA_FPS_DIR")

CEMU = env_path(
    "SENTINELA_CEMU",
    "~/.local/share/sentinela/Cemu.AppImage",
)

SENTINELA_GL_SRC = env_path(
    "SENTINELA_GL_LIB",
    "~/.local/share/sentinela/libSentinelaGL.so",
)

SENTINELA_GL_DEST = env_path(
    "SENTINELA_GL_DEST",
    "~/.local/lib/sentinela/libSentinelaGL.so",
)


def caminho_proton(nome):
    return os.path.join(COMPATTOOLS, nome)


# ---------------------------------------------------------------
# ARGUMENTO: JOGO
# ---------------------------------------------------------------

if len(sys.argv) > 1:
    JOGO = sys.argv[1]
else:
    print("[SENTINELA] Arraste um .exe sobre o launcher.")
    sys.exit(1)


# ---------------------------------------------------------------
# NOME DO JOGO
# ---------------------------------------------------------------

# 2º argumento opcional: identidade explícita do jogo fornecida pelo
# .desktop (Name=). Se vier, usamos ele (fonte confiável, sem adivinhar
# pelo nome do executável). Se não vier, derivamos do .exe.
if len(sys.argv) > 2 and sys.argv[2].strip():
    nome_jogo = sys.argv[2].strip()
else:
    nome_jogo = os.path.splitext(os.path.basename(JOGO))[0]


# ---------------------------------------------------------------
# PROTON DO JOGO
# ---------------------------------------------------------------

# Prioridade:
# 1. 3º argumento do .desktop (nome do Proton, override livre);
# 2. PROTON_PADRAO.
# O nome é resolvido para COMPATTOOLS em tempo de execução.
proton_nome = PROTON_PADRAO

if len(sys.argv) > 3 and sys.argv[3].strip():
    proton_nome = sys.argv[3].strip()

PROTON = caminho_proton(proton_nome)

if not os.path.isdir(PROTON):
    print("[SENTINELA] Aviso: Proton não encontrado:", proton_nome)
    print("[SENTINELA] Usando o padrão:", PROTON_PADRAO)
    proton_nome = PROTON_PADRAO
    PROTON = caminho_proton(proton_nome)


# ---------------------------------------------------------------
# JOGO NATIVO? (CEMU)
# ---------------------------------------------------------------

jogo_nativo = JOGO.lower().endswith((".wux", ".wud", ".wua"))


# ---------------------------------------------------------------
# AMBIENTE
# ---------------------------------------------------------------

env = os.environ.copy()

env["WINEPREFIX"] = PREFIXO
env["PROTONPATH"] = PROTON
env["GAME_NAME"] = nome_jogo
env["GAMEID"] = "umu-default"
env["PROTON_VERB"] = "waitforexitandrun"

# Força o Proton/Wine a carregar o dinput8.dll LOCAL (Mod Engine / tradução)
# em vez do builtin do Windows. Necessário para o mod de tradução PT-BR.
env["WINEDLLOVERRIDES"] = "dinput8=n,b"

# NOTA: env vars específicas de jogo ficam no .desktop, via prefixo
# /usr/bin/env na linha Exec= (ex.: PROTON_MEDIA_USE_GST=1). O Launcher
# apenas herda (os.environ.copy()). Correspondência por nome de jogo foi
# REMOVIDA de propósito: ela enganava (o RE8 se anuncia como "Resident
# Evil Village", que não casa com "re7") e vira código morto assim que o
# jogo é desinstalado.


# Argumentos extras por jogo (fixes de jogo, não escolha do usuário).
# Prioridade (igual ao Proton):
# 1. 4º+ argumentos do .desktop (override livre);
# 2. Padrão deste mapa (por nome do jogo).
# Exemplo: Rise of the Tomb Raider — -nolauncher pula o launcher pré-jogo.
ARGUMENTOS_PADRAO = {
    "rise of the tomb raider": ["-nolauncher"],
}

argumentos_jogo = sys.argv[4:]

if not argumentos_jogo:
    argumentos_jogo = list(ARGUMENTOS_PADRAO.get(nome_jogo.lower(), []))


# ---------------------------------------------------------------
# MANGOHUD
# ---------------------------------------------------------------

env["MANGOHUD"] = "0"


# ---------------------------------------------------------------
# SENTINELA FPS (opcional)
# ---------------------------------------------------------------

if SENTINELA_FPS and os.path.isdir(SENTINELA_FPS):
    env["VK_LAYER_PATH"] = SENTINELA_FPS
    env["VK_INSTANCE_LAYERS"] = "VK_LAYER_SENTINELA_fps"


# ---------------------------------------------------------------
# SENTINELA GL (OPENGL NATIVO)
# ---------------------------------------------------------------

if jogo_nativo:
    os.makedirs(os.path.dirname(SENTINELA_GL_DEST), exist_ok=True)
    shutil.copy2(SENTINELA_GL_SRC, SENTINELA_GL_DEST)
    env["LD_PRELOAD"] = SENTINELA_GL_DEST


# ---------------------------------------------------------------
# LIMPAR FPS ANTIGO
# ---------------------------------------------------------------

for arquivo in ("/tmp/sentinela-fps", "/tmp/sentinela-frames"):
    try:
        os.remove(arquivo)
    except FileNotFoundError:
        pass


# ---------------------------------------------------------------
# PRESSURE VESSEL / VULKAN
# ---------------------------------------------------------------

env["STEAM_RUNTIME_PREFER_HOST_LIBRARIES"] = "1"
env["PRESSURE_VESSEL_IMPORT_VARS"] = "1"
env["PRESSURE_VESSEL_FILESYSTEMS_RO"] = "/usr:/usr"
env["LIBGL_DRIVERS_PATH"] = "/usr/lib/dri:/usr/lib64/dri"
env["DRI_PRIME"] = "0"


# ---------------------------------------------------------------
# DIRETÓRIO DO JOGO
# ---------------------------------------------------------------

diretorio_jogo = os.path.dirname(JOGO)


# ---------------------------------------------------------------
# INFORMAÇÕES
# ---------------------------------------------------------------

print("[SENTINELA] Preparando ambiente...")
print("[SENTINELA] Jogo:", JOGO)
print("[SENTINELA] Nome:", nome_jogo)
print("[SENTINELA] UMU:", UMU)
print("[SENTINELA] Proton:", PROTON)
print("[SENTINELA] Proton (nome):", proton_nome)

if SENTINELA_FPS and os.path.isdir(SENTINELA_FPS):
    print("[SENTINELA] Layer FPS:", SENTINELA_FPS)

if jogo_nativo:
    print("[SENTINELA] Coletor GL nativo:", SENTINELA_GL_DEST)


# ---------------------------------------------------------------
# VERIFICAR SUPER SENTINELA
# ---------------------------------------------------------------

print("[SENTINELA] Verificando Sentinela...")

resultado = subprocess.run(
    ["systemctl", "--user", "is-active", "--quiet", "sentinela"]
)

if resultado.returncode != 0:
    print("[SENTINELA] Iniciando Sentinela...")
    subprocess.run(
        ["systemctl", "--user", "start", "sentinela"],
        check=False,
    )
    time.sleep(1)
else:
    print("[SENTINELA] Sentinela já está ativo.")


# ---------------------------------------------------------------
# INICIAR JOGO
# ---------------------------------------------------------------

if jogo_nativo:
    print("[SENTINELA] Iniciando Cemu (OpenGL nativo)...")
    processo = subprocess.Popen(
        [CEMU, "-g", JOGO],
        env=env,
        cwd=diretorio_jogo,
    )
else:
    print("[SENTINELA] Iniciando jogo...")
    processo = subprocess.Popen(
        [UMU, JOGO] + argumentos_jogo,
        env=env,
        cwd=diretorio_jogo,
    )

print("[SENTINELA] Jogo iniciado PID:", processo.pid)
print("[SENTINELA] Launcher finalizado.")
