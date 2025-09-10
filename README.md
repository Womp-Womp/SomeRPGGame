# AstraRPG — Discord (Pycord) + CLI | Procedural Dark‑Fantasy RPG

**Tone & World:** Serious **dark fantasy** (D\&D × Warhammer Fantasy × Weird Custom). Central world name (working): **The Abysm of Karth**.

**Modality:** Command-only. Exact same commands in **CLI** and **Discord** (via **Pycord**).

**Generation Doctrine:**

* **Numeric & Logic:** **Deterministic** procedural systems with per‑character seeds.
* **Non‑numeric flavor (names, epitaphs, room prose, item descriptions):** **Gemini 2.5 Flash** (cheap flavor), with fallbacks.
* **Maps:** numeric graph only (no LLM); ASCII/Unicode rendering for parity in terminal & Discord.

**MVP Scope (must-have):**

* `!attack`, `!fish`, `!stats`, `!inv`, `!equip`, `!help`, `!zone`, `!travel`
* Economy: `!buy`, `!sell`
* Farming core loop: `!farm` with subcommands **and genetics as MVP**
* Skill tree (basic) — numeric graph + unlocks
* Lootboxes (3–4 deterministic options, in-game currency only)
* Base building: grid with layers (ASCII/Unicode), everything lootbox-fed
* Pets & husbandry (beast-type enemies → tame & breed)

**Later (not MVP):** Diplomacy, monetization/scale, KPIs/telemetry, expense tracking for LLM.

---

## 0) Quickstart: Check Your Python Version (Local vs Cloud)

### CLI checks

```bash
python --version           # macOS/Linux default
python3 --version          # macOS/Linux alt
py --version               # Windows launcher (if installed)
```

### Programmatic check

```python
import sys
print(sys.version)
```

**Recommended:** Python **3.11+**. If juggling versions, use **pyenv** (macOS/Linux) or **pyenv-win**.

---

## 1) Project Layout

```
astrarpg/
  engine/
    __init__.py
    models.py          # Player, Monster, Item, Trait, Pet, SkillNode, etc.
    generation.py      # seeded RNG, numeric rolls, loot tables, genetics, map graph
    combat.py          # deterministic combat math & outcomes
    economy.py         # !buy, !sell, vendor stock, rarity, offers (3–4 choices)
    farming.py         # plots, crops, genetics (alleles), breeding
    pets.py            # taming, traits, breeding rules
    skilltree.py       # graph, unlock checks, serialization
    basebuilding.py    # layered grid, placements, adjacency effects
    commands.py        # command dispatch: attack/fish/farm/... shared by both adapters
    formatters.py      # colossal-number display (log/log), ascii UI helpers
    persistence.py     # SQLite access (schema migrations, repositories)
  adapters/
    cli.py             # stdin/stdout runner
    discord_bot.py     # Pycord bot wrapper
  genai/
    client.py          # Gemini wrapper (google-genai)
    prompts.py         # prompt templates
  config.py            # env parsing, flags, cooldowns, seeds
  requirements.txt
  README.md (this)
```

**Tenet:** *Pure engine + thin adapters.* Everything testable. Discord & CLI call the same dispatcher.

---

## 2) Install & Run

### Dependencies

```txt
# requirements.txt
py-cord>=2.5.0
pydantic>=2.8.0
google-genai
python-dotenv>=1.0.0
sqlalchemy>=2.0.0
alembic>=1.13.0     # optional for schema migrations
```

### Environment (.env)

```env
DISCORD_BOT_TOKEN=YOUR_DISCORD_TOKEN
GEMINI_API_KEY=YOUR_GEMINI_KEY
ASTRARPG_DB_URL=sqlite:///astrarpg.db
ASTRARPG_ENV=dev
ASTRARPG_DEFAULT_TEMPERATURE=0.9
ASTRARPG_THINKING_BUDGET=-1
```

### Setup

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -U pip
pip install -r requirements.txt
```

### Run CLI

```bash
python -m astrarpg.adapters.cli
```

### Run Discord (Pycord)

```bash
python -m astrarpg.adapters.discord_bot
```

---

## 3) Deterministic Seeds (per Character)

* Seed source: `seed = SHA256(f"{player_id}:{namespace}:{salt}")`
* Use **separate namespaces** (e.g., `monster`, `lootbox`, `farm`, `map`, `pet`, `skill`) to ensure independence.
* Derive `random.Random(int(seed[:16], 16))` for stable, fast PRNG.

```python
# engine/generation.py (excerpt)
import hashlib, random

