"""
DEAD ZONE — Zombie Survival Wave Defense
PyQt6 Edition with enhanced graphics, particle systems, and gameplay
"""

import sys
import math
import random
import csv
import os
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QStackedWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGraphicsDropShadowEffect, QSizePolicy
)
from PyQt6.QtCore import (
    Qt, QTimer, QPointF, QRectF, QSizeF,
    pyqtSignal, QPropertyAnimation, QEasingCurve,
    QSize, QRect
)
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QFontDatabase,
    QPen, QBrush, QRadialGradient, QLinearGradient,
    QPainterPath, QPolygonF, QPixmap, QConicalGradient,
    QKeyEvent, QMouseEvent, QWheelEvent, QPaintEvent,
    QTransform, QIcon, QPalette
)

# ─── CONSTANTS ───────────────────────────────────────────────────────────────
W_WORLD, H_WORLD = 2400, 2400
SCREEN_W, SCREEN_H = 1280, 800
FPS = 60

HIGH_SCORE_FILE = Path.home() / ".dead_zone_hs.csv"

# ─── COLORS ──────────────────────────────────────────────────────────────────
class C:
    BG          = QColor(10, 10, 8)
    RED         = QColor(220, 30, 30)
    RED_DIM     = QColor(140, 20, 20)
    GREEN       = QColor(60, 180, 60)
    GREEN_DIM   = QColor(30, 100, 30)
    YELLOW      = QColor(255, 200, 40)
    ORANGE      = QColor(255, 140, 20)
    CYAN        = QColor(0, 200, 220)
    WHITE       = QColor(255, 255, 255)
    GREY        = QColor(120, 120, 120)
    DARK        = QColor(20, 20, 16)
    BLOOD       = QColor(120, 0, 0)
    AMMO_CLR    = QColor(255, 220, 60)
    WOOD_CLR    = QColor(160, 100, 40)
    FOOD_CLR    = QColor(255, 140, 60)
    MED_CLR     = QColor(255, 80, 180)
    XP_CLR      = QColor(140, 120, 255)
    PURPLE      = QColor(180, 0, 255)
    TEAL        = QColor(0, 220, 200)

# ─── DIFFICULTY ──────────────────────────────────────────────────────────────
DIFFICULTIES = {
    "easy":    {"name":"LOW",     "z_spd":0.7,  "z_hp":0.7,  "z_dmg":0.6,  "spawn":0.7,  "res":1.5, "p_spd":3.2, "ammo":60, "med":4, "wood":40, "color":QColor(60,220,120)},
    "medium":  {"name":"MED",     "z_spd":1.0,  "z_hp":1.0,  "z_dmg":1.0,  "spawn":1.0,  "res":1.0, "p_spd":2.8, "ammo":30, "med":2, "wood":25, "color":QColor(255,180,0)},
    "hard":    {"name":"HARD",    "z_spd":1.3,  "z_hp":1.3,  "z_dmg":1.3,  "spawn":1.4,  "res":0.8, "p_spd":2.6, "ammo":20, "med":1, "wood":15, "color":QColor(255,100,0)},
    "extreme": {"name":"EXTREME", "z_spd":1.7,  "z_hp":1.6,  "z_dmg":1.6,  "spawn":1.8,  "res":0.6, "p_spd":2.5, "ammo":15, "med":1, "wood":10, "color":QColor(255,40,0)},
    "max":     {"name":"MAX",     "z_spd":2.2,  "z_hp":2.0,  "z_dmg":2.0,  "spawn":2.4,  "res":0.4, "p_spd":2.4, "ammo":10, "med":0, "wood":5,  "color":QColor(200,0,255)},
}

# ─── ZOMBIE TEMPLATES ────────────────────────────────────────────────────────
ZT = {
    "regular": {"spd":0.85, "hp":40,  "dmg":8,  "r":13, "c0":"#5a8030","c1":"#304020","xp":15,"score":25},
    "fast":    {"spd":1.9,  "hp":22,  "dmg":5,  "r":9,  "c0":"#b07030","c1":"#704010","xp":12,"score":40},
    "tank":    {"spd":0.38, "hp":200, "dmg":20, "r":22, "c0":"#507050","c1":"#304035","xp":50,"score":150},
    "spitter": {"spd":1.1,  "hp":55,  "dmg":6,  "r":11, "c0":"#20aa20","c1":"#106010","xp":20,"score":60, "ranged":True},
    "exploder":{"spd":1.4,  "hp":35,  "dmg":0,  "r":15, "c0":"#aa4400","c1":"#661100","xp":25,"score":80, "explosive":True},
    "boss":    {"spd":0.55, "hp":600, "dmg":25, "r":32, "c0":"#880000","c1":"#440000","xp":120,"score":500,"is_boss":True},
    "runner":  {"spd":2.5,  "hp":18,  "dmg":3,  "r":8,  "c0":"#cc8800","c1":"#884400","xp":10,"score":30},
    "armored": {"spd":0.6,  "hp":300, "dmg":15, "r":20, "c0":"#607080","c1":"#404050","xp":60,"score":200},
}

# ─── DATACLASSES ─────────────────────────────────────────────────────────────
@dataclass
class Particle:
    x: float; y: float
    vx: float; vy: float
    life: int; max_life: int
    color: QColor; r: float = 3.0
    gravity: float = 0.0

@dataclass
class FloatText:
    x: float; y: float
    text: str; color: QColor
    life: int = 60; vy: float = -1.2

@dataclass
class Bullet:
    x: float; y: float
    vx: float; vy: float
    life: int = 70; dmg: float = 20.0
    is_enemy: bool = False
    color: QColor = field(default_factory=lambda: C.YELLOW)
    r: float = 3.5

@dataclass
class Pickup:
    x: float; y: float
    ptype: str; amount: int
    r: float = 11.0; bob: float = 0.0

@dataclass
class Barricade:
    x: float; y: float
    hp: float = 150; max_hp: float = 150
    w: float = 52; h: float = 20
    angle: float = 0.0

@dataclass
class BloodStain:
    x: float; y: float
    r: float; alpha: float

@dataclass
class Zombie:
    x: float; y: float; ztype: str
    hp: float; max_hp: float; spd: float
    dmg: float; r: float
    c0: str; c1: str
    xp: int; score: int
    ranged: bool = False
    explosive: bool = False
    is_boss: bool = False
    angle: float = 0.0
    atk_cd: int = 0
    wobble: float = 0.0
    flash_time: int = 0
    spit_cd: int = 120
    is_armored: bool = False
    armor_hp: float = 0.0
    max_armor: float = 0.0

@dataclass
class Player:
    x: float = W_WORLD / 2
    y: float = H_WORLD / 2
    hp: float = 100; max_hp: float = 100
    speed: float = 2.8; angle: float = 0.0; r: float = 14
    alive: bool = True
    shoot_cd: int = 0; reload_time: int = 0
    clip: int = 30; max_clip: int = 30
    xp: float = 0; level: int = 1
    dmg_mult: float = 1.0
    rage: float = 0.0
    shield: float = 0.0
    grenades: int = 3
    grenade_cd: int = 0
    dash_cd: int = 0
    is_dashing: bool = False
    dash_frames: int = 0

# ─── UTILITY ─────────────────────────────────────────────────────────────────
def qcf(hex_str: str) -> QColor:
    return QColor(hex_str)

def dist(ax, ay, bx, by) -> float:
    return math.hypot(ax - bx, ay - by)

def norm(dx, dy):
    d = math.hypot(dx, dy) or 1
    return dx / d, dy / d

def lerp(a, b, t):
    return a + (b - a) * t

def wave_config(wave: int, spawn_mult: float):
    return {
        "regular":  int((3 + wave * 2.2) * spawn_mult),
        "fast":     int((wave - 2) * 1.8 * spawn_mult) if wave > 2 else 0,
        "tank":     int((wave - 4) * 0.9 * spawn_mult) if wave > 4 else 0,
        "spitter":  int((wave - 3) * 0.8 * spawn_mult) if wave > 3 else 0,
        "exploder": int((wave - 6) * 0.7 * spawn_mult) if wave > 6 else 0,
        "runner":   int((wave - 1) * 1.2 * spawn_mult) if wave > 1 else 0,
        "armored":  int((wave - 7) * 0.5 * spawn_mult) if wave > 7 else 0,
        "boss":     math.ceil(wave / 5) if wave % 5 == 0 else 0,
    }

# ─── LOAD HIGH SCORES ────────────────────────────────────────────────────────
def load_scores():
    try:
        default_scores = {"high_score": 0, "best_wave": 0, "total_kills": 0}
        if not HIGH_SCORE_FILE.exists():
            return default_scores

        with open(HIGH_SCORE_FILE, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None) # Read header row
            if header is None: # File is empty or has no header
                return default_scores
            
            data_row = next(reader, None) # Read data row
            if data_row is None: # Only header exists
                return default_scores

            scores = {}
            for i, key in enumerate(header):
                if i < len(data_row): # Ensure we don't go out of bounds
                    try:
                        scores[key] = int(data_row[i])
                    except ValueError:
                        # Handle cases where a value might not be an integer, fall back to default
                        scores[key] = default_scores.get(key, 0)
                else:
                    # If a header column is missing its data, use default
                    scores[key] = default_scores.get(key, 0)
            
            # Ensure all default keys are present in case the CSV is incomplete
            for key, default_val in default_scores.items():
                if key not in scores:
                    scores[key] = default_val
            
            return scores

    except (FileNotFoundError, csv.Error) as e:
        print(f"Error loading scores from CSV: {e}")
    except Exception as e: # Catch any other unexpected errors
        print(f"An unexpected error occurred loading scores: {e}")
    return {"high_score": 0, "best_wave": 0, "total_kills": 0} # Return defaults on any error

