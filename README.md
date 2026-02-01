# Adventure of the Platformer Game

**Author:** Bradley Kibwana

**Tech Stack:** Python, `arcade` library

A retro-styled 2D platformer game featuring physics-based movement, procedural object generation, and a multi-state game loop.

## 🎮 Key Features

### 1. Game State Management

The game utilizes `arcade.View` to manage three distinct states, creating a complete game flow:

* **MenuView:** A retro UI main menu to Start New Game, Resume, or Exit.
* **GameView:** The core gameplay loop handling physics, collisions, and rendering.
* **GameOverView:** Triggered when lives reach zero, allowing the player to Restart or Exit.

### 2. Procedural Level Population

While the terrain is based on tilemaps, the game features a **Dynamic Object Placement System** (`place_dynamic_objects`).

* Instead of static item placement, the game scans the map and randomly spawns Crates, Coins, Bombs, Gems, and Keys.
* **Difficulty Scaling:** As the `LEVEL` increases, the probability of Hazards (Bombs) increases, while the density of loot adjusts.

### 3. Checkpoint & Lives System

* **Lives:** The player starts with **3 Lives**.
* Lose a life by hitting a Bomb, falling off the map, or touching hazards.
* Gain a life by collecting a **Gem**.


* **Checkpoints:** Collecting a **Key** updates the player's spawn point (`checkpoint_x`, `checkpoint_y`). On death, the player respawns at the last collected key rather than the start of the level.

### 4. Physics & Animation

* **Platformer Physics:** Implements gravity, jumping, and wall collisions using `arcade.PhysicsEnginePlatformer`.
* **Sprite Animation:** The player character changes texture based on state:
* Idle
* Walking (cycling through frames)
* Jumping / Falling
* Directional flipping (Left/Right)



### 5. Camera Tracking

Includes a smooth 2D Camera that follows the player, keeping them centered within the bounds of the map width/height.

---

## 🕹️ Controls

| Key | Action |
| --- | --- |
| **W** or **UP Arrow** | Jump |
| **A** or **LEFT Arrow** | Move Left |
| **D** or **RIGHT Arrow** | Move Right |
| **Mouse Click** | Interact with UI Buttons |

---

## 💎 Scoring & Items

| Item | Type | Effect |
| --- | --- | --- |
| **Bronze Coin** | Score | +10 Points |
| **Silver Coin** | Score | +25 Points |
| **Gold Coin** | Score | +50 Points |
| **Gem (Red)** | Power-up | +100 Points & **+1 Extra Life** |
| **Key (Blue)** | Utility | Sets new **Respawn Checkpoint** |
| **Bomb** | Hazard | **Death** (Lose 1 Life) |

---

## 🛠️ Code Structure Overview

### Configuration

Global constants define screen dimensions (`1280x720`), gravity, speed, and retro color palettes used throughout the UI.

### Classes

* **`SubMenu`**: A reusable UI widget for pop-up menus.
* **`MenuView`**: Handles the UI manager for the start screen using a Grid Layout.
* **`GameOverView`**: Displays the "Game Over" screen and resets the game instance on restart.
* **`GameView`**: The "Engine" of the game.
* `setup()`: Initializes the map, physics, and dynamic objects.
* `on_update()`: Handles movement logic, collision detection, and level progression.
* `respawn_player()`: Manages life deduction and position resetting.



---

## 🚀 How to Run

1. **Prerequisites:** Ensure you have Python installed.
2. **Install Arcade:**
```bash
pip install arcade

```


3. **Run the Game:**
```bash
python main.py

```



*Note: This game uses Arcade's built-in resources (`:resources:`), so no external asset downloads are required.*