def make_seed(*parts) -> int:
    s = ":".join(map(str, parts))
    return int(hashlib.sha256(s.encode()).hexdigest()[:16], 16)

def rng_for(*parts) -> random.Random:
    return random.Random(make_seed(*parts))
```

---

## 4) Gemini Usage (Non‑Numeric Flavor Only)

We keep numeric logic deterministic. Gemini decorates text: names, epithets, one‑liners, shopkeeper barks. Fallback to deterministic strings on error/timeouts.

**Wrapper using your library (`google-genai`)**

```python
# genai/client.py
import os
from google import genai
from google.genai import types
from ..config import GEMINI_API_KEY, DEFAULT_TEMPERATURE, THINKING_BUDGET

class GeminiClient:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model = "gemini-2.5-flash"

    def text(self, user_text: str, system_text: str = "You are a safe, evocative dark‑fantasy flavor generator. Keep outputs short, PG-13, and setting-consistent.") -> str:
        contents = [types.Content(role="user", parts=[types.Part.from_text(text=user_text)])]
        cfg = types.GenerateContentConfig(
            temperature=DEFAULT_TEMPERATURE,
            thinking_config=types.ThinkingConfig(thinking_budget=THINKING_BUDGET),
            system_instruction=[types.Part.from_text(text=system_text)],
        )
        out = []
        for chunk in self.client.models.generate_content_stream(
            model=self.model,
            contents=contents,
            config=cfg,
        ):
            if chunk.text:
                out.append(chunk.text)
        return "".join(out).strip()
```

**Prompt templates**

```python
# genai/prompts.py
WORLD_NAME = "The Abysm of Karth"

FLAVOR_MONSTER = (
    "Generate a short dark‑fantasy monster name and one-sentence epithet.\n"
    "World: {world}. Biome: {biome}. Tier: {tier}. Theme: {theme}.\n"
    "Format: <NAME>\n<DESC>\nKeep numeric stats OUT."
)

FLAVOR_SHOP = (
    "You are a grim shopkeep in {world}. Provide a 1-line greeting, atmospheric, no stats."
)

FLAVOR_ZONE = (
    "Name a zone in {world} with the style {style}, biome {biome}, tier {tier}. One line only."
)
```

**Example: generating a monster name/epithet during `!attack`**

```python
# engine/commands.py (excerpt)
from ..genai.client import GeminiClient
from ..genai.prompts import FLAVOR_MONSTER, WORLD_NAME

_gem = None

def gem():
    global _gem
    if _gem is None:
        _gem = GeminiClient()
    return _gem

# inside cmd_attack loop
try:
    text = gem().text(FLAVOR_MONSTER.format(world=WORLD_NAME, biome="void-sea", tier=zone, theme="leviathan"))
    if text:
        first, *_ = text.splitlines()
        mon.name = first.strip() or mon.name
except Exception:
    pass