def save_scores(data: dict):
    try:
        with open(HIGH_SCORE_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            header = ["high_score", "best_wave", "total_kills"] # Explicit order for CSV
            values = [data.get(key, 0) for key in header] # Get values, with 0 as default if key is missing
            writer.writerow(header)
            writer.writerow(values)
    except Exception as e:
        print(f"Error saving scores to CSV: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
#  GAME ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
class GameEngine:
    def __init__(self, diff_key: str = "medium"):
        self.diff_key = diff_key
        self.diff = DIFFICULTIES[diff_key]
        self.reset()

    def reset(self):
        d = self.diff
        self.player = Player(speed=d["p_spd"])
        self.inv = {"food": 0, "ammo": d["ammo"], "wood": d["wood"], "medicine": d["med"]}
        self.wave = 1
        self.kills = 0
        self.score = 0
        self.frame = 0
        self.zombies: List[Zombie] = []
        self.bullets: List[Bullet] = []
        self.pickups: List[Pickup] = []
        self.barricades: List[Barricade] = []
        self.particles: List[Particle] = []
        self.blood_stains: List[BloodStain] = []
        self.float_texts: List[FloatText] = []
        self.decor = []
        self.wave_active = True
        self.between_waves = False
        self.wave_countdown = 0
        self.game_over = False
        self.victory = False
        self.screen_shake = 0.0
        self.pending_spawns = []  # (delay_frames, type)
        self.cam_x = self.player.x
        self.cam_y = self.player.y
        self._gen_decor()
        self._spawn_init_pickups()
        self._start_wave()

    def _gen_decor(self):
        self.decor = []
        for _ in range(350):
            t = random.random()
            kind = "rock" if t > 0.6 else "plank" if t > 0.3 else "debris"
            self.decor.append({
                "x": random.uniform(20, W_WORLD - 20),
                "y": random.uniform(20, H_WORLD - 20),
                "kind": kind,
                "s": random.uniform(6, 24),
                "a": random.uniform(0, math.pi * 2),
                "c": QColor(
                    random.randint(18, 38),
                    random.randint(18, 35),
                    random.randint(10, 24)
                )
            })

    def _spawn_init_pickups(self):
        for _ in range(35):
            pt = random.choice(["food", "ammo", "wood", "medicine"])
            amt = {"ammo": 12, "wood": 18, "medicine": 1, "food": 2}[pt]
            amt = round(amt * self.diff["res"])
            self.pickups.append(Pickup(
                x=random.uniform(150, W_WORLD - 150),
                y=random.uniform(150, H_WORLD - 150),
                ptype=pt, amount=max(1, amt),
                bob=random.uniform(0, math.pi * 2)
            ))

    def _start_wave(self):
        cfg = wave_config(self.wave, self.diff["spawn"])
        frame = 0
        for ztype, count in cfg.items():
            for _ in range(count):
                self.pending_spawns.append((frame, ztype))
                frame += {"regular": 12, "fast": 9, "tank": 24, "spitter": 15,
                          "exploder": 11, "runner": 8, "armored": 30, "boss": 36}[ztype]
        self.wave_active = True
        self.between_waves = False

    def _do_spawn(self, ztype: str):
        t = ZT[ztype]
        margin = 100
        side = random.randint(0, 3)
        if side == 0:   x, y = random.uniform(0, W_WORLD), -margin
        elif side == 1: x, y = W_WORLD + margin, random.uniform(0, H_WORLD)
        elif side == 2: x, y = random.uniform(0, W_WORLD), H_WORLD + margin
        else:           x, y = -margin, random.uniform(0, H_WORLD)

        ws = 1 + (self.wave - 1) * 0.08
        d = self.diff
        z = Zombie(
            x=x, y=y, ztype=ztype,
            hp=t["hp"] * d["z_hp"] * ws,
            max_hp=t["hp"] * d["z_hp"] * ws,
            spd=(t["spd"] + random.uniform(0, 0.25)) * d["z_spd"] * (1 + (self.wave - 1) * 0.04),
            dmg=t["dmg"] * d["z_dmg"] * ws,
            r=t["r"], c0=t["c0"], c1=t["c1"],
            xp=t["xp"], score=t["score"],
            ranged=t.get("ranged", False),
            explosive=t.get("explosive", False),
            is_boss=t.get("is_boss", False),
            wobble=random.uniform(0, math.pi * 2),
            spit_cd=120 if t.get("ranged") else 9999,
        )
        if ztype == "armored":
            z.is_armored = True
            z.armor_hp = 80 * d["z_hp"]
            z.max_armor = z.armor_hp
        self.zombies.append(z)

    # ─── UPDATE ───
    def update(self, keys: set, mouse_world: QPointF, fire_held: bool):
        if self.game_over:
            return
        p = self.player
        self.frame += 1
        if self.screen_shake > 0:
            self.screen_shake = max(0, self.screen_shake - 0.8)

        # Pending spawns
        new_pending = []
        for (delay, ztype) in self.pending_spawns:
            if delay <= 0:
                self._do_spawn(ztype)
            else:
                new_pending.append((delay - 1, ztype))
        self.pending_spawns = new_pending

        # Player movement
        mx, my = 0.0, 0.0
        if Qt.Key.Key_W in keys or Qt.Key.Key_Up in keys:    my -= 1
        if Qt.Key.Key_S in keys or Qt.Key.Key_Down in keys:  my += 1
        if Qt.Key.Key_A in keys or Qt.Key.Key_Left in keys:  mx -= 1
        if Qt.Key.Key_D in keys or Qt.Key.Key_Right in keys: mx += 1
        if mx and my: mx *= 0.707; my *= 0.707

        rage_boost = 1.2 if p.rage > 80 else 1.0
        spd = p.speed * rage_boost

        if p.is_dashing:
            p.dash_frames -= 1
            spd *= 3.5
            if p.dash_frames <= 0:
                p.is_dashing = False

        p.x = max(p.r, min(W_WORLD - p.r, p.x + mx * spd))
        p.y = max(p.r, min(H_WORLD - p.r, p.y + my * spd))

        # Aim
        p.angle = math.atan2(mouse_world.y() - p.y, mouse_world.x() - p.x)

        # Auto-fire
        if fire_held:
            self.shoot(mouse_world)

        # Cooldowns
        if p.shoot_cd > 0: p.shoot_cd -= 1
        if p.grenade_cd > 0: p.grenade_cd -= 1
        if p.dash_cd > 0: p.dash_cd -= 1

        if p.reload_time > 0:
            p.reload_time -= 1
            if p.reload_time == 0:
                need = p.max_clip - p.clip
                take = min(need, self.inv["ammo"])
                self.inv["ammo"] -= take
                p.clip += take

        # Camera
        self.cam_x = lerp(self.cam_x, p.x, 0.1)
        self.cam_y = lerp(self.cam_y, p.y, 0.1)

        self._update_bullets()
        self._update_zombies()
        self._update_pickups()
        self._update_particles()
        self._update_float_texts()

        # Rage decay
        p.rage = max(0, p.rage - 0.12)

        # Wave management
        if self.wave_active and len(self.zombies) == 0 and len(self.pending_spawns) == 0:
            self.wave_active = False
            self.between_waves = True
            cooldown = max(5, 10 - self.wave // 3)
            self.wave_countdown = cooldown * FPS
            self._scatter_pickups(p.x, p.y, min(6 + self.wave, 20))
            self.score += self.wave * 100
            if self.wave >= 20:
                self.victory = True
                self.game_over = True
                return

        if self.between_waves:
            self.wave_countdown -= 1
            if self.wave_countdown <= 0:
                self.wave += 1
                self.between_waves = False
                self._start_wave()

    def _update_bullets(self):
        for b in self.bullets[:]:
            b.x += b.vx; b.y += b.vy
            b.life -= 1
            hit = False
            if not b.is_enemy:
                for z in self.zombies[:]:
                    if dist(b.x, b.y, z.x, z.y) < z.r + 5:
                        if z.is_armored and z.armor_hp > 0:
                            z.armor_hp = max(0, z.armor_hp - b.dmg * 0.5)
                            z.flash_time = 4
                        else:
                            z.hp -= b.dmg
                            z.flash_time = 6
                            self._spawn_blood(b.x, b.y, 5)
                        if z.hp <= 0:
                            self._zombie_die(z)
                        hit = True
                        break
                if not hit:
                    for bar in self.barricades:
                        bx, by = bar.x - bar.w/2, bar.y - bar.h/2
                        if bx < b.x < bx + bar.w and by < b.y < by + bar.h:
                            hit = True; break
            else:
                p = self.player
                if dist(b.x, b.y, p.x, p.y) < p.r + 6:
                    self._hurt_player(b.dmg)
                    self._spawn_blood(b.x, b.y, 4)
                    hit = True

            if hit or b.life <= 0 or b.x < -100 or b.x > W_WORLD+100 or b.y < -100 or b.y > H_WORLD+100:
                self.bullets.remove(b)

    def _update_zombies(self):
        p = self.player
        for z in self.zombies[:]:
            z.wobble += 0.08
            if z.flash_time > 0: z.flash_time -= 1
            dx, dy = p.x - z.x, p.y - z.y
            d = math.hypot(dx, dy) or 1
            z.angle = math.atan2(dy, dx)

            # Spitter
            if z.ranged:
                z.spit_cd -= 1
                if z.spit_cd <= 0 and d < 380:
                    z.spit_cd = int(90 + random.uniform(0, 60))
                    nx, ny = norm(dx, dy)
                    speed = 5.5
                    ep = Bullet(z.x, z.y,
                        vx=nx*speed + random.uniform(-0.6,0.6),
                        vy=ny*speed + random.uniform(-0.6,0.6),
                        life=80, dmg=z.dmg,
                        is_enemy=True,
                        color=QColor(60, 255, 60), r=5.5)
                    self.bullets.append(ep)

            # Exploder
            if z.explosive and d < z.r + p.r + 22:
                self._spawn_explosion(z.x, z.y, 85)
                self.zombies.remove(z)
                self.kills += 1
                self.score += z.score
                continue

            # Movement
            if not z.ranged or d > 230:
                bx, by = dx / d * z.spd, dy / d * z.spd
                for bar in self.barricades:
                    bd = dist(z.x, z.y, bar.x, bar.y)
                    if bd < 55:
                        bx += (z.x - bar.x) / bd * 2.5
                        by += (z.y - bar.y) / bd * 2.5
                if d > z.r + p.r:
                    ml = math.hypot(bx, by) or 1
                    z.x += (bx / ml) * z.spd
                    z.y += (by / ml) * z.spd

            # Attack player
            if d < z.r + p.r + 4 and not z.ranged:
                if z.atk_cd <= 0:
                    self._hurt_player(z.dmg)
                    z.atk_cd = 55
                    self.screen_shake = min(self.screen_shake + 8, 16)

            if z.atk_cd > 0: z.atk_cd -= 1

            # Attack barricades
            for bar in self.barricades[:]:
                if dist(z.x, z.y, bar.x, bar.y) < z.r + 32:
                    if z.atk_cd <= 0:
                        bar.hp -= z.dmg * 0.5
                        if bar.hp <= 0:
                            self.barricades.remove(bar)
                            break

    def _update_pickups(self):
        p = self.player
        for pk in self.pickups[:]:
            pk.bob += 0.05
            if dist(p.x, p.y, pk.x, pk.y) < p.r + pk.r + 5:
                if pk.ptype == "xp":
                    p.xp += pk.amount
                    self._check_level_up()
                    self._float(p.x, p.y - 20, f"+{pk.amount} XP", C.XP_CLR)
                else:
                    self.inv[pk.ptype] = self.inv.get(pk.ptype, 0) + pk.amount
                    if pk.ptype == "ammo":  self.inv["ammo"]  = min(self.inv["ammo"], 400)
                    if pk.ptype == "wood":  self.inv["wood"]  = min(self.inv["wood"], 999)
                self.pickups.remove(pk)

    def _update_particles(self):
        for pt in self.particles[:]:
            pt.x += pt.vx; pt.y += pt.vy
            pt.vx *= 0.88; pt.vy *= 0.88
            pt.vy += pt.gravity
            pt.life -= 1
            if pt.life <= 0:
                self.particles.remove(pt)

    def _update_float_texts(self):
        for ft in self.float_texts[:]:
            ft.y += ft.vy
            ft.life -= 1
            if ft.life <= 0:
                self.float_texts.remove(ft)

    # ─── ACTIONS ───
    def shoot(self, mouse_world: QPointF):
        p = self.player
        if not p.alive or p.reload_time > 0: return
        if p.clip <= 0:
            self.try_reload()
            return
        if p.shoot_cd > 0: return

        p.clip -= 1
        p.shoot_cd = max(4, 9 - p.level // 3)
        dx = mouse_world.x() - p.x
        dy = mouse_world.y() - p.y

        shot_count = 2 if p.level >= 8 else 1
        for s in range(shot_count):
            ang = math.atan2(dy, dx) + (s - (shot_count - 1) / 2) * 0.15
            spread = 0.04 * (0.7 if p.level > 5 else 1.0)
            self.bullets.append(Bullet(
                x=p.x, y=p.y,
                vx=math.cos(ang)*14 + random.uniform(-spread, spread)*14,
                vy=math.sin(ang)*14 + random.uniform(-spread, spread)*14,
                life=70, dmg=20 * p.dmg_mult,
                color=C.AMMO_CLR
            ))

        p.rage = min(100, p.rage + 1)

        # Muzzle flash
        nx = math.cos(p.angle)
        ny = math.sin(p.angle)
        for _ in range(6):
            self.particles.append(Particle(
                x=p.x, y=p.y,
                vx=nx*(3+random.uniform(0,5))+random.uniform(-2,2),
                vy=ny*(3+random.uniform(0,5))+random.uniform(-2,2),
                life=random.randint(6, 12), max_life=12,
                color=QColor(255, 200, 60), r=random.uniform(1.5, 3.5)
            ))

    def try_heal(self):
        p = self.player
        if self.inv.get("medicine", 0) > 0 and p.hp < p.max_hp:
            self.inv["medicine"] -= 1
            p.hp = min(p.max_hp, p.hp + 45)
            self._float(p.x, p.y - 20, "+45 HP", QColor(60, 255, 120))
            # Heal particles
            for _ in range(10):
                ang = random.uniform(0, math.pi * 2)
                self.particles.append(Particle(
                    p.x, p.y,
                    vx=math.cos(ang)*2, vy=math.sin(ang)*2 - 2,
                    life=30, max_life=30, color=QColor(60, 255, 120), r=3
                ))

    def try_reload(self):
        p = self.player
        if p.clip < p.max_clip and self.inv.get("ammo", 0) > 0 and p.reload_time == 0:
            p.reload_time = 90

    def throw_grenade(self, target: QPointF):
        p = self.player
        if p.grenades <= 0 or p.grenade_cd > 0: return
        p.grenades -= 1
        p.grenade_cd = 120
        # Schedule explosion
        tx, ty = target.x(), target.y()
        # Grenade travels to target
        dx, dy = tx - p.x, ty - p.y
        d = math.hypot(dx, dy) or 1
        spd = 8
        gren = Bullet(p.x, p.y, vx=dx/d*spd, vy=dy/d*spd,
                      life=int(d/spd)+2, dmg=0,
                      color=QColor(200, 180, 60), r=6)
        gren._grenade = True
        gren._tx, gren._ty = tx, ty
        gren._exploded = False
        self.bullets.append(gren)
        self._float(p.x, p.y - 30, "GRENADE!", QColor(255, 200, 0))

    def try_dash(self, keys: set):
        p = self.player
        if p.dash_cd > 0 or p.is_dashing: return
        mx, my = 0.0, 0.0
        if Qt.Key.Key_W in keys or Qt.Key.Key_Up in keys:    my -= 1
        if Qt.Key.Key_S in keys or Qt.Key.Key_Down in keys:  my += 1
        if Qt.Key.Key_A in keys or Qt.Key.Key_Left in keys:  mx -= 1
        if Qt.Key.Key_D in keys or Qt.Key.Key_Right in keys: mx += 1
        if mx == 0 and my == 0: return
        p.is_dashing = True
        p.dash_frames = 10
        p.dash_cd = 90
        # Dash invincibility trail
        for i in range(8):
            self.particles.append(Particle(
                p.x - mx * i * 5, p.y - my * i * 5,
                vx=random.uniform(-1, 1), vy=random.uniform(-1, 1),
                life=15, max_life=15, color=QColor(0, 200, 255, 180), r=8
            ))

    def place_barricade(self, world_pos: QPointF):
        if self.inv.get("wood", 0) < 10:
            p = self.player
            self._float(p.x, p.y, "Need 🪵 10!", C.RED)
            return
        self.inv["wood"] -= 10
        self.barricades.append(Barricade(
            x=world_pos.x(), y=world_pos.y(),
            angle=random.uniform(-0.2, 0.2)
        ))

    # ─── HELPERS ───
    def _hurt_player(self, dmg: float):
        p = self.player
        if p.is_dashing: return  # Dash invincibility
        if p.shield > 0:
            p.shield -= dmg
            if p.shield < 0: p.shield = 0
            self._float(p.x, p.y, "BLOCKED!", C.CYAN)
            return
        p.hp = max(0, p.hp - dmg)
        if p.hp <= 0:
            p.alive = False
            self.game_over = True
            self._spawn_explosion(p.x, p.y, 60)

    def _zombie_die(self, z: Zombie):
        self.kills += 1
        self.score += z.score
        p = self.player
        p.xp += z.xp
        p.rage = min(100, p.rage + (20 if z.is_boss else 5))
        self._check_level_up()

        t = ZT[z.ztype]
        res_map = {
            "regular": ("ammo", 0.35, "food", 0.4),
            "fast":    ("ammo", 0.25, "food", 0.35),
            "tank":    ("wood", 0.5,  "medicine", 0.4),
            "spitter": ("ammo", 0.5,  "food", 0.3),
            "exploder":("wood", 0.4,  None, 0),
            "runner":  ("ammo", 0.3,  "food", 0.45),
            "armored": ("wood", 0.6,  "medicine", 0.5),
            "boss":    ("ammo", 0.9,  "medicine", 0.8),
        }
        rmap = res_map.get(z.ztype, ("ammo", 0.3, "food", 0.3))
        for i in [0, 2]:
            rtype, prob = rmap[i], rmap[i+1]
            if rtype and random.random() < prob:
                amt = {"ammo": 8, "food": 3, "wood": 10, "medicine": 1}[rtype]
                self.pickups.append(Pickup(
                    x=z.x, y=z.y, ptype=rtype,
                    amount=round(amt * self.diff["res"]),
                    bob=random.uniform(0, math.pi * 2)
                ))

        # XP pickup
        self.pickups.append(Pickup(z.x + random.uniform(-10, 10),
                                    z.y + random.uniform(-10, 10),
                                    "xp", z.xp, r=8))

        self._spawn_blood(z.x, z.y, 20 if z.is_boss else 8)
        if z.is_boss:
            self.screen_shake = 28
            self._float(z.x, z.y - 40, "BOSS DOWN! +500", C.YELLOW)
        self.zombies.remove(z)

    def _check_level_up(self):
        p = self.player
        needed = p.level * 80
        if p.xp >= needed:
            p.xp -= needed
            p.level += 1
            p.max_hp += 12
            p.hp = min(p.max_hp, p.hp + 25)
            p.dmg_mult = 1.0 + (p.level - 1) * 0.15
            if p.level % 3 == 0:
                p.grenades = min(p.grenades + 1, 5)
            self._float(p.x, p.y - 50, f"⬆ LEVEL {p.level}!", C.YELLOW)
            self.screen_shake = 8
            # Level-up burst
            for i in range(20):
                ang = i / 20 * math.pi * 2
                self.particles.append(Particle(
                    p.x, p.y,
                    vx=math.cos(ang)*4, vy=math.sin(ang)*4,
                    life=40, max_life=40,
                    color=QColor(255, 200, 40), r=4, gravity=-0.05
                ))

    def _spawn_blood(self, x, y, n: int):
        for _ in range(n):
            self.particles.append(Particle(
                x, y,
                vx=random.uniform(-5, 5), vy=random.uniform(-5, 5),
                life=random.randint(18, 32), max_life=32,
                color=QColor(random.randint(100, 160), 0, 0), r=random.uniform(2, 4),
                gravity=0.1
            ))
        if len(self.blood_stains) < 200:
            self.blood_stains.append(BloodStain(
                x + random.uniform(-5, 5), y + random.uniform(-5, 5),
                r=random.uniform(4, 12), alpha=random.uniform(0.1, 0.45)
            ))

    def _spawn_explosion(self, x, y, radius: float):
        self.screen_shake = min(self.screen_shake + 22, 28)
        for i in range(35):
            col = C.ORANGE if i % 2 == 0 else C.YELLOW
            self.particles.append(Particle(
                x, y,
                vx=random.uniform(-11, 11), vy=random.uniform(-11, 11),
                life=random.randint(22, 40), max_life=40,
                color=col, r=random.uniform(3, 7), gravity=0.08
            ))
        # Smoke
        for _ in range(12):
            self.particles.append(Particle(
                x + random.uniform(-10, 10), y + random.uniform(-10, 10),
                vx=random.uniform(-1.5, 1.5), vy=random.uniform(-3, -1),
                life=60, max_life=60,
                color=QColor(80, 80, 80), r=random.uniform(5, 12)
            ))
        for z in self.zombies[:]:
            if dist(z.x, z.y, x, y) < radius:
                z.hp -= 70
                z.flash_time = 10
                if z.hp <= 0:
                    self._zombie_die(z)
        p = self.player
        if dist(p.x, p.y, x, y) < radius:
            self._hurt_player(22)
        for bar in self.barricades[:]:
            if dist(bar.x, bar.y, x, y) < radius:
                bar.hp -= 55
                if bar.hp <= 0:
                    self.barricades.remove(bar)

    def _scatter_pickups(self, cx, cy, n: int):
        types = ["food", "ammo", "wood", "medicine"]
        for _ in range(n):
            pt = random.choice(types)
            amt = {"ammo": 15, "wood": 20, "medicine": 1, "food": 3}[pt]
            self.pickups.append(Pickup(
                x=cx + random.uniform(-700, 700),
                y=cy + random.uniform(-700, 700),
                ptype=pt, amount=round(amt * self.diff["res"]),
                bob=random.uniform(0, math.pi * 2)
            ))

    def _float(self, x, y, text: str, color: QColor):
        self.float_texts.append(FloatText(x, y - 10, text, color))


# ═══════════════════════════════════════════════════════════════════════════════
#  GAME CANVAS (Rendering)
# ═══════════════════════════════════════════════════════════════════════════════
class GameCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.engine: Optional[GameEngine] = None
        self.keys = set()
        self.mouse_screen = QPointF(0, 0)
        self.mouse_world = QPointF(0, 0)
        self.fire_held = False
        self.build_mode = False
        self.build_ghost: Optional[QPointF] = None
        self._frame_count = 0

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def set_engine(self, eng: GameEngine):
        self.engine = eng

    def _world_to_screen(self, wx, wy, cx, cy) -> tuple:
        sx = wx - cx + self.width() / 2
        sy = wy - cy + self.height() / 2
        return sx, sy

    def _screen_to_world(self, sx, sy) -> tuple:
        if not self.engine: return 0, 0
        cx, cy = self.engine.cam_x, self.engine.cam_y
        wx = sx - self.width() / 2 + cx
        wy = sy - self.height() / 2 + cy
        return wx, wy

    def update_mouse_world(self):
        if not self.engine: return
        wx, wy = self._screen_to_world(self.mouse_screen.x(), self.mouse_screen.y())
        self.mouse_world = QPointF(wx, wy)

    def game_tick(self):
        if not self.engine: return
        self.update_mouse_world()
        self._frame_count += 1
        if not self.engine.game_over:
            self.engine.update(self.keys, self.mouse_world, self.fire_held)
        self.update()

    # ─── INPUT ───
    def keyPressEvent(self, e: QKeyEvent):
        self.keys.add(e.key())
        if not self.engine or self.engine.game_over: return
        k = e.key()
        if k == Qt.Key.Key_H:   self.engine.try_heal()
        if k == Qt.Key.Key_R:   self.engine.try_reload()
        if k == Qt.Key.Key_Space: self.engine.try_dash(self.keys)
        if k == Qt.Key.Key_B:
            self.build_mode = not self.build_mode

    def keyReleaseEvent(self, e: QKeyEvent):
        self.keys.discard(e.key())

    def mouseMoveEvent(self, e: QMouseEvent):
        self.mouse_screen = QPointF(e.position().x(), e.position().y())
        self.update_mouse_world()
        if self.build_mode:
            self.build_ghost = QPointF(self.mouse_world)

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton:
            self.fire_held = True
            if self.build_mode and self.engine:
                self.engine.place_barricade(self.mouse_world)
            else:
                if self.engine:
                    self.engine.shoot(self.mouse_world)
        elif e.button() == Qt.MouseButton.RightButton:
            if self.engine:
                self.engine.throw_grenade(self.mouse_world)

    def mouseReleaseEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton:
            self.fire_held = False

    # ─── PAINT ───
    def paintEvent(self, e: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        W, H = self.width(), self.height()
        eng = self.engine

        if not eng:
            painter.fillRect(0, 0, W, H, C.BG)
            return

        # Screen shake offset
        sx = random.uniform(-eng.screen_shake, eng.screen_shake) if eng.screen_shake > 0 else 0
        sy = random.uniform(-eng.screen_shake, eng.screen_shake) if eng.screen_shake > 0 else 0
        cx = eng.cam_x - sx
        cy = eng.cam_y - sy

        def ws(wx, wy):
            return self._world_to_screen(wx, wy, cx, cy)

        # ── Ground ──
        self._draw_ground(painter, W, H, cx, cy)
        self._draw_decor(painter, eng, cx, cy)
        self._draw_blood(painter, eng, cx, cy, ws)
        self._draw_barricades(painter, eng, ws)
        self._draw_pickups(painter, eng, ws)
        self._draw_bullets(painter, eng, ws)
        self._draw_zombies(painter, eng, ws)
        self._draw_player(painter, eng, ws, W, H)
        self._draw_particles(painter, eng, cx, cy)
        self._draw_float_texts(painter, eng, cx, cy)

        # Build ghost
        if self.build_mode and self.build_ghost:
            gx, gy = ws(self.build_ghost.x(), self.build_ghost.y())
            col = C.GREEN if eng.inv.get("wood", 0) >= 10 else C.RED
            pen = QPen(col, 2, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(QBrush(QColor(col.red(), col.green(), col.blue(), 40)))
            painter.drawRect(int(gx - 26), int(gy - 10), 52, 20)
            painter.setPen(QPen(col, 1))
            painter.setFont(QFont("Courier New", 9))
            painter.drawText(int(gx - 30), int(gy - 16), "🪵 10 wood")

        # ── HUD ──
        self._draw_hud(painter, eng, W, H)
        self._draw_minimap(painter, eng, W, H)
        self._draw_wave_info(painter, eng, W, H)
        self._draw_boss_warning(painter, eng, W, H)

        painter.end()

    def _draw_ground(self, p: QPainter, W, H, cx, cy):
        # Fill visible area
        p.fillRect(0, 0, W, H, QColor(18, 18, 12))

        # Grid
        pen = QPen(QColor(255, 255, 255, 6), 1)
        p.setPen(pen)
        ox = -(cx % 100)
        oy = -(cy % 100)
        # World offset
        world_left = cx - W/2
        world_top = cy - H/2

        start_x = -cx + int(cx / 100) * 100 - 100
        start_y = -cy + int(cy / 100) * 100 - 100

        xs = int((cx - W/2) / 100) * 100
        ys = int((cy - H/2) / 100) * 100

        for gx in range(xs, int(cx + W/2) + 100, 100):
            sx, _ = self._world_to_screen(gx, 0, cx, cy)
            p.drawLine(int(sx), 0, int(sx), H)
        for gy in range(ys, int(cy + H/2) + 100, 100):
            _, sy = self._world_to_screen(0, gy, cx, cy)
            p.drawLine(0, int(sy), W, int(sy))

        # World border
        bx1, by1 = self._world_to_screen(0, 0, cx, cy)
        bx2, by2 = self._world_to_screen(W_WORLD, H_WORLD, cx, cy)
        pen = QPen(QColor(180, 0, 0, 160), 6)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(int(bx1), int(by1), int(bx2 - bx1), int(by2 - by1))
        pen2 = QPen(QColor(120, 0, 0, 60), 22)
        p.setPen(pen2)
        p.drawRect(int(bx1+11), int(by1+11), int(bx2-bx1-22), int(by2-by1-22))

    def _draw_decor(self, p: QPainter, eng: GameEngine, cx, cy):
        W, H = self.width(), self.height()
        for d in eng.decor:
            sx, sy = self._world_to_screen(d["x"], d["y"], cx, cy)
            if sx < -40 or sx > W+40 or sy < -40 or sy > H+40: continue
            p.save()
            p.translate(sx, sy)
            p.rotate(math.degrees(d["a"]))
            p.setBrush(QBrush(d["c"]))
            p.setPen(Qt.PenStyle.NoPen)
            s = d["s"]
            if d["kind"] == "rock":
                p.drawEllipse(QRectF(-s, -s*0.65, s*2, s*1.3))
            elif d["kind"] == "plank":
                p.drawRect(QRectF(-s/2, -s/5, s, s/2.5))
            else:
                p.setOpacity(0.3)
                p.drawRect(QRectF(-s/3, -s/3, s*0.7, s*0.7))
            p.restore()

    def _draw_blood(self, p: QPainter, eng: GameEngine, cx, cy, ws):
        for bs in eng.blood_stains:
            sx, sy = ws(bs.x, bs.y)
            p.setOpacity(bs.alpha * 0.6)
            p.setBrush(QBrush(QColor(80, 0, 0)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(sx, sy), bs.r, bs.r)
        p.setOpacity(1.0)

    def _draw_barricades(self, p: QPainter, eng: GameEngine, ws):
        for bar in eng.barricades:
            sx, sy = ws(bar.x, bar.y)
            hp_pct = bar.hp / bar.max_hp
            r = int(120 + 70 * (1 - hp_pct))
            g = int(80 * hp_pct)
            p.save()
            p.translate(sx, sy)
            p.rotate(math.degrees(bar.angle))
            # Shadow
            p.setOpacity(0.3)
            p.fillRect(QRectF(-bar.w/2+3, -bar.h/2+4, bar.w, bar.h), QColor(0,0,0))
            p.setOpacity(1.0)
            # Wood body
            grad = QLinearGradient(-bar.w/2, -bar.h/2, -bar.w/2, bar.h/2)
            grad.setColorAt(0, QColor(r, g+30, 18))
            grad.setColorAt(1, QColor(r-30, g, 10))
            p.setBrush(QBrush(grad))
            p.setPen(QPen(QColor(60, 30, 5), 2))
            p.drawRect(QRectF(-bar.w/2, -bar.h/2, bar.w, bar.h))
            # Wood grain lines
            p.setPen(QPen(QColor(0,0,0,50), 1))
            for i in range(1, 4):
                lx = -bar.w/2 + bar.w/4 * i
                p.drawLine(QPointF(lx, -bar.h/2), QPointF(lx, bar.h/2))
            p.restore()
            # HP bar
            if hp_pct < 1.0:
                bw = bar.w
                p.fillRect(QRectF(sx - bw/2, sy - bar.h/2 - 7, bw, 3), QColor(30,30,30))
                hpc = QColor(60,180,60) if hp_pct > 0.5 else QColor(200,50,50)
                p.fillRect(QRectF(sx - bw/2, sy - bar.h/2 - 7, bw * hp_pct, 3), hpc)

    def _draw_pickups(self, p: QPainter, eng: GameEngine, ws):
        W, H = self.width(), self.height()
        icons = {"food":"🍖","ammo":"🔫","wood":"🪵","medicine":"💊","xp":"✨"}
        colors = {
            "food": C.FOOD_CLR, "ammo": C.AMMO_CLR,
            "wood": C.WOOD_CLR, "medicine": C.MED_CLR, "xp": C.XP_CLR
        }
        f = QFont("Segoe UI Emoji", 14)
        for pk in eng.pickups:
            sx, sy = ws(pk.x, pk.y)
            if sx < -20 or sx > W+20 or sy < -20 or sy > H+20: continue
            bob = math.sin(pk.bob) * 3
            col = colors.get(pk.ptype, C.WHITE)
            # Glow
            p.setOpacity(0.35)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(col))
            r = pk.r + 4
            p.drawEllipse(QPointF(sx, sy + bob), r, r)
            p.setOpacity(1.0)
            p.setFont(f)
            p.drawText(QRectF(sx-12, sy-12+bob, 24, 24), Qt.AlignmentFlag.AlignCenter,
                       icons.get(pk.ptype, "?"))

    def _draw_bullets(self, p: QPainter, eng: GameEngine, ws):
        W, H = self.width(), self.height()
        for b in eng.bullets:
            sx, sy = ws(b.x, b.y)
            if sx < -10 or sx > W+10 or sy < -10 or sy > H+10: continue
            if b.is_enemy:
                # Spit projectile
                p.setOpacity(0.6)
                p.setBrush(QBrush(QColor(40,180,40)))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QPointF(sx, sy), b.r + 3, b.r + 3)
                p.setOpacity(1.0)
                p.setBrush(QBrush(QColor(80, 255, 80)))
                p.drawEllipse(QPointF(sx, sy), b.r, b.r)
            elif hasattr(b, '_grenade') and b._grenade:
                p.setBrush(QBrush(QColor(200, 180, 60)))
                p.setPen(QPen(QColor(255, 220, 80), 1))
                p.drawEllipse(QPointF(sx, sy), 5, 5)
            else:
                # Player bullet trail
                p.setOpacity(0.3)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(C.AMMO_CLR))
                p.drawEllipse(QPointF(sx - b.vx*0.5, sy - b.vy*0.5), b.r + 1, b.r + 1)
                p.setOpacity(1.0)
                p.setBrush(QBrush(C.AMMO_CLR))
                p.drawEllipse(QPointF(sx, sy), b.r, b.r)
        p.setOpacity(1.0)

    def _draw_zombies(self, p: QPainter, eng: GameEngine, ws):
        W, H = self.width(), self.height()
        for z in eng.zombies:
            sx, sy = ws(z.x, z.y)
            if sx < -60 or sx > W+60 or sy < -60 or sy > H+60: continue
            self._draw_zombie(p, z, sx, sy)

    def _draw_zombie(self, p: QPainter, z: Zombie, sx, sy):
        p.save()
        p.translate(sx, sy)

        # Shadow
        p.setOpacity(0.3)
        p.setBrush(QBrush(QColor(0,0,0)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(-z.r*0.9, z.r*0.3, z.r*1.8, z.r*0.7))
        p.setOpacity(1.0)

        p.rotate(math.degrees(math.sin(z.wobble) * 0.12))

        # Flash
        if z.flash_time > 0:
            p.setOpacity(z.flash_time / 6.0)
            p.setBrush(QBrush(QColor(255, 255, 255)))
            p.drawEllipse(QPointF(0, 0), z.r + 2, z.r + 2)
            p.setOpacity(1.0)

        # Body gradient
        grad = QRadialGradient(-z.r*0.3, -z.r*0.3, z.r*0.4, 0, 0, z.r)
        grad.setColorAt(0, QColor(z.c0))
        grad.setColorAt(1, QColor(z.c1))
        p.setBrush(QBrush(grad))

        if z.is_boss:
            p.setPen(QPen(QColor(255, 0, 0, 200), 3))
        elif z.explosive:
            p.setPen(QPen(QColor(255, 150, 0, 160), 2))
        elif z.ztype == "armored":
            p.setPen(QPen(QColor(100, 140, 180, 200), 2.5))
        else:
            p.setPen(QPen(QColor(180, 0, 0, 90), 1.5))

        p.drawEllipse(QPointF(0, 0), z.r, z.r)

        # Armor layer
        if z.is_armored and z.armor_hp > 0:
            pct = z.armor_hp / z.max_armor
            p.setOpacity(pct * 0.6)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(QColor(100, 150, 200, 200), 3))
            p.drawEllipse(QPointF(0, 0), z.r + 3, z.r + 3)
            p.setOpacity(1.0)

        # Eyes
        p.rotate(math.degrees(z.angle))
        p.setBrush(QBrush(QColor(255, 30, 0)))
        p.setPen(Qt.PenStyle.NoPen)
        er = 4.5 if z.is_boss else (3.5 if z.ztype == "tank" else 2.2)
        # Eye glow
        p.setOpacity(0.4)
        p.drawEllipse(QPointF(z.r*0.52, -z.r*0.28), er + 3, er + 3)
        p.drawEllipse(QPointF(z.r*0.52,  z.r*0.28), er + 3, er + 3)
        p.setOpacity(1.0)
        p.drawEllipse(QPointF(z.r*0.52, -z.r*0.28), er, er)
        p.drawEllipse(QPointF(z.r*0.52,  z.r*0.28), er, er)

        p.restore()

        # HP bar
        if z.hp < z.max_hp:
            bw = z.r * 2.5
            hp_pct = max(0, z.hp / z.max_hp)
            p.fillRect(QRectF(sx - bw/2, sy - z.r - 11, bw, 4), QColor(25,25,25))
            if hp_pct > 0.6:   hc = QColor(50, 200, 50)
            elif hp_pct > 0.3: hc = QColor(220, 200, 0)
            else:               hc = QColor(220, 40, 40)
            p.fillRect(QRectF(sx - bw/2, sy - z.r - 11, bw * hp_pct, 4), hc)
            if z.is_armored and z.armor_hp > 0:
                p.fillRect(QRectF(sx - bw/2, sy - z.r - 16, bw * (z.armor_hp/z.max_armor), 3), QColor(100,160,220))

        # Labels
        if z.is_boss or z.ztype in ("tank", "armored"):
            lbl = "BOSS" if z.is_boss else z.ztype.upper()
            col = QColor(255, 80, 0) if z.is_boss else QColor(160, 160, 200)
            p.setPen(QPen(col))
            f = QFont("Courier New", 7, QFont.Weight.Bold)
            p.setFont(f)
            p.drawText(QRectF(sx - 20, sy - 5, 40, 14), Qt.AlignmentFlag.AlignCenter, lbl)

    def _draw_player(self, p: QPainter, eng: GameEngine, ws, W, H):
        if not eng.player.alive: return
        pl = eng.player
        sx, sy = ws(pl.x, pl.y)

        p.save()
        p.translate(sx, sy)

        # Shadow
        p.setOpacity(0.3)
        p.setBrush(QBrush(QColor(0,0,0)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QRectF(-pl.r*0.9+3, pl.r*0.3+4, pl.r*1.8, pl.r*0.75))
        p.setOpacity(1.0)

        # Rage glow
        if pl.rage > 60:
            rg = int(pl.rage * 2)
            p.setOpacity(0.25 + pl.rage / 400)
            glow_col = QColor(255, max(0, 100 - rg), 0)
            p.setBrush(QBrush(glow_col))
            p.drawEllipse(QPointF(0, 0), pl.r + 8 + math.sin(eng.frame * 0.15) * 3, pl.r + 8)
            p.setOpacity(1.0)

        # Dash trail
        if pl.is_dashing:
            p.setOpacity(0.3)
            p.setBrush(QBrush(C.CYAN))
            p.drawEllipse(QPointF(0, 0), pl.r + 6, pl.r + 6)
            p.setOpacity(1.0)

        # Body
        grad = QRadialGradient(-pl.r*0.3, -pl.r*0.3, pl.r*0.45, 0, 0, pl.r)
        grad.setColorAt(0, QColor(90, 180, 90))
        grad.setColorAt(1, QColor(30, 90, 40))
        p.setBrush(QBrush(grad))
        p.setPen(QPen(QColor(20, 55, 20), 2))
        p.drawEllipse(QPointF(0, 0), pl.r, pl.r)

        # Highlight
        p.setOpacity(0.12)
        p.setBrush(QBrush(QColor(255,255,255)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(-pl.r*0.3, -pl.r*0.3), pl.r*0.45, pl.r*0.45)
        p.setOpacity(1.0)

        # Level badge
        if pl.level > 1:
            p.setPen(QPen(C.YELLOW))
            f = QFont("Courier New", max(7, 6 + pl.level // 2), QFont.Weight.Bold)
            p.setFont(f)
            p.drawText(QRectF(-10, -8, 20, 16), Qt.AlignmentFlag.AlignCenter, str(pl.level))

        # Gun
        p.rotate(math.degrees(pl.angle))
        p.setBrush(QBrush(QColor(120, 120, 120)))
        p.setPen(QPen(QColor(60, 60, 60), 1))
        p.drawRect(QRectF(pl.r*0.2, -4, 20, 8))
        p.setBrush(QBrush(QColor(80, 80, 80)))
        p.drawRect(QRectF(pl.r*0.2 + 14, -3, 10, 6))
        if pl.clip == 0:
            p.setBrush(QBrush(QColor(220, 40, 0)))
            p.drawRect(QRectF(pl.r*0.2, 3, 20, 2))

        p.restore()

        # Reload bar
        if pl.reload_time > 0:
            pct = (90 - pl.reload_time) / 90
            p.fillRect(QRectF(sx - 22, sy + pl.r + 6, 44, 5), QColor(30,30,30))
            p.fillRect(QRectF(sx - 22, sy + pl.r + 6, 44 * pct, 5), QColor(255, 180, 0))

    def _draw_particles(self, p: QPainter, eng: GameEngine, cx, cy):
        W, H = self.width(), self.height()
        for pt in eng.particles:
            sx, sy = self._world_to_screen(pt.x, pt.y, cx, cy)
            if sx < -20 or sx > W+20 or sy < -20 or sy > H+20: continue
            a = pt.life / pt.max_life
            col = QColor(pt.color)
            col.setAlphaF(a)
            p.setBrush(QBrush(col))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(sx, sy), pt.r * a, pt.r * a)
        p.setOpacity(1.0)

    def _draw_float_texts(self, p: QPainter, eng: GameEngine, cx, cy):
        W, H = self.width(), self.height()
        for ft in eng.float_texts:
            sx, sy = self._world_to_screen(ft.x, ft.y, cx, cy)
            if sx < -50 or sx > W+50 or sy < -50 or sy > H+50: continue
            a = ft.life / 60.0
            col = QColor(ft.color)
            col.setAlphaF(a)
            p.setPen(QPen(col))
            f = QFont("Courier New", 11, QFont.Weight.Bold)
            p.setFont(f)
            p.drawText(QRectF(sx - 60, sy - 8, 120, 20), Qt.AlignmentFlag.AlignCenter, ft.text)

    def _draw_hud(self, p: QPainter, eng: GameEngine, W, H):
        pl = eng.player
        # Top bar background
        grad = QLinearGradient(0, 0, 0, 56)
        grad.setColorAt(0, QColor(0, 0, 0, 200))
        grad.setColorAt(1, QColor(0, 0, 0, 0))
        p.fillRect(0, 0, W, 56, QBrush(grad))

        # Resources
        icons = [("🍖", eng.inv.get("food",0), C.FOOD_CLR),
                 ("🔫", eng.inv.get("ammo",0), C.AMMO_CLR),
                 ("🪵", eng.inv.get("wood",0), C.WOOD_CLR),
                 ("💊", eng.inv.get("medicine",0), C.MED_CLR)]
        p.setFont(QFont("Segoe UI Emoji", 13))
        ef = QFont("Courier New", 10, QFont.Weight.Bold)
        xoff = 12
        for icon, val, col in icons:
            p.setFont(QFont("Segoe UI Emoji", 13))
            p.drawText(QRectF(xoff, 8, 22, 22), Qt.AlignmentFlag.AlignCenter, icon)
            p.setFont(ef)
            p.setPen(QPen(col))
            p.drawText(QRectF(xoff + 22, 12, 36, 16), Qt.AlignmentFlag.AlignLeft, str(val))
            xoff += 66

        # Wave + diff badge (center)
        diff_col = eng.diff["color"]
        p.setFont(QFont("Courier New", 14, QFont.Weight.Bold))
        if eng.between_waves:
            secs = math.ceil(eng.wave_countdown / FPS)
            wtext = f"NEXT WAVE {eng.wave + 1} IN {secs}s"
            p.setPen(QPen(QColor(180, 180, 60)))
        elif eng.wave % 5 == 0 and eng.wave_active:
            wtext = f"⚠ BOSS WAVE {eng.wave}"
            p.setPen(QPen(QColor(255, 40, 0)))
        else:
            wtext = f"WAVE {eng.wave}"
            p.setPen(QPen(C.RED))
        p.drawText(QRectF(W/2 - 150, 10, 300, 22), Qt.AlignmentFlag.AlignCenter, wtext)

        # Diff badge
        p.setFont(QFont("Courier New", 9))
        p.setPen(QPen(diff_col))
        p.drawText(QRectF(W - 80, 10, 70, 16), Qt.AlignmentFlag.AlignRight, f"[{eng.diff['name']}]")

        # Kills / Score
        p.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
        p.setPen(QPen(C.AMMO_CLR))
        p.drawText(QRectF(W - 200, 26, 188, 16), Qt.AlignmentFlag.AlignRight,
                   f"Kills:{eng.kills}  Score:{eng.score}")

        # ── HP Bar ──
        hp_w = min(300, int(W * 0.25))
        hp_x = W//2 - hp_w//2
        hp_y = H - 90
        p.fillRect(QRectF(hp_x - 1, hp_y - 1, hp_w + 2, 12), QColor(15,15,15))
        hp_pct = pl.hp / pl.max_hp
        if hp_pct > 0.6:   hc = QColor(50, 200, 60)
        elif hp_pct > 0.3: hc = QColor(220, 180, 0)
        else:               hc = QColor(220, 30, 30)
        hg = QLinearGradient(hp_x, hp_y, hp_x + hp_w, hp_y)
        hg.setColorAt(0, hc.darker(120))
        hg.setColorAt(1, hc)
        p.fillRect(QRectF(hp_x, hp_y, hp_w * hp_pct, 10), QBrush(hg))
        p.setPen(QPen(QColor(255,255,255,60), 1))
        p.drawRect(QRectF(hp_x - 1, hp_y - 1, hp_w + 2, 12))
        p.setFont(QFont("Courier New", 8, QFont.Weight.Bold))
        p.setPen(QPen(QColor(200,200,200)))
        p.drawText(QRectF(hp_x, hp_y - 14, hp_w, 12), Qt.AlignmentFlag.AlignCenter,
                   f"HP  {int(pl.hp)} / {int(pl.max_hp)}")

        # ── Ammo / Reload ──
        p.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
        if pl.reload_time > 0:
            pct = (90 - pl.reload_time) / 90
            p.setPen(QPen(QColor(255, 180, 40)))
            p.drawText(QRectF(hp_x, hp_y + 14, hp_w, 16),
                       Qt.AlignmentFlag.AlignCenter, f"RELOADING... {int(pct*100)}%")
        else:
            col = C.AMMO_CLR if pl.clip > 5 else C.RED
            p.setPen(QPen(col))
            p.drawText(QRectF(hp_x, hp_y + 14, hp_w, 16),
                       Qt.AlignmentFlag.AlignCenter,
                       f"{'|' * pl.clip}{'.' * (pl.max_clip - pl.clip)}  [{eng.inv.get('ammo',0)}]  LVL{pl.level}")

        # ── Rage meter ──
        if pl.rage > 5:
            rx, ry, rw = 16, H - 160, 90
            p.fillRect(QRectF(rx - 1, ry - 1, rw + 2, 10), QColor(15,15,15))
            rc = QColor(255, 0, 0) if pl.rage > 80 else QColor(255, 100, 0)
            p.fillRect(QRectF(rx, ry, rw * (pl.rage / 100), 8), rc)
            p.setFont(QFont("Courier New", 8))
            p.setPen(QPen(rc))
            p.drawText(QRectF(rx, ry - 13, rw, 11), Qt.AlignmentFlag.AlignLeft, "RAGE")

        # ── XP bar ──
        xp_needed = pl.level * 80
        xp_pct = pl.xp / xp_needed
        p.fillRect(QRectF(hp_x - 1, hp_y + 33, hp_w + 2, 6), QColor(15,15,15))
        xg = QLinearGradient(hp_x, hp_y+33, hp_x + hp_w, hp_y+33)
        xg.setColorAt(0, QColor(80, 60, 200))
        xg.setColorAt(1, QColor(160, 100, 255))
        p.fillRect(QRectF(hp_x, hp_y + 33, hp_w * xp_pct, 5), QBrush(xg))
        p.setFont(QFont("Courier New", 7))
        p.setPen(QPen(QColor(160, 140, 255)))
        p.drawText(QRectF(hp_x, hp_y + 41, hp_w, 11),
                   Qt.AlignmentFlag.AlignCenter, f"XP {int(pl.xp)}/{xp_needed}")

        # ── Grenades ──
        p.setFont(QFont("Segoe UI Emoji", 12))
        gx = W - 90
        gy = H - 90
        for i in range(pl.grenades):
            p.drawText(QRectF(gx + i * 22, gy, 22, 22),
                       Qt.AlignmentFlag.AlignCenter, "💣")
        p.setFont(QFont("Courier New", 8))
        p.setPen(QPen(QColor(200,200,100)))
        if pl.grenade_cd > 0:
            p.drawText(QRectF(gx, gy + 22, 80, 14), Qt.AlignmentFlag.AlignLeft,
                       f"RMB: {math.ceil(pl.grenade_cd/FPS)}s")

        # ── Dash cooldown ──
        p.setFont(QFont("Courier New", 8))
        p.setPen(QPen(C.CYAN))
        if pl.dash_cd > 0:
            p.drawText(QRectF(16, H - 180, 90, 14), Qt.AlignmentFlag.AlignLeft,
                       f"DASH: {math.ceil(pl.dash_cd/FPS)}s")
        else:
            p.drawText(QRectF(16, H - 180, 90, 14), Qt.AlignmentFlag.AlignLeft, "DASH: READY")

        # Build mode indicator
        if self.build_mode:
            p.setFont(QFont("Courier New", 11, QFont.Weight.Bold))
            p.setPen(QPen(C.GREEN))
            bg_rect = QRectF(W/2 - 140, 55, 280, 24)
            p.fillRect(bg_rect, QColor(0, 160, 0, 120))
            p.drawText(bg_rect, Qt.AlignmentFlag.AlignCenter, "🔨 BUILD MODE  [B] exit  Click to place")

        # Keys help (subtle, bottom left)
        p.setFont(QFont("Courier New", 8))
        p.setPen(QPen(QColor(80, 80, 80)))
        helps = ["WASD:Move", "H:Heal", "R:Reload", "B:Build", "Space:Dash", "RMB:Grenade"]
        for i, h in enumerate(helps):
            p.drawText(16, H - 20 - (len(helps) - 1 - i) * 14, h)

    def _draw_minimap(self, p: QPainter, eng: GameEngine, W, H):
        mw, mh = 110, 110
        mx, my = W - mw - 12, 44
        p.fillRect(QRectF(mx, my, mw, mh), QColor(0, 0, 0, 160))
        p.setPen(QPen(QColor(180, 0, 0, 80), 1))
        p.drawRect(QRectF(mx, my, mw, mh))
        sx_s = mw / W_WORLD; sy_s = mh / H_WORLD
        p.setPen(Qt.PenStyle.NoPen)
        for z in eng.zombies:
            col = QColor(255, 40, 40) if z.is_boss else QColor(200, 50, 50)
            p.setBrush(QBrush(col))
            zr = 3 if z.is_boss else 2
            p.drawEllipse(QPointF(mx + z.x*sx_s, my + z.y*sy_s), zr, zr)
        p.setBrush(QBrush(QColor(160, 100, 40)))
        for bar in eng.barricades:
            p.drawRect(QRectF(mx + bar.x*sx_s - 2, my + bar.y*sy_s - 1, 4, 2))
        p.setBrush(QBrush(QColor(220, 220, 80)))
        for pk in eng.pickups:
            if pk.ptype != "xp":
                p.drawRect(QRectF(mx + pk.x*sx_s - 1, my + pk.y*sy_s - 1, 2, 2))
        # Camera viewport rect
        cam_rx = mx + (eng.cam_x - W/2) * sx_s
        cam_ry = my + (eng.cam_y - H/2) * sy_s
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(255, 255, 255, 30), 1))
        p.drawRect(QRectF(cam_rx, cam_ry, W * sx_s, H * sy_s))
        # Player dot
        p.setBrush(QBrush(QColor(60, 255, 80)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(mx + eng.player.x*sx_s, my + eng.player.y*sy_s), 4, 4)
        # Minimap label
        p.setFont(QFont("Courier New", 7))
        p.setPen(QPen(QColor(80,80,80)))
        p.drawText(int(mx), int(my + mh + 12), "MINIMAP")

    def _draw_wave_info(self, p: QPainter, eng: GameEngine, W, H):
        if eng.between_waves:
            fade_frames = max(5, 10 - eng.wave // 3) * FPS
            if eng.wave_countdown > fade_frames - 60:
                a = min(1.0, (fade_frames - eng.wave_countdown + 60) / 60)
                p.setOpacity(a)
                p.setFont(QFont("Courier New", 32, QFont.Weight.Bold))
                p.setPen(QPen(C.RED))
                p.drawText(QRectF(0, H/2 - 30, W, 40), Qt.AlignmentFlag.AlignCenter,
                           f"WAVE {eng.wave} CLEARED")
                p.setFont(QFont("Courier New", 13))
                p.setPen(QPen(QColor(100, 100, 100)))
                p.drawText(QRectF(0, H/2 + 18, W, 22), Qt.AlignmentFlag.AlignCenter,
                           "Collect resources — next wave incoming")
                p.setOpacity(1.0)

    def _draw_boss_warning(self, p: QPainter, eng: GameEngine, W, H):
        if eng.wave_active and eng.wave % 5 == 0 and eng.frame < 200:
            a = abs(math.sin(eng.frame * 0.08)) * 0.85
            p.setOpacity(a)
            p.setFont(QFont("Courier New", 24, QFont.Weight.Bold))
            p.setPen(QPen(QColor(255, 20, 0)))
            p.drawText(QRectF(0, 80, W, 36), Qt.AlignmentFlag.AlignCenter, "⚠  BOSS WAVE  ⚠")
            p.setOpacity(1.0)


# ═══════════════════════════════════════════════════════════════════════════════
#  START SCREEN
# ═══════════════════════════════════════════════════════════════════════════════
class StartScreen(QWidget):
    start_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.selected_diff = "medium"
        self._frame = 0
        self._bg_particles = [{"x": random.uniform(0,1), "y": random.uniform(0,1),
                                "s": random.uniform(0.5,2.5), "v": random.uniform(0.0003, 0.001)}
                               for _ in range(80)]
        self._setup_ui()
        self._anim_timer = QTimer()
        self._anim_timer.timeout.connect(self._tick_anim)
        self._anim_timer.start(16)

    def _tick_anim(self):
        self._frame += 1
        for pt in self._bg_particles:
            pt["y"] -= pt["v"]
            if pt["y"] < 0: pt["y"] = 1.0; pt["x"] = random.uniform(0,1)
        self.update()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Transparent overlay widget for UI
        overlay = QWidget()
        overlay.setObjectName("overlay")
        overlay.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        ov_layout = QVBoxLayout(overlay)
        ov_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ov_layout.setSpacing(0)

        # Title
        title = QLabel("DEAD ZONE")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Courier New", 72, QFont.Weight.Black))
        title.setStyleSheet("color: #cc0000; letter-spacing: 6px;")
        ov_layout.addSpacing(60)
        ov_layout.addWidget(title)

        subtitle = QLabel("ZOMBIE SURVIVAL · WAVE DEFENSE · RESOURCE MANAGEMENT")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(QFont("Courier New", 11))
        subtitle.setStyleSheet("color: #444; letter-spacing: 3px; margin-top: 4px;")
        ov_layout.addWidget(subtitle)
        ov_layout.addSpacing(30)

        # How to play
        hints = QLabel(
            "<b>WASD</b>  Move  ·  <b>Mouse</b>  Aim  ·  <b>Click</b>  Shoot  ·  <b>RMB</b>  Grenade<br>"
            "<b>H</b>  Heal  ·  <b>B</b>  Build Barricade  ·  <b>R</b>  Reload  ·  <b>Space</b>  Dash<br>"
            "<span style='color:#333'>Collect resources · Survive 20 waves · Build defences</span>"
        )
        hints.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hints.setFont(QFont("Courier New", 11))
        hints.setStyleSheet("color: #555; line-height: 200%;")
        ov_layout.addWidget(hints)
        ov_layout.addSpacing(28)

        # Difficulty
        diff_label = QLabel("SELECT DIFFICULTY")
        diff_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        diff_label.setFont(QFont("Courier New", 10))
        diff_label.setStyleSheet("color: #444; letter-spacing: 3px;")
        ov_layout.addWidget(diff_label)
        ov_layout.addSpacing(10)

        diff_row = QHBoxLayout()
        diff_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        diff_row.setSpacing(10)
        self.diff_btns = {}
        for key, cfg in DIFFICULTIES.items():
            btn = QPushButton(cfg["name"])
            btn.setFixedSize(90, 36)
            btn.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            col = cfg["color"]
            cs = col.name()
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: #555;
                    border: 1px solid #333;
                    letter-spacing: 2px;
                }}
                QPushButton:hover {{
                    color: {cs};
                    border-color: {cs};
                    background: rgba(0,0,0,80);
                }}
                QPushButton:checked {{
                    color: {cs};
                    border: 2px solid {cs};
                    background: rgba(0,0,0,120);
                }}
            """)
            btn.clicked.connect(lambda _, k=key: self._select_diff(k))
            self.diff_btns[key] = btn
            diff_row.addWidget(btn)
        self.diff_btns["medium"].setChecked(True)
        ov_layout.addLayout(diff_row)
        ov_layout.addSpacing(26)

        # Start button
        start_btn = QPushButton("▶  SURVIVE")
        start_btn.setFixedSize(240, 56)
        start_btn.setFont(QFont("Courier New", 16, QFont.Weight.Black))
        start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        start_btn.setStyleSheet("""
            QPushButton {
                background: #aa0000;
                color: white;
                border: none;
                letter-spacing: 4px;
            }
            QPushButton:hover {
                background: #ee1111;
            }
            QPushButton:pressed {
                background: #ff4444;
            }
        """)
        start_btn.clicked.connect(lambda: self.start_requested.emit(self.selected_diff))

        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_row.addWidget(start_btn)
        ov_layout.addLayout(btn_row)
        ov_layout.addSpacing(20)

        # Scores display
        scores = load_scores()
        score_lbl = QLabel(
            f"HIGH SCORE: {scores['high_score']}  ·  "
            f"BEST WAVE: {scores['best_wave']}  ·  "
            f"TOTAL KILLS: {scores['total_kills']}"
        )
        score_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        score_lbl.setFont(QFont("Courier New", 9))
        score_lbl.setStyleSheet("color: #333; letter-spacing: 1px;")
        ov_layout.addWidget(score_lbl)
        ov_layout.addSpacing(8)

        # Credit
        credit = QLabel("Made with ❤️ by Sagittarius1 · PyQt6 Edition")
        credit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credit.setFont(QFont("Courier New", 8))
        credit.setStyleSheet("color: #282828;")
        ov_layout.addWidget(credit)
        ov_layout.addStretch()

        layout.addWidget(overlay)

    def _select_diff(self, key: str):
        self.selected_diff = key
        for k, btn in self.diff_btns.items():
            btn.setChecked(k == key)

    def paintEvent(self, e):
        p = QPainter(self)
        W, H = self.width(), self.height()

        # Deep black BG
        p.fillRect(0, 0, W, H, QColor(4, 4, 3))

        # Animated particles (dim stars)
        p.setPen(Qt.PenStyle.NoPen)
        for pt in self._bg_particles:
            px = int(pt["x"] * W)
            py = int(pt["y"] * H)
            s = pt["s"]
            a = int(random.uniform(30, 90))
            p.setBrush(QBrush(QColor(180, 40, 40, a)))
            p.drawEllipse(QPointF(px, py), s, s)

        # Vignette
        vig = QRadialGradient(W/2, H/2, max(W, H)*0.7)
        vig.setColorAt(0, QColor(0, 0, 0, 0))
        vig.setColorAt(1, QColor(0, 0, 0, 200))
        p.fillRect(0, 0, W, H, QBrush(vig))

        # Pulsing red border
        pulse = abs(math.sin(self._frame * 0.025)) * 0.5 + 0.3
        p.setPen(QPen(QColor(180, 0, 0, int(pulse * 120)), 4))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(4, 4, W - 8, H - 8)
        p.end()


# ═══════════════════════════════════════════════════════════════════════════════
#  GAME OVER SCREEN
# ═══════════════════════════════════════════════════════════════════════════════
class GameOverScreen(QWidget):
    restart_requested = pyqtSignal(str)
    menu_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.selected_diff = "medium"
        self._victory = False
        self._stats = {}
        self._setup_ui()

    def show_result(self, victory: bool, eng: GameEngine, selected_diff: str):
        self._victory = victory
        self.selected_diff = selected_diff
        self._stats = {
            "wave": eng.wave, "kills": eng.kills, "score": eng.score,
            "level": eng.player.level, "food": eng.inv.get("food", 0),
            "ammo": eng.inv.get("ammo", 0), "wood": eng.inv.get("wood", 0),
            "medicine": eng.inv.get("medicine", 0), "diff": eng.diff["name"]
        }
        scores = load_scores()
        new_hs = max(scores["high_score"], eng.score)
        new_bw = max(scores["best_wave"], eng.wave)
        scores["high_score"] = new_hs
        scores["best_wave"] = new_bw
        scores["total_kills"] = scores.get("total_kills", 0) + eng.kills
        save_scores(scores)
        self._rebuild_ui(scores)

    def _rebuild_ui(self, scores: dict):
        # Clear old layout
        old_layout = self.layout()
        if old_layout:
            while old_layout.count():
                item = old_layout.takeAt(0)
                if item.widget(): item.widget().deleteLater()
            QWidget().setLayout(old_layout)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(0)

        v = self._victory
        st = self._stats

        title = QLabel("SURVIVED!" if v else "YOU DIED")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Courier New", 64, QFont.Weight.Black))
        col = "#44ff88" if v else "#cc0000"
        title.setStyleSheet(f"color: {col};")
        layout.addSpacing(50)
        layout.addWidget(title)

        stats = QLabel(
            f"Wave: {st['wave']}  ·  Kills: {st['kills']}  ·  Score: {st['score']}<br>"
            f"<span style='color:#444'>Difficulty: {st['diff']}  ·  Level: {st['level']}</span>"
        )
        stats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats.setFont(QFont("Courier New", 14))
        stats.setStyleSheet("color: #777; margin-top: 6px;")
        layout.addWidget(stats)

        hs_lbl = QLabel(
            f"High Score: {scores['high_score']}  ·  "
            f"Best Wave: {scores['best_wave']}  ·  "
            f"Total Kills: {scores['total_kills']}"
        )
        hs_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hs_lbl.setFont(QFont("Courier New", 11))
        hs_lbl.setStyleSheet("color: #555; margin: 10px 0;")
        layout.addWidget(hs_lbl)
        layout.addSpacing(20)

        # Diff row
        diff_label = QLabel("SELECT DIFFICULTY")
        diff_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        diff_label.setFont(QFont("Courier New", 10))
        diff_label.setStyleSheet("color: #444; letter-spacing: 3px;")
        layout.addWidget(diff_label)
        layout.addSpacing(8)

        diff_row = QHBoxLayout()
        diff_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        diff_row.setSpacing(8)
        self.diff_btns = {}
        for key, cfg in DIFFICULTIES.items():
            btn = QPushButton(cfg["name"])
            btn.setFixedSize(88, 34)
            btn.setFont(QFont("Courier New", 10))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            cs = cfg["color"].name()
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; color: #555;
                    border: 1px solid #333; letter-spacing: 1px;
                }}
                QPushButton:hover {{ color: {cs}; border-color: {cs}; }}
                QPushButton:checked {{ color: {cs}; border: 2px solid {cs}; }}
            """)
            btn.clicked.connect(lambda _, k=key: self._select_diff(k))
            self.diff_btns[key] = btn
            diff_row.addWidget(btn)
        self.diff_btns[self.selected_diff].setChecked(True)
        layout.addLayout(diff_row)
        layout.addSpacing(24)

        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_row.setSpacing(16)

        retry_btn = QPushButton("↺  TRY AGAIN")
        retry_btn.setFixedSize(200, 52)
        retry_btn.setFont(QFont("Courier New", 14, QFont.Weight.Bold))
        retry_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        retry_btn.setStyleSheet("""
            QPushButton { background:#aa0000; color:white; border:none; letter-spacing:3px; }
            QPushButton:hover { background:#ee1111; }
        """)
        retry_btn.clicked.connect(lambda: self.restart_requested.emit(self.selected_diff))

        menu_btn = QPushButton("⌂  MAIN MENU")
        menu_btn.setFixedSize(200, 52)
        menu_btn.setFont(QFont("Courier New", 14, QFont.Weight.Bold))
        menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        menu_btn.setStyleSheet("""
            QPushButton { background:transparent; color:#666; border:2px solid #444; letter-spacing:3px; }
            QPushButton:hover { color:#aaa; border-color:#888; }
        """)
        menu_btn.clicked.connect(self.menu_requested.emit)

        btn_row.addWidget(retry_btn)
        btn_row.addWidget(menu_btn)
        layout.addLayout(btn_row)
        layout.addStretch()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def _select_diff(self, key: str):
        self.selected_diff = key
        for k, btn in self.diff_btns.items():
            btn.setChecked(k == key)

    def paintEvent(self, e):
        p = QPainter(self)
        W, H = self.width(), self.height()
        p.fillRect(0, 0, W, H, QColor(4, 4, 3, 240))
        vig = QRadialGradient(W/2, H/2, max(W,H)*0.7)
        vig.setColorAt(0, QColor(0,0,0,0))
        vig.setColorAt(1, QColor(0,0,0,220))
        p.fillRect(0, 0, W, H, QBrush(vig))
        p.end()


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ═══════════════════════════════════════════════════════════════════════════════
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DEAD ZONE — Zombie Survival")
        self.setMinimumSize(1024, 640)
        self.resize(SCREEN_W, SCREEN_H)
        self.setStyleSheet("QMainWindow { background: #040403; }")

        self.engine: Optional[GameEngine] = None
        self.selected_diff = "medium"

        # Central stacked widget
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Screens
        self.start_screen = StartScreen()
        self.game_canvas = GameCanvas()
        self.go_screen = GameOverScreen()

        self.stack.addWidget(self.start_screen)   # 0
        self.stack.addWidget(self.game_canvas)    # 1
        self.stack.addWidget(self.go_screen)      # 2

        # Signals
        self.start_screen.start_requested.connect(self.start_game)
        self.go_screen.restart_requested.connect(self.start_game)
        self.go_screen.menu_requested.connect(self.show_menu)

        # Game timer
        self.timer = QTimer()
        self.timer.timeout.connect(self._game_tick)

        self.stack.setCurrentIndex(0)

    def start_game(self, diff_key: str):
        self.selected_diff = diff_key
        self.engine = GameEngine(diff_key)
        self.game_canvas.set_engine(self.engine)
        self.game_canvas.build_mode = False
        self.game_canvas.keys.clear()
        self.stack.setCurrentIndex(1)
        self.game_canvas.setFocus()
        self.timer.start(1000 // FPS)

    def show_menu(self):
        self.timer.stop()
        self.engine = None
        self.stack.setCurrentIndex(0)

    def _game_tick(self):
        if not self.engine: return
        self.game_canvas.game_tick()
        if self.engine.game_over:
            self.timer.stop()
            self.go_screen.show_result(self.engine.victory, self.engine, self.selected_diff)
            self.stack.setCurrentIndex(2)


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Dead Zone")
    app.setApplicationDisplayName("DEAD ZONE — Zombie Survival")

    # Dark palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(4, 4, 3))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(220, 220, 200))
    palette.setColor(QPalette.ColorRole.Base, QColor(10, 10, 8))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(20, 20, 16))
    palette.setColor(QPalette.ColorRole.Button, QColor(30, 30, 24))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(200, 200, 180))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(160, 0, 0))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
