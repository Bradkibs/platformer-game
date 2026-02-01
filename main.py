"""
Platformer Game: Dynamic Object Placement for All Levels.
FIXES:
1. Replaces static coordinates (x=800) with a loop that scans the whole map.
2. Ensures obstacles and items appear in Level 2, 3, etc.
"""
import arcade
import arcade.gui
import random

# --- Constants & Configuration ---
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Adventure of the Platformer"
TILE_SCALING = 0.5
COIN_SCALING = 0.5
PLAYER_MOVEMENT_SPEED = 5
GRAVITY = 1
PLAYER_JUMP_SPEED = 20
CAMERA_SPEED = 0.1

# --- Scores ---
SCORE_BRONZE = 10
SCORE_SILVER = 25
SCORE_GOLD = 50
SCORE_GEM = 100

# --- Retro Theme Colors ---
COLOR_BG_GAME = arcade.color.WHEAT
COLOR_BG_MENU = arcade.color.BISQUE
COLOR_TEXT_MAIN = arcade.color.SADDLE_BROWN
COLOR_BTN_NORMAL = arcade.color.BURLYWOOD
COLOR_BTN_HOVER = arcade.color.SANDY_BROWN
COLOR_BTN_PRESS = arcade.color.SIENNA
COLOR_BTN_TEXT = arcade.color.DARK_BROWN

# Load Retro Font
arcade.load_font(':resources:/fonts/ttf/Kenney/Kenney_Pixel.ttf')
RETRO_FONT = "Kenney Pixel"

# Define the Retro Button Style
RETRO_BUTTON_STYLE = {
    "normal": arcade.gui.UIFlatButton.UIStyle(
        font_size=24, font_name=RETRO_FONT, font_color=COLOR_BTN_TEXT,
        bg=COLOR_BTN_NORMAL, border=COLOR_BTN_PRESS, border_width=2,
    ),
    "hover": arcade.gui.UIFlatButton.UIStyle(
        font_size=24, font_name=RETRO_FONT, font_color=COLOR_BTN_TEXT,
        bg=COLOR_BTN_HOVER, border=COLOR_BTN_TEXT, border_width=2,
    ),
    "press": arcade.gui.UIFlatButton.UIStyle(
        font_size=24, font_name=RETRO_FONT, font_color=arcade.color.WHITE,
        bg=COLOR_BTN_PRESS, border=COLOR_BTN_PRESS, border_width=2,
    ),
}

class SubMenu(arcade.gui.UIMouseFilterMixin, arcade.gui.UIAnchorLayout):
    """Acts like a fake view/window."""
    def __init__(self, title):
        super().__init__(size_hint=(1, 1))
        frame = self.add(arcade.gui.UIAnchorLayout(width=300, height=400, size_hint=None))
        frame.with_padding(all=20)
        frame.with_background(
            texture=arcade.gui.NinePatchTexture(
                left=7, right=7, bottom=7, top=7,
                texture=arcade.load_texture(":resources:gui_basic_assets/window/grey_panel.png"),
            )
        )
        back_button = arcade.gui.UIFlatButton(text="Back", width=250, style=RETRO_BUTTON_STYLE)
        back_button.on_click = self.on_click_back_button
        title_label = arcade.gui.UILabel(text=title, align="center", font_size=30, font_name=RETRO_FONT, text_color=COLOR_TEXT_MAIN)
        widget_layout = arcade.gui.UIBoxLayout(align="left", space_between=10)
        widget_layout.add(title_label)
        widget_layout.add(back_button)
        frame.add(child=widget_layout, anchor_x="center_x", anchor_y="top")

    def on_click_back_button(self, event):
        self.parent.remove(self)


class MenuView(arcade.View):
    """View for menu screen"""
    def __init__(self, main_view):
        super().__init__()
        self.main_view = main_view
        self.manager = arcade.gui.UIManager()
        self.grid = arcade.gui.UIGridLayout(column_count=2, row_count=3, horizontal_spacing=20, vertical_spacing=20)

        resume_btn = arcade.gui.UIFlatButton(text="Resume", width=200, style=RETRO_BUTTON_STYLE)
        start_new_btn = arcade.gui.UIFlatButton(text="New Game", width=200, style=RETRO_BUTTON_STYLE)
        exit_btn = arcade.gui.UIFlatButton(text="Exit", width=420, style=RETRO_BUTTON_STYLE)

        self.grid.add(resume_btn, column=0, row=0)
        self.grid.add(start_new_btn, column=1, row=0)
        self.grid.add(exit_btn, column=0, row=2, column_span=2)
        self.anchor = self.manager.add(arcade.gui.UIAnchorLayout())
        self.anchor.add(anchor_x="center_x", anchor_y="center_y", child=self.grid)

        @resume_btn.event("on_click")
        def on_click_resume_button(event):
            self.window.show_view(self.main_view)

        @start_new_btn.event("on_click")
        def on_click_start_new_game_button(event):
            game_view = GameView()
            game_view.setup()
            self.window.show_view(game_view)

        @exit_btn.event("on_click")
        def on_click_exit_button(event):
            arcade.exit()

    def on_show_view(self):
        self.manager.enable()
        arcade.set_background_color(COLOR_BG_MENU)

    def on_hide_view(self):
        self.manager.disable()

    def on_draw(self):
        self.clear()
        self.manager.draw()


