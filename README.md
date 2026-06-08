# Last Bastion

> A post-apocalyptic medieval fantasy idle game built in Godot 4.x.
> My second game -- first Godot project built from scratch, no tutorials.

Built by [@lel1guy](https://github.com/lel1guy) from Quarteira, Algarve, Portugal

---

## The World

The world has collapsed. Civilization is in ruins, overrun by skeletons, zombies, orcs, and demons. You are the **last bastion** -- managing a crumbling stronghold, scavenging for scraps, farming what little food remains, and hiring archers to hold back the ever-growing horde.

Survive. Upgrade. Endure.

---

## What's In It

- **Click-to-fight combat** -- tap enemies to deal damage
- **Archer system** -- recruit and upgrade archers that fight automatically
- **Resource management** -- collect Gold, Scrap, and Food
- **Room unlocks** -- Storeroom, Farm, and more to expand your base
- **Upgrade tree** -- improve scavenging, farming, combat damage, and more
- **Auto-save** -- every 60 seconds and on app close (JSON-based)
- **Android support**

---

## Built With

- [Godot 4](https://godotengine.org/) -- game engine
- GDScript -- scripting language

---

## Run It

```bash
git clone https://github.com/lel1guy/LastBastion.git
```

Open Godot 4 -> **Import** -> select `project.godot` -> **F5** to run.

---

## Project Structure

```
LastBastion/
+-- Assets/          # Sprites, animations, audio
+-- Scenes/          # Godot scene files (.tscn)
+-- Scripts/         # GDScript files
|   +-- GameManager.gd   # Autoload -- global state & signals
|   +-- Game.gd          # Main game scene logic
|   +-- Mob.gd           # Base mob class
|   +-- archer.gd        # Archer unit logic
|   +-- arrow.gd         # Projectile logic
|   +-- upgrade_item.gd  # Individual upgrade UI + logic
|   +-- upgrades.gd      # Upgrades container
|   +-- resources.gd     # Resource display UI
|   +-- main.gd          # Entry point / scene switcher
+-- Save&Load.gd     # Autoload -- save/load system (JSON)
+-- project.godot
```

---

## Roadmap

- [ ] More mob types and stages
- [ ] Prestige / reset system
- [ ] Offline progression (idle income while closed)
- [ ] Sound effects & background music
- [ ] Animated UI feedback

---

## Status: Paused

Core loop is playable (alpha milestone reached). Save/load works, upgrades work, archers auto-fight. Paused while I focus on other projects, but I'll come back for polish -- sound design, achievements, and balancing.

---

## License

This project is currently unlicensed. All rights reserved.