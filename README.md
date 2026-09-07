# Polytes

<div align="center">

**Um "pet" de desktop vivo, não scriptado**

![Python](https://img.shields.io/badge/Python-3-3776AB?style=flat&logo=python&logoColor=white)
![PyQt5](https://img.shields.io/badge/PyQt5-Desktop-41CD52?style=flat&logo=qt&logoColor=white)
![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow?style=flat)
![License](https://img.shields.io/badge/license-GPLv3-blue?style=flat)

[**Página no itch.io**](https://foxcuukinho.itch.io/polytes)

</div>

---

> 🚧 **Projeto em desenvolvimento ativo.** O código aqui muda com frequência e ainda não há um lançamento oficial. Em breve o Polytes será lançado no [itch.io](https://foxcuukinho.itch.io/polytes), com build compilada e pronta pra uso (executável) para **Windows** e **Linux** — sem precisar instalar Python ou dependências manualmente. Este repositório é o código-fonte do projeto.
>
> Esta é a **V1**: o cérebro (Utility AI) e a animação ainda são bem simples de propósito. Não espere um stickman no nível do *Animator vs. Animation* — o movimento é procedural e ainda tem arestas pra lixar. Mais comportamentos e polish estão a caminho.

> ⚠️ **Aviso de build (setembro/2026):** os commits do dia 6 de setembro estão defeituosos para build — a versão compilada para Windows está apresentando um crash ao criar um stickman. Alguns polishs planejados também ficaram de fora dessa leva de commits. **No momento não há nenhuma build disponível no itch.io** (nem `.exe`, nem AppImage, nem `.deb`) — a página existe, mas sem downloads publicados ainda. A build real sai daqui algum tempo. Até lá, quem quiser testar precisa rodar direto pelo código-fonte via `python main.py`.

---

## O que é

**Polytes** é um pet de desktop: bonecos-palito (stickmen) que vivem soltos na sua tela, com física de verdade, personalidade gerada proceduralmente e comportamento emergente — não scriptado. Cada stickman decide sozinho se vai ficar parado ou andar, baseado em traços de personalidade e necessidades internas que mudam com o tempo.

O objetivo da V1 não é só "provar o conceito" — é já entregar a sensação de um **ser físico de verdade**, não um shimeji parado na tela.

Você pode arrastar o stickman pelo corpo, soltar ele em movimento e ele reage como um boneco de pano (ragdoll), quicando nas bordas da tela.

O projeto é inspirado na série **Animator vs. Animation**, e construído do zero em Python.

---

## Como funciona

```
Criador de stickman (nome, cor, cabeça oca/cheia)
              ↓
Nome → seed determinística (SHA-256) → traits de personalidade
              ↓
   energy (0-100)         curiosity (0-100)
              ↓
        StickmanNeeds (stamina, boredom mudam com o tempo)
              ↓
        StickmanBrain (Utility AI decide IDLE ou WALK)
              ↓
   StickmanPhysics (gravidade, colisão, movimento, ragdoll)
              ↓
   StickmanAnimator (animação procedural, IK/FK, interpolação)
              ↓
        draw_stickman (desenho na janela overlay transparente)
```

Cada stickman é desenhado numa janela `PyQt5` transparente e sem bordas, cobrindo a tela inteira, com uma máscara (`QRegion`) recalculada a cada frame — só a "silhueta" do boneco é clicável/visível, o resto da janela é invisível.

No Linux, a janela também recebe hints EWMH via X11 (`_NET_WM_STATE_ABOVE`, `SKIP_TASKBAR`, `SKIP_PAGER` e window type `DOCK`), fazendo o stickman ficar sempre visível por cima de outras janelas, sumir do Alt-Tab/taskbar e sobreviver ao "mostrar área de trabalho" (Win+D / Super+D). Testado em GNOME e KDE.

---

## Principais sistemas

| Sistema | Descrição |
|---|---|
| **Personalidade procedural** | Nome vira seed via `hashlib.sha256`; `random.Random(seed)` isolado gera `energy`/`curiosity`; cabeça oca e cor (matiz) aplicam buffs nos traits |
| **Necessidades dinâmicas** | `stamina` e `boredom` sobem/descem por frame dependendo do estado atual, modulados por `curiosity`/`energy` |
| **Utility AI** | `StickmanBrain` soma "utilidades" de 4 fatores pra decidir entre `IDLE` e `WALK`, com cooldown/histerese pra evitar troca de estado a cada frame |
| **Animação procedural (FK)** | Sistema de juntas genérico via `RIG` (`rig.py`), com interpolação linear entre frames pra evitar animação "travada" |
| **Ragdoll físico (Verlet/Jakobsen)** | Ao ser arrastado e solto, o corpo vira pontos físicos (`RagPoint`) conectados por constraints de distância (`solve_bone`) — inércia real, arremesso e quique nas bordas da tela |
| **Colisão com janelas do sistema** | Via `pywinctl`: o stickman pousa em cima de janelas reais, reage a colisão lateral/topo/base, e sai andando de cima delas de volta pro chão real |
| **Overlay fullscreen + máscara** | Janela cobre a tela inteira desde o início (nunca redimensiona), só a máscara (`setMask`) muda por frame — evita artefatos visuais de composição do Qt |
| **Always-on-top via X11** | Hints EWMH (`ABOVE`, `SKIP_TASKBAR`, `SKIP_PAGER`, window type `DOCK`) fazem o stickman ficar sempre visível, sumir do Alt-Tab e sobreviver ao "mostrar área de trabalho" |
| **Ghost process** | Cada stickman tem um processo do sistema operacional próprio (nomeado, visível no gerenciador de tarefas); matar esse processo deleta o stickman de verdade |

---

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3 |
| UI / Janela | PyQt5 (`QWidget`, `QPainter`, `QTimer`, `QRegion`) |
| Física | Verlet integration / Jakobsen constraints, implementação própria |
| Colisão com janelas do sistema | `pywinctl` |
| Always-on-top (Linux) | `python-xlib` (hints EWMH) |
| IDE | VS Code + Pylance |

---

## Estrutura do projeto

```
Polytes/
├── main.py                      # Ponto de entrada
├── stickman.py                  # Classe Stickman (dados)
│
├── Animation/
│   ├── animations.py            # Frames de IDLE / WALK
│   ├── stickman_animator.py     # Interpolação e ciclo de animação
│   ├── rig.py                   # Definição das juntas (RIG)
│   └── draw_stickman.py         # Desenho do stickman na tela
│
├── Body/
│   └── body_physics.py          # FK (calculate_joints) + Ragdoll (RagPoint, solve_bone, solve_body)
│
├── Brain/
│   ├── stickman_personality.py  # Geração procedural de personalidade
│   ├── stickman_needs.py        # Stamina / boredom
│   └── stickman_brain.py        # Utility AI (decisão de estado)
│
├── CreatorWindow/
│   ├── creator_window.py        # Janela de criação (nome, cor, cabeça)
│   ├── preview_widget.py        # Preview do stickman no editor
│   └── widgets.py               # Widgets customizados (ex: ToggleSwitch)
│
├── Simulation/
│   ├── simulation.py            # QTimer principal, loop de update
│   ├── stickman_manager.py      # Coordena todos os stickmen ativos
│   ├── stickman_ghost_process.py # Processo associado ao stickman
│   ├── stickman_overlay.py      # Janela transparente + eventos de mouse
│   ├── stickman_physics.py      # Gravidade, colisão, movimento
│   └── stickman_ragdoll.py      # Lógica de ragdoll e colisão com janelas
│
└── Utils/
    ├── constants.py              # Constantes globais do projeto
    ├── helpers.py                # Geometria, colisões, hash, seed, polar_point
    └── x11_hints.py               # Hints EWMH (always-on-top, dock, skip taskbar/pager)
```

---

## Rodando o projeto

### Pré-requisitos

- Python 3.x
- PyQt5
- `python-xlib` (Linux, necessário só pro always-on-top via X11)

```bash
pip install -r requirements.txt
```

### Executar

```bash
python main.py
```

Isso abre a janela **Criador de stickman**: escolha um nome, uma cor e se a cabeça é oca ou cheia, clique em **Criar Stickman** e ele aparece na tela.

### Interagindo

- **Clique e arraste** qualquer parte do corpo do stickman pra manipulá-lo como um boneco de pano
- **Solte em movimento** pra ver o arremesso com inércia
- O stickman quica nas bordas da tela e reage a colisão com janelas reais enquanto está "voando" (`flying`)
- Solto, ele volta a andar/ficar parado sozinho, de acordo com a personalidade dele
- Pra deletar um stickman, encerre o processo correspondente a ele no gerenciador de tarefas do sistema

---

## Escopo da V1

**Dentro do escopo:**
- Física de mundo (gravidade, chão, bordas de tela, colisão com janelas do sistema)
- Personalidade procedural a partir do nome
- Necessidades dinâmicas (stamina, boredom) influenciando decisões
- Utility AI simples (IDLE / WALK)
- Movimento horizontal real até um alvo escolhido
- Desenho procedural via sistema de juntas (RIG)
- Animação com interpolação entre frames
- Editor mínimo de criação (nome, cor, cabeça oca/cheia)
- Ragdoll físico completo: arrasto, arremesso com inércia, quique nas bordas e em janelas
- Always-on-top real via X11 (Linux)
- Ghost process (deletar stickman via gerenciador de tarefas)

**Fora do escopo da V1** (planejado ou considerado pra V1.x/V2):
- Colisão entre múltiplos stickmen
- Auto-colisão do corpo
- Escalar/subir em janelas do sistema ativamente
- IA hierárquica de objetivos (`GO_TO_WINDOW`, submissões)
- Persistência em disco, drift de personalidade de longo prazo
- Squash/stretch e animações mais refinadas
- Seletor de cor customizado (barras Hue/Saturação) — V1 usa um color picker próprio, ver `color_picker.py`
- Formato de arquivo próprio (`.stickfigure`), hub de compartilhamento, presets múltiplos de andar
- Always-on-top em Wayland (limitação conhecida — hints EWMH não se aplicam fora do X11)

---

## Status & lançamento

- 🚧 **Em desenvolvimento** — todos os sistemas centrais da V1 estão implementados, mas a build ainda não foi publicada (ver aviso no topo)
- 📦 Lançamento planejado no [**itch.io**](https://foxcuukinho.itch.io/polytes), com build compilada (executável) pra **Windows** e **Linux**
- Até lá, rodar via `python main.py` é a única forma de usar

## Licença

O código do Polytes é licenciado sob **GPL v3**. Isso significa que qualquer versão modificada distribuída (mesmo comercialmente) precisa continuar com o código-fonte aberto sob a mesma licença, e manter os créditos de autoria original.

> **Sobre o nome:** "Polytes" é o nome/marca deste projeto especificamente. Forks e versões modificadas são bem-vindos sob os termos da GPL v3, mas não podem se apresentar como "Polytes" oficial nem usar o nome como se fossem a versão original — use um nome diferente pro seu fork.