class GameView(arcade.View):
    """Main Game Logic View"""

    def __init__(self):
        super().__init__()
        self.manager = arcade.gui.UIManager()

        # UI Pause Button
        pause_btn = arcade.gui.UIFlatButton(text="Pause", width=120, style=RETRO_BUTTON_STYLE)
        @pause_btn.event("on_click")
        def on_click_pause(event):
            menu_view = MenuView(self)
            self.window.show_view(menu_view)

        self.anchor = self.manager.add(arcade.gui.UIAnchorLayout())
        self.anchor.add(anchor_x="right", anchor_y="top", align_x=-20, align_y=-20, child=pause_btn)

        # Game Variables
        self.player_sprite = None
        self.physics_engine = None
        self.scene = None
        self.tile_map = None
        self.camera = None
        self.gui_camera = None

        self.map_width = 0
        self.walk_textures_right = []
        self.walk_textures_left = []
        self.walk_index = 0
        self.facing_right = True

        self.score = 0
        self.level = 1
        self.reset_score = True

        # Checkpoint variables
        self.checkpoint_x = 128
        self.checkpoint_y = 128

        # Pre-load textures
        self.player_texture_idle = arcade.load_texture(":resources:/images/animated_characters/male_person/malePerson_idle.png")
        self.player_texture_jump_right = arcade.load_texture(":resources:images/animated_characters/male_person/malePerson_jump.png")
        self.player_texture_fall_right = arcade.load_texture(":resources:images/animated_characters/male_person/malePerson_fall.png")
        self.player_texture_jump_left = self.player_texture_jump_right.flip_left_right()
        self.player_texture_fall_left = self.player_texture_fall_right.flip_left_right()

        for i in range(8):
            tex = arcade.load_texture(f":resources:/images/animated_characters/male_person/malePerson_walk{i}.png")
            self.walk_textures_right.append(tex)
            self.walk_textures_left.append(tex.flip_left_right())

        # Sounds
        self.collect_coin_sound = arcade.load_sound(":resources:sounds/coin1.wav")
        self.collect_gem_sound = arcade.load_sound(":resources:sounds/coin2.wav")
        self.collect_key_sound = arcade.load_sound(":resources:sounds/secret2.wav")
        self.jump_sound = arcade.load_sound(":resources:sounds/jump1.wav")
        self.gameover_sound = arcade.load_sound(":resources:sounds/gameover1.wav")

    def get_ground_y(self, x_pos):
        """
        Calculates the Y height of the ground at a specific X coordinate.
        """
        ground_y = -100 # Default to below screen if nothing found

        if "Platforms" in self.scene:
            for tile in self.scene["Platforms"]:
                if tile.left < x_pos < tile.right:
                    if tile.top > ground_y:
                        ground_y = tile.top
        return ground_y

    def place_dynamic_objects(self):
        """
        Scans the entire level map and places objects (Crates, Coins, Gems)
        dynamically based on available ground, rather than fixed coordinates.
        """
        # Start scanning after the start area (300px) and stop before the end (200px)
        # We step every 300 pixels to spread things out.
        scan_step = 300

        for x_coord in range(400, int(self.map_width - 200), scan_step):

            # Add some randomness to the step so it doesn't look like a grid
            actual_x = x_coord + random.randint(-50, 50)

            # Find the ground height at this spot
            ground_y = self.get_ground_y(actual_x)

            # If we found a pit (ground is too low), skip this spot
            if ground_y < 0:
                continue

            # --- DECISION: WHAT TO PLACE HERE? ---
            roll = random.randint(1, 100)

            # 30% Chance: Crate Stack with Silver Coins
            if roll <= 30:
                previous_box = None
                # Create stack of 1 to 3 crates
                stack_height = random.randint(1, 3)

                for i in range(stack_height):
                    crate = arcade.Sprite(":resources:images/tiles/boxCrate_double.png", TILE_SCALING)
                    crate.center_x = actual_x
                    if i == 0:
                        crate.bottom = ground_y
                    else:
                        crate.bottom = previous_box.top
                    self.scene.add_sprite("Obstacles", crate)
                    previous_box = crate

                # Place silver coin on top
                coin = arcade.Sprite(":resources:/images/items/coinSilver.png", COIN_SCALING)
                coin.center_x = actual_x
                coin.bottom = previous_box.top + 10
                self.scene.add_sprite("Coins_Silver", coin)

            # 40% Chance: Cluster of Bronze Coins
            elif roll <= 70:
                # Place 3 coins in a row
                for i in range(3):
                    coin = arcade.Sprite(":resources:/images/items/coinBronze.png", COIN_SCALING)
                    coin.center_x = actual_x + (i * 40)
                    coin.bottom = ground_y + 10
                    self.scene.add_sprite("Coins_Bronze", coin)

            # 10% Chance: Rare Red Gem (Floating High)
            elif roll <= 80:
                gem = arcade.Sprite(":resources:/images/items/gemRed.png", COIN_SCALING)
                gem.center_x = actual_x
                gem.bottom = ground_y + 250 # High jump!
                self.scene.add_sprite("Gems", gem)

        # --- SPECIAL: Always Place Checkpoint Key ---
        # Place it roughly in the middle of the level
        mid_map = self.map_width / 2
        mid_ground = self.get_ground_y(mid_map)
        if mid_ground > 0:
            key = arcade.Sprite(":resources:/images/items/keyBlue.png", COIN_SCALING)
            key.center_x = mid_map
            key.bottom = mid_ground + 10
            self.scene.add_sprite("Keys", key)

    def setup(self):
        # -- MAP LOADING --
        layer_options = {
            "Platforms": {"use_spatial_hash": True},
        }

        # Try loading the map.
        map_name = f":resources:tiled_maps/level_{self.level}.json"

        try:
            self.tile_map = arcade.load_tilemap(map_name, TILE_SCALING, layer_options)
        except FileNotFoundError:
            print(f"Map {map_name} not found, resetting to level 1")
            self.level = 1
            map_name = f":resources:tiled_maps/map2_level_{self.level}.json"
            self.tile_map = arcade.load_tilemap(map_name, TILE_SCALING, layer_options)

        self.scene = arcade.Scene.from_tilemap(self.tile_map)

        self.map_width = (self.tile_map.width * self.tile_map.tile_width) * self.tile_map.scaling
        self.map_height = (self.tile_map.height * self.tile_map.tile_height) * self.tile_map.scaling

        # Create SpriteLists
        self.scene.add_sprite_list("Coins_Bronze")
        self.scene.add_sprite_list("Coins_Silver")
        self.scene.add_sprite_list("Gems")
        self.scene.add_sprite_list("Keys")
        self.scene.add_sprite_list("Obstacles")

        # --- RUN DYNAMIC PLACEMENT ---
        # This will fill the level with items regardless of map size
        self.place_dynamic_objects()

        # --- PLAYER SETUP ---
        if "Foreground" in self.scene:
            self.scene.add_sprite_list_after("Player", "Foreground")
        else:
            self.scene.add_sprite_list("Player")

        self.player_sprite = arcade.Sprite(self.player_texture_idle)
        self.player_sprite.center_x = self.checkpoint_x
        self.player_sprite.center_y = self.checkpoint_y
        self.scene.add_sprite("Player", self.player_sprite)

        # Create Physics Engine
        wall_layers = [self.scene["Obstacles"]]
        if "Platforms" in self.scene:
            wall_layers.append(self.scene["Platforms"])

        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite,
            walls=wall_layers,
            gravity_constant=GRAVITY
        )

        self.camera = arcade.Camera2D()
        self.gui_camera = arcade.Camera2D()
        self.camera.position = (self.player_sprite.center_x, self.player_sprite.center_y)

        if self.reset_score: self.score = 0
        self.reset_score = True

        self.score_text = arcade.Text(f"Score: {self.score}", x=10, y=10, font_size=30, font_name=RETRO_FONT, color=COLOR_TEXT_MAIN)

    def on_show_view(self):
        self.manager.enable()
        arcade.set_background_color(COLOR_BG_GAME)

    def on_hide_view(self):
        self.manager.disable()

    def on_draw(self):
        self.clear()
        self.camera.use()
        self.scene.draw()
        self.gui_camera.use()
        self.manager.draw()
        self.score_text.draw()

    def respawn_player(self):
        self.player_sprite.change_x = 0
        self.player_sprite.change_y = 0
        self.player_sprite.center_x = self.checkpoint_x
        self.player_sprite.center_y = self.checkpoint_y
        arcade.play_sound(self.gameover_sound)
        self.camera.position = (self.checkpoint_x, self.checkpoint_y)

    def on_update(self, delta_time):
        if self.physics_engine:
            self.physics_engine.update()

        if self.player_sprite.change_x > 0: self.facing_right = True
        elif self.player_sprite.change_x < 0: self.facing_right = False

        if not self.physics_engine.can_jump():
            if self.player_sprite.change_y > 0:
                self.player_sprite.texture = self.player_texture_jump_right if self.facing_right else self.player_texture_jump_left
            else:
                self.player_sprite.texture = self.player_texture_fall_right if self.facing_right else self.player_texture_fall_left
        elif abs(self.player_sprite.change_x) > 0:
            self.walk_index += 0.2
            if self.walk_index >= len(self.walk_textures_right): self.walk_index = 0
            self.player_sprite.texture = self.walk_textures_right[int(self.walk_index)] if self.facing_right else self.walk_textures_left[int(self.walk_index)]
        else:
            self.walk_index = 0
            self.player_sprite.texture = self.player_texture_idle

        # --- ROBUST COLLISION CHECKS ---
        if "Coins" in self.scene:
            gold_hit = arcade.check_for_collision_with_list(self.player_sprite, self.scene["Coins"])
            for coin in gold_hit:
                coin.remove_from_sprite_lists()
                arcade.play_sound(self.collect_coin_sound)
                self.score += SCORE_GOLD

        bronze_hit = arcade.check_for_collision_with_list(self.player_sprite, self.scene["Coins_Bronze"])
        for coin in bronze_hit:
            coin.remove_from_sprite_lists()
            arcade.play_sound(self.collect_coin_sound)
            self.score += SCORE_BRONZE

        silver_hit = arcade.check_for_collision_with_list(self.player_sprite, self.scene["Coins_Silver"])
        for coin in silver_hit:
            coin.remove_from_sprite_lists()
            arcade.play_sound(self.collect_coin_sound)
            self.score += SCORE_SILVER

        gem_hit = arcade.check_for_collision_with_list(self.player_sprite, self.scene["Gems"])
        for gem in gem_hit:
            gem.remove_from_sprite_lists()
            arcade.play_sound(self.collect_gem_sound)
            self.score += SCORE_GEM

        key_hit = arcade.check_for_collision_with_list(self.player_sprite, self.scene["Keys"])
        for key in key_hit:
            key.remove_from_sprite_lists()
            arcade.play_sound(self.collect_key_sound)
            self.checkpoint_x = key.center_x
            self.checkpoint_y = key.center_y

        self.score_text.text = f"Score: {self.score}"

        # Robust "Don't Touch" check
        if "Don't Touch" in self.scene:
            if arcade.check_for_collision_with_list(self.player_sprite, self.scene["Don't Touch"]):
                self.respawn_player()

        if self.player_sprite.top < 0:
            self.respawn_player()

        # Level End Logic
        if self.player_sprite.center_x >= self.map_width:
            self.level += 1
            self.reset_score = False
            self.checkpoint_x = 128
            self.checkpoint_y = 128
            self.setup()

        # Camera
        screen_center_x = self.window.width / 2
        screen_center_y = self.window.height / 2
        target_x = self.player_sprite.center_x
        target_y = self.player_sprite.center_y

        if target_x < screen_center_x: target_x = screen_center_x
        elif target_x > self.map_width - screen_center_x: target_x = self.map_width - screen_center_x
        if target_y < screen_center_y: target_y = screen_center_y
        elif target_y > self.map_height - screen_center_y: target_y = self.map_height - screen_center_y

        curr_x, curr_y = self.camera.position
        self.camera.position = (curr_x + (target_x - curr_x) * CAMERA_SPEED, curr_y + (target_y - curr_y) * CAMERA_SPEED)

    def on_key_press(self, key, modifiers):
        if key in [arcade.key.UP, arcade.key.W] and self.physics_engine.can_jump():
            self.player_sprite.change_y = PLAYER_JUMP_SPEED
            arcade.play_sound(self.jump_sound)
        elif key in [arcade.key.LEFT, arcade.key.A]:
            self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED
        elif key in [arcade.key.RIGHT, arcade.key.D]:
            self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED

    def on_key_release(self, key, modifiers):
        if key in [arcade.key.LEFT, arcade.key.A, arcade.key.RIGHT, arcade.key.D]:
            self.player_sprite.change_x = 0

def main():
    window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, resizable=True)
    start_view = GameView()
    start_view.setup()
    window.show_view(start_view)
    arcade.run()

if __name__ == "__main__":
    main()