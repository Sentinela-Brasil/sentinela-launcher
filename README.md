# Sentinela Launcher

> **In English:** A lightweight Python launcher for managing Proton/UMU and Cemu
> game execution on Linux, with configurable paths and optional integration with the
> Sentinela environment. Designed to keep system-specific configuration separate from
> the launcher code, making the project easier to adapt to other Linux installations.
> *Documentation: Portuguese (Brazilian).*

Launcher de jogos para Linux (X11) focado em **integrar com o projeto Sentinela**:
prepara o ambiente do Wine/Proton (via [UMU](https://github.com/Open-Wine-Components/umu-launcher))
ou do Cemu (nativo), liga a camada de coleta de FPS e inicia o jogo.

Surgiu como a peça que faltava para o Sentinela "saber" que um jogo começou — sem
ele, o coletor não tem como ligar sozinho no arranque de cada jogo.

## Componentes

| Arquivo | Papel |
|---|---|
| `sentinela_launcher.py` | O launcher: monta o `env` e inicia o jogo. |
| `guardiao_games.py` | Auto-start no boot: espera o desktop e a TV antes de abrir o jogo do dia. |

Sem dependências externas — só a biblioteca padrão do Python 3.

## Requisitos e dependências

**Básicos (para rodar o launcher):**

- Linux com **X11** (testado no Fedora 44 / Xfce)
- Python 3 (apenas a biblioteca padrão)

**Da execução (dependem do modo):**

- Modo Windows/Proton: [UMU](https://github.com/Open-Wine-Components/umu-launcher)
  + um Proton instalado
- Modo nativo (Cemu): o AppImage do Cemu (ver `SENTINELA_CEMU`)
- `guardiao_games.py`: `xrandr`, `xfdesktop` e `gio`

**Integrações opcionais (NÃO vêm no clone):**

Clonar o repositório **não** instala nem disponibiliza estes componentes — eles
fazem parte do ambiente Sentinela ou da tua máquina. O launcher **degrada sem
bloquear** quando faltam:

- **Layer de FPS** (`SENTINELA_FPS_DIR`): só é ativada se a pasta existir; se não
  existir, é simplesmente ignorada e o jogo roda sem a coleta de FPS.
- **Serviço `systemd --user` `sentinela`**: se não existir ou falhar ao iniciar, o
  launcher **segue e inicia o jogo normalmente**. A chamada de start usa `check=False`
  e nada no fluxo depende do resultado dela.

## Uso

```sh
# Windows/Proton via UMU
./sentinela_launcher.py "/caminho/Jogo.exe"

# com identidade explícita (vinda do .desktop, Name=)
./sentinela_launcher.py "/caminho/Jogo.exe" "Nome do Jogo"

# escolhendo o Proton + argumentos extra
./sentinela_launcher.py "/caminho/Jogo.exe" "Nome" "GE-Proton9-27" --algum-arg

# jogo nativo (Cemu) — extensões .wux / .wud / .wua
./sentinela_launcher.py "/caminho/jogo.wux"
```

Posição dos argumentos: **1º** jogo · **2º** nome (opcional) · **3º** Proton (opcional)
· **4º+** argumentos repassados ao jogo.

Se o Proton pedido não existir, o launcher avisa e cai no padrão.

## Variáveis de ambiente (launcher)

Nenhum caminho pessoal fica chumbado no código: tudo tem padrão e pode ser trocado
por variável de ambiente.

| Variável | Padrão | Para quê |
|---|---|---|
| `SENTINELA_UMU` | `~/.local/share/lutris/runtime/umu/umu-run` | binário do UMU |
| `SENTINELA_WINEPREFIX` | `~/.local/share/Steam/steamapps/compatdata/umu-default/pfx` | `WINEPREFIX` |
| `SENTINELA_COMPATTOOLS` | `~/.local/share/Steam/compatibilitytools.d` | pasta dos Protons |
| `SENTINELA_PROTON` | `UMU-Proton-10.0-4` | Proton padrão |
| `SENTINELA_FPS_DIR` | _(vazio)_ | pasta da camada Vulkan de FPS (se não existir, é ignorada) |
| `SENTINELA_CEMU` | `~/.local/share/sentinela/Cemu.AppImage` | AppImage do Cemu |
| `SENTINELA_GL_LIB` | `~/.local/share/sentinela/libSentinelaGL.so` | lib do coletor OpenGL (nativos) |
| `SENTINELA_GL_DEST` | `~/.local/lib/sentinela/libSentinelaGL.so` | destino do `LD_PRELOAD` |

### Exemplo de `.desktop`

Variáveis específicas do jogo vão na linha `Exec=`, **com prefixo `/usr/bin/env`**
(o campo `Env=` do padrão é ignorado pelo Xfce/GIO):

```ini
[Desktop Entry]
Type=Application
Name=Nome do Jogo
Exec=/usr/bin/env PROTON_MEDIA_USE_GST=1 /home/USUARIO/sentinela-launcher/sentinela_launcher.py "/caminho/Jogo.exe" "Nome do Jogo"
Terminal=false
```

> No exemplo, `/home/USUARIO/sentinela-launcher/...` é **ilustrativo**: troca pelo
> caminho onde clonaste o repositório.

## Guardião (`guardiao_games.py`)

Espera inteligente no boot: aguarda a área de trabalho subir (`xfdesktop`) e a **TV
ligar** antes de abrir o jogo .desktop que estiver na pasta vigiada. Se houver mais
de um `.desktop`, não abre nada (evita iniciar o jogo errado). O motivo do "esperar a
TV" é evitar crash de jogos DX12/Vulkan quando o monitor/TV ainda está desligado.

| Variável | Padrão | Para quê |
|---|---|---|
| `GUARDIAO_AREA` | `~/Desktop` | pasta com o(s) `.desktop` de jogos |
| `GUARDIAO_DISPLAY` | `HDMI-A-0` | saída de vídeo que precisa estar conectada |

## Licença

MIT — veja [LICENSE](LICENSE).