```

---

## 5) SQLite Persistence (Permanent Progression)

SQLite first, then optional Postgres later. Use SQLAlchemy for portability.

**Schema (minimal MVP)**

```sql
-- migrations/001_init.sql
CREATE TABLE IF NOT EXISTS player (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  level INTEGER NOT NULL DEFAULT 1,
  xp INTEGER NOT NULL DEFAULT 0,
  hp INTEGER NOT NULL DEFAULT 20,
  hp_max INTEGER NOT NULL DEFAULT 20,
  atk INTEGER NOT NULL DEFAULT 5,
  df INTEGER NOT NULL DEFAULT 2,
  crit REAL NOT NULL DEFAULT 0.05,
  gold INTEGER NOT NULL DEFAULT 0,
  zone_id INTEGER NOT NULL DEFAULT 1,
  seed_namespace TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS inventory (
  player_id TEXT NOT NULL,
  item_id TEXT NOT NULL,
  qty INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (player_id, item_id)
);

CREATE TABLE IF NOT EXISTS item (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  slot TEXT,           -- weapon, armor, trinket, seed, livestock, etc.
  rarity INTEGER NOT NULL DEFAULT 1,
  meta JSON
);

CREATE TABLE IF NOT EXISTS skill_node (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  tier INTEGER NOT NULL,
  meta JSON
);

CREATE TABLE IF NOT EXISTS skill_edge (
  from_id TEXT NOT NULL,
  to_id TEXT NOT NULL,
  cost INTEGER NOT NULL DEFAULT 1,
  PRIMARY KEY (from_id, to_id)
);

CREATE TABLE IF NOT EXISTS pet (
  id TEXT PRIMARY KEY,
  owner_id TEXT NOT NULL,
  name TEXT NOT NULL,
  traits JSON NOT NULL,
  meta JSON
);

CREATE TABLE IF NOT EXISTS farm_plot (
  id TEXT PRIMARY KEY,
  owner_id TEXT NOT NULL,
  layer INTEGER NOT NULL DEFAULT 0,
  x INTEGER NOT NULL,
  y INTEGER NOT NULL,
  crop JSON,
  meta JSON
);
```

**Repository helper (Python)**

```python
# engine/persistence.py (excerpt)
from sqlalchemy import create_engine, text
from ..config import DB_URL

engine = create_engine(DB_URL, future=True)

def fetch_player(pid: str):
    with engine.connect() as c:
        row = c.execute(text("SELECT * FROM player WHERE id=:id"), {"id": pid}).mappings().first()
        return dict(row) if row else None

def upsert_player(d: dict):
    cols = ",".join(d.keys())
    params = ":"+", :".join(d.keys())
    with engine.begin() as c:
        c.execute(text(f"""
        INSERT INTO player ({cols}) VALUES ({params})
        ON CONFLICT(id) DO UPDATE SET
        {', '.join(f'{k}=excluded.{k}' for k in d.keys() if k!='id')}
        """), d)
```

---

## 6) Commands (MVP)

### Universal

* `!help` — list commands
* `!stats` — level / HP / ATK / DEF / Crit / Gold / Zone
* `!inv` — inventory listing (paginated)
* `!equip <item>` — equip by ID or name
* `!zone` — show zone info; `!travel <zone>` to move

### Combat

* `!attack <zone> <times>` — N iterative combats in zone

### Fishing

* `!fish` — present four ASCII fish options; `!fish a|b|c|d` to pick

### Economy

* `!buy` — offers (3–4 choices), prices scale by seed, zone, and reputation
* `!sell` — present inventory candidates, choose which to sell

### Farming (MVP with Genetics)

* `!farm` — shows farm summary and subcommands
* `!farm plant <seed_id> (x y)`
* `!farm harvest (x y)`
* `!farm cross <plantA> <plantB>` — creates `seed` items with **genetic recombination**
* `!farm info <plant|seed>` — inspects genotype/phenotype

### Lootboxes (in‑game currency only)

* `!lootbox` — opens a box presenting **3–4 deterministic** choices; pick one.

### Pets & Husbandry

* `!tame <monster>` — attempt to tame eligible beasts after combat
* `!stable` — list pets; `!breed <petA> <petB>`

---

## 7) Colossal Numbers (Leviathan Growth)

We display stats using hybrid notations and log/log linearization for UI.

```python
# engine/formatters.py
import math

def format_big(n: float) -> str:
    if n == 0: return "0"
    if abs(n) < 1e6:
        return f"{n:.0f}"
    # scientific with suffix
    exp = int(math.floor(math.log10(abs(n))))
    mant = n / (10**exp)
    return f"{mant:.2f}e{exp}"

def format_loglog(n: float) -> str:
    if n <= 1: return "0"
    return f"loglog={math.log(math.log(n, 10), 10):.4f}"
```

Use **internal linear math**; only **display** applies notation. Avoid floating overflow by keeping core on integers and capping multipliers, or operate in log-space when needed.

---

## 8) Deterministic Lootboxes (3–4 Choices)

```python
# engine/economy.py (excerpt)
from .generation import rng_for

def lootbox_options(player_id: str, box_id: str):
    rng = rng_for("lootbox", player_id, box_id)
    k = rng.choice([3,4])
    options = []
    for i in range(k):
        rarity = rng.choices([1,2,3,4,5],[70,20,7,2,1])[0]
        item_id = f"itm_{box_id}_{i}_{rarity}"
        options.append({"item_id": item_id, "rarity": rarity})
    return options
```

* Present options with names via **Gemini** (non‑numeric) or deterministic fallback.

---

## 9) Farming with Genetics (MVP)

Model plants and beasts as **trait vectors**. Each trait has alleles `A/a`, dominance tables, and random mutation with tiny probability.

```python
# engine/farming.py (excerpt)
from .generation import rng_for

TRAITS = {
  "yield": {"dominant":"H","recessive":"h"},
  "hardiness": {"dominant":"R","recessive":"r"},
  "growth": {"dominant":"G","recessive":"g"},
}

def cross_allele(a1: str, a2: str, b1: str, b2: str, rng):
    from_a = rng.choice([a1,a2]); from_b = rng.choice([b1,b2])
    return from_a+from_b

def phenotype(genotype: dict[str,str]):
    ph = {}
    for t, alleles in TRAITS.items():
        g = genotype[t]
        dom = alleles["dominant"]
        # dominance if any allele is uppercase dom
        ph[t] = 1 if dom in g else 0
    return ph

def cross(parentA: dict, parentB: dict, player_id: str, seed_salt: str):
    rng = rng_for("farm_cross", player_id, seed_salt)
    child = {}
    for t in TRAITS:
        a1,a2 = parentA[t][0], parentA[t][1]
        b1,b2 = parentB[t][0], parentB[t][1]
        g = cross_allele(a1,a2,b1,b2,rng)
        # tiny mutation chance
        if rng.random() < 0.005:
            g = g.swapcase()
        child[t] = g
    return {"genotype": child, "phenotype": phenotype(child)}
```

**Farming commands** render a layer grid with crops on coordinates. Growth ticks are numeric and deterministic per tick seed.

---

## 10) Pets & Husbandry

* Some monsters flagged **Beast** → eligible for taming.
* Taming chance is deterministic by player seed, zone, and monster blueprint.
* Pets have genetic traits similar to farming; breeding yields heritable stats (non‑numeric flavor from Gemini).

```python
# engine/pets.py (excerpt)
from .generation import rng_for

def taming_roll(player_id: str, monster_blueprint: str, zone: int):
    rng = rng_for("tame", player_id, monster_blueprint, zone)
    return rng.random() < 0.12  # tune later
```

---

## 11) Base Building (Layered Grid)

* **Grid coordinates (x,y)** per **layer** (z). Each cell stores a tile code.
* Render deterministically with ASCII/Unicode. Example tiles: `.` empty, `#` wall, `≈` water, `♣` grove, `⌂` hut.

```python
# engine/basebuilding.py (excerpt)

def render_layer(cells: dict[tuple[int,int], str], w: int, h: int) -> str:
    lines = []
    for y in range(h):
        row = []
        for x in range(w):
            row.append(cells.get((x,y), "."))
        lines.append("".join(row))
    return "\n".join(lines)
```

**Example Output (Layer 0)**

```
..........
..♣♣....≈≈.
..♣⌂..##≈≈.
..♣♣..##≈≈.
..........
```

---

## 12) Skill Tree (Graph, Numeric)

* Store nodes & edges in SQLite. Unlock checks are deterministic functions of XP, items, and prior unlocks.
* Rendering: ASCII summary; Discord embeds later.

```python
# engine/skilltree.py (excerpt)

def can_unlock(player, node, owned_nodes):
    return player.level >= node["tier"] and node["id"] not in owned_nodes
```

---

## 13) Command Dispatch (Shared between CLI & Discord)

```python
# engine/commands.py (skeleton)
from .models import Player
from .generation import rng_for
from .combat import fight
from .economy import lootbox_options

HELP = "!attack <zone> <times> | !fish [a|b|c|d] | !stats | !inv | !equip <item> | !buy | !sell | !farm | !lootbox | !zone | !travel <z>"

def dispatch(user_id: str, raw: str, player: Player) -> str:
    if not raw.startswith("!"): return "Commands start with !. Try !help."
    parts = raw.strip().split()
    cmd, args = parts[0].lower(), parts[1:]
    if cmd == "!help": return HELP
    if cmd == "!stats": return f"LVL {player.level} HP {player.hp}/{player.hp_max} ATK {player.atk} DEF {player.df} GOLD {player.gold} ZONE {player.zone_id}"
    # ... wire the rest (attack, fish, buy/sell, farm, lootbox, pets, base)
    return "Unknown command. Try !help."
```

---

## 14) Pycord Adapter (Discord)

````python
# adapters/discord_bot.py
import discord
from discord.ext import commands
from ..engine.models import Player
from ..engine.commands import dispatch
from ..config import DISCORD_BOT_TOKEN

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

PLAYERS = {}

def get_player(uid: str):
    p = PLAYERS.get(uid)
    if p: return p
    p = Player(id=uid, name=f"Hero-{uid[:6]}")
    PLAYERS[uid] = p
    return p

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (id {bot.user.id})")

@bot.listen("on_message")
async def on_message(msg: discord.Message):
    if msg.author.bot: return
    if not msg.content.startswith("!"): return
    player = get_player(str(msg.author.id))
    out = dispatch(player.id, msg.content, player)
    if len(out) > 1800: out = out[:1800] + "\n...(truncated)"
    await msg.channel.send(f"```
{out}
```")

bot.run(DISCORD_BOT_TOKEN)
````

---

## 15) CLI Adapter

```python
# adapters/cli.py
import sys
from ..engine.models import Player
from ..engine.commands import dispatch

def main():
    player = Player(id="cli_user", name="CLI Hero")
    print("AstraRPG CLI. Type commands like !attack 10000 1, !fish, !stats.")
    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        out = dispatch(player.id, line, player)
        print(out)

if __name__ == "__main__":
    main()
```

---

## 16) Combat Math (Deterministic)

```python
# engine/combat.py
import math
from .generation import rng_for

DEF_COEFF = 0.7
CRIT_BASE = 0.05
CRIT_MULT = 2.0

def roll_damage(atk, df, rng):
    base = max(1.0, atk - DEF_COEFF * df)
    var = rng.uniform(0.9, 1.1)
    return max(1, math.floor(base * var))

def fight(player, monster, salt: str):
    rng = rng_for("combat", player.id, monster.name, salt)
    p_hp, m_hp = player.hp, monster.hp
    log = []
    rounds = 0
    while p_hp > 0 and m_hp > 0 and rounds < 50:
        pd = roll_damage(player.atk, monster.df, rng)
        m_hp -= pd
        log.append(f"You hit {monster.name} for {pd}. {max(m_hp,0)} HP left.")
        if m_hp <= 0: break
        md = roll_damage(monster.atk, player.df, rng)
        p_hp -= md
        log.append(f"{monster.name} hits you for {md}. {max(p_hp,0)} HP left.")
        rounds += 1
    outcome = "win" if m_hp <= 0 and p_hp > 0 else ("loss" if p_hp <= 0 else "draw")
    return outcome, p_hp, m_hp, log
```

---

## 17) ASCII Fish Mini‑Game

```python
# inside commands
FISH = {"a": "><(((('>", "b": "<º)))><", "c": "Ͽ(°Ɐ°)Ͼ", "d": ">))'>    ~~~"}
```

```
The river glints. Which fish do you snag?
!a   ><(((('>
!b   <º)))><
!c   Ͽ(°Ɐ°)Ͼ
!d   >))'>    ~~~
```

---

## 18) Expense Tracking (Later)

* Log Gemini token counts and response sizes.
* Add a `LLM_BUDGET_DAILY` env to short‑circuit flavor requests after a threshold.

---

## 19) Moderation

* Rely on Gemini moderation for flavor. We also keep a local hard blocklist for slurs; fallback to deterministic strings on violation.

---

## 20) Roadmap (Opinionated)

1. **Stabilize seeds + numeric tables** (combat, economy, farming growth)
2. **Finish farming genetics UI** (clear `!farm` feedback, phenotypes)
3. **Skill tree v1** (5–7 nodes, 2 tiers)
4. **Lootboxes** (3–4 choices with reliable fallbacks)
5. **Base building layer 0** (place, remove, render) → layers 1–2
6. Pets & breeding parity with farming traits
7. CLI/Discord parity tests; cooldowns & soft flood limits
8. Zone graph traversal mechanics (hazards, gates)
9. Tuning for **colossal numbers** + notations
10. Optional: KPIs/metrics, dashboards, delayed monetization

---

## TL;DR

* **Pycord + CLI** adapters over a **pure engine**.
* **SQLite** for permanent progression.
* **Deterministic seeds per character** for all numeric logic.
* **Gemini for flavor only**; maps & stats purely numeric.
* MVP includes **farming with genetics**, **lootboxes (3–4 choices)**, **skill tree**, **base building layers**, **pets & husbandry**.
* Colossal numbers displayed via scientific/log‑log notations, keeping core math stable.
