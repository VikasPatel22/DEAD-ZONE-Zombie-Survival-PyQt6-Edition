# 💀 DEAD ZONE — Zombie Survival (PyQt6 Edition)

A fully-featured top-down zombie wave defense game written in pure Python using PyQt6. Survive 20+ waves of increasingly brutal zombie hordes, manage resources, build barricades, and level up your survivor.

---

## 🎮 Features

### Gameplay
- **20+ Waves** of escalating zombie hordes with full scaling
- **8 Zombie Types**: Regular, Fast, Tank, Spitter, Exploder, Runner, Armored, Boss
- **Resource Management**: Ammo, Food, Wood, Medicine
- **Build System**: Place wooden barricades to defend positions (costs 🪵 10 wood)
- **Level-Up System**: Gain XP, increase damage (15%/level), max HP, unlock dual-shot
- **Rage Meter**: Builds on kills → speed boost + visual effect at 80%+
- **Grenade System**: Right-click to throw grenades with blast radius
- **Dash Ability**: Space bar dash with invincibility frames and cooldown

### Zombie Types
| Type       | Notes |
|------------|-------|
| Regular    | Standard zombie |
| Fast       | Low HP, high speed — harass you |
| Tank       | Massive HP, slow, huge damage |
| Spitter    | Ranged acid projectiles |
| Exploder   | Suicide bomber — triggers near player |
| Runner     | Faster than Fast, glass cannon |
| Armored    | Has armor HP shield before main HP |
| Boss       | Appears every 5 waves — massive stats |

### Difficulty Levels
| Difficulty | Description |
|------------|-------------|
| LOW        | Forgiving — ideal for learning |
| MED        | Balanced — recommended start |
| HARD       | Harder damage, faster spawns |
| EXTREME    | Resource-scarce, brutal |
| MAX        | Nightmare — for veterans only |

### Visual Features
- Smooth camera tracking with lerp
- Screen shake on hits, explosions, boss deaths
- Full particle system: blood, muzzle flash, explosions, smoke, level-up bursts
- Floating damage/pickup text
- Animated blood stains on the ground
- Minimap with zombie positions, pickups, barricades, viewport rect
- Pulsing boss warning
- Build mode ghost cursor
- Rage glow effect on player
- Dash trail effect
- Armor indicator on Armored zombies
- Barricade HP bars and wood-grain texture

### HUD
- Resource counters (top left)
- Wave indicator (top center) — boss wave warning
- Difficulty badge
- Kill count + score
- HP bar with color transition (green → yellow → red)
- Ammo display with visual clip indicator
- Reload progress bar
- XP bar
- Rage meter
- Grenade counter
- Dash cooldown indicator
- Mini help text (bottom left)
- Minimap (top right)

---

## 🕹️ Controls

| Key / Input | Action |
|-------------|--------|
| `WASD` / Arrow Keys | Move |
| `Mouse` | Aim |
| `Left Click` / Hold | Shoot / Auto-fire |
| `Right Click` | Throw grenade |
| `Space` | Dash (brief invincibility) |
| `H` | Use medicine (+45 HP) |
| `B` | Toggle build mode |
| `R` | Reload weapon |
| `Click` (build mode) | Place barricade (costs 🪵10) |

---

## 🚀 Installation

### Requirements
- Python 3.9+
- PyQt6

### Quick Start

```bash
# Clone or download the game files
# Then install dependencies:
pip install -r requirements.txt

# Run the game
python dead_zone.py
```

### On Linux (if needed)
```bash
pip install PyQt6 --break-system-packages
python dead_zone.py
```

### On macOS
```bash
pip3 install -r requirements.txt
python3 dead_zone.py
```

### On Windows
```bash
pip install -r requirements.txt
python dead_zone.py
```

---

## 📂 Files

```
dead_zone/
├── dead_zone.py        # Main game file — everything in one file
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

High scores are saved automatically to `~/.dead_zone_hs.csv`.

---

## 🧠 Architecture

The game is organized into clean layers:

- **`GameEngine`** — Pure logic: update loop, entity management, collision, wave spawning
- **`GameCanvas`** — PyQt6 widget: input handling, all rendering via `QPainter`
- **`StartScreen`** — Animated main menu with particle effects
- **`GameOverScreen`** — Results screen with persistent high score display
- **`MainWindow`** — QMainWindow with `QStackedWidget` managing all screens
- **`QTimer`** — Fixed 60 FPS game loop

### Key Design Choices
- All game state lives in `GameEngine` — rendering is stateless
- `QPainter` used directly with `QRadialGradient`, `QLinearGradient` for rich visuals
- Particles, float texts, blood stains are separate pools for performance
- Screen-to-world and world-to-screen transforms via simple math (no scene graph)
- Dataclasses for all entities (`Zombie`, `Bullet`, `Particle`, etc.)

---

## 🔮 Planned / Possible Extensions

- [ ] Sound effects (via `PyQt6.QtMultimedia`)
- [ ] More weapon types (shotgun, machine gun, sniper)
- [ ] Special abilities (nuke, turret placement)
- [ ] Day/night cycle visual mode
- [ ] Leaderboard with player names
- [ ] Pause menu
- [ ] Controller support

---

## 👤 Credits

Made with ❤️ by **Sagittarius1**  
Original web version: [sagittarius1.netlify.app](https://sagittarius1.netlify.app)  
PyQt6 port with extended features — 2024
