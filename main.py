"""
Platformer Game with Views, animation and camera clamping.
"""
import arcade
import arcade.gui
from typing import List

# Constants
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Adventure of the Platformer"
TILE_SCALING = 0.5
PLAYER_MOVEMENT_SPEED = 5
GRAVITY = 1
PLAYER_JUMP_SPEED = 20


class SubMenu(arcade.gui.UIMouseFilterMixin, arcade.gui.UIAnchorLayout):
    """Acts like a fake view/window."""

    def __init__(self, title, input_text, toggle_label, dropdown_options, slider_label):
        super().__init__(size_hint=(1, 1))

        frame = self.add(arcade.gui.UIAnchorLayout(width=300, height=400, size_hint=None))
        frame.with_padding(all=20)
        frame.with_background(
            texture=arcade.gui.NinePatchTexture(
                left=7, right=7, bottom=7, top=7,
                texture=arcade.load_texture(":resources:gui_basic_assets/window/dark_blue_gray_panel.png"),
            )
        )

        back_button = arcade.gui.UIFlatButton(text="Back", width=250)
        back_button.on_click = self.on_click_back_button

        title_label = arcade.gui.UILabel(text=title, align="center", font_size=20)
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

        resume_btn = arcade.gui.UIFlatButton(text="Resume", width=150)
        start_new_game_btn = arcade.gui.UIFlatButton(text="Start New Game", width=150)
        exit_btn = arcade.gui.UIFlatButton(text="Exit", width=320)

        self.grid.add(resume_btn, column=0, row=0)
        self.grid.add(start_new_game_btn, column=1, row=0)
        self.grid.add(exit_btn, column=0, row=2, column_span=2)

        self.anchor = self.manager.add(arcade.gui.UIAnchorLayout())
        self.anchor.add(anchor_x="center_x", anchor_y="center_y", child=self.grid)

        @resume_btn.event("on_click")
        def on_click_resume_button(event):
            self.window.show_view(self.main_view)

        @start_new_game_btn.event("on_click")
        def on_click_start_new_game_button(event):
            game_view = GameView()
            game_view.setup()
            self.window.show_view(game_view)

        @exit_btn.event("on_click")
        def on_click_exit_button(event):
            arcade.exit()

    def on_show_view(self):
        self.manager.enable()
        arcade.set_background_color(arcade.color.DARK_BLUE_GRAY)

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
        pause_btn = arcade.gui.UIFlatButton(text="Pause Game", width=150)

        @pause_btn.event("on_click")
        def on_click_pause(event):
            menu_view = MenuView(self)
            self.window.show_view(menu_view)

        self.anchor = self.manager.add(arcade.gui.UIAnchorLayout())
        self.anchor.add(anchor_x="right", anchor_y="top", align_x=-10, align_y=-10, child=pause_btn)

        # Game Variables
        self.player_sprite = None
        self.physics_engine = None
        self.scene = None
        self.tile_map = None
        self.camera = None
        self.gui_camera = None

        # Map Dimensions for Camera Clipping
        self.map_width = 0
        self.map_height = 0

        # Animation
        self.walk_textures_right = []
        self.walk_textures_left = []
        self.walk_index = 0
        self.facing_right = True

        self.score = 0
        self.level = 1
        self.reset_score = True

        # Pre-load static textures
        self.player_texture_idle = arcade.load_texture(
            ":resources:/images/animated_characters/male_person/malePerson_idle.png")
        self.player_texture_jump_right = arcade.load_texture(
            ":resources:images/animated_characters/male_person/malePerson_jump.png")
        self.player_texture_fall_right = arcade.load_texture(
            ":resources:images/animated_characters/male_person/malePerson_fall.png")
        self.player_texture_jump_left = self.player_texture_jump_right.flip_left_right()
        self.player_texture_fall_left = self.player_texture_fall_right.flip_left_right()

        # Load walk sequence efficiently
        for i in range(8):
            tex = arcade.load_texture(f":resources:/images/animated_characters/male_person/malePerson_walk{i}.png")
            self.walk_textures_right.append(tex)
            self.walk_textures_left.append(tex.flip_left_right())

        self.collect_coin_sound = arcade.load_sound(":resources:sounds/coin1.wav")
        self.jump_sound = arcade.load_sound(":resources:sounds/jump1.wav")
        self.gameover_sound = arcade.load_sound(":resources:sounds/gameover1.wav")

    def setup(self):
        layer_options = {"Platforms": {"use_spatial_hash": True}}
        self.tile_map = arcade.load_tilemap(f":resources:tiled_maps/map2_level_{self.level}.json", TILE_SCALING,
                                            layer_options)
        self.scene = arcade.Scene.from_tilemap(self.tile_map)

        # 1. Calculate Map Boundaries (in pixels)
        self.map_width = (self.tile_map.width * self.tile_map.tile_width) * self.tile_map.scaling
        self.map_height = (self.tile_map.height * self.tile_map.tile_height) * self.tile_map.scaling

        self.scene.add_sprite_list_after("Player", "Foreground")
        self.player_sprite = arcade.Sprite(self.player_texture_idle)
        self.player_sprite.center_x, self.player_sprite.center_y = 128, 128
        self.scene.add_sprite("Player", self.player_sprite)

        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, walls=self.scene["Platforms"], gravity_constant=GRAVITY
        )

        # Initialize cameras without invalid attributes
        self.camera = arcade.Camera2D()
        self.gui_camera = arcade.Camera2D()

        if self.reset_score: self.score = 0
        self.reset_score = True
        self.score_text = arcade.Text(f"Score: {self.score}", x=10, y=10, font_size=18)

    def on_show_view(self):
        self.manager.enable()
        arcade.set_background_color(arcade.csscolor.CORNFLOWER_BLUE)

    def on_hide_view(self):
        self.manager.disable()

    def on_draw(self):
        self.clear()
        self.camera.use()
        self.scene.draw()
        self.gui_camera.use()
        self.manager.draw()
        self.score_text.draw()

    def on_update(self, delta_time):
        if self.physics_engine:
            self.physics_engine.update()

        # Handle Animation
        if self.player_sprite.change_x > 0:
            self.facing_right = True
        elif self.player_sprite.change_x < 0:
            self.facing_right = False

        if not self.physics_engine.can_jump():
            if self.player_sprite.change_y > 0:
                self.player_sprite.texture = self.player_texture_jump_right if self.facing_right else self.player_texture_jump_left
            else:
                self.player_sprite.texture = self.player_texture_fall_right if self.facing_right else self.player_texture_fall_left
        elif abs(self.player_sprite.change_x) > 0:
            self.walk_index += 0.2
            if self.walk_index >= len(self.walk_textures_right): self.walk_index = 0
            self.player_sprite.texture = self.walk_textures_right[int(self.walk_index)] if self.facing_right else \
            self.walk_textures_left[int(self.walk_index)]
        else:
            self.walk_index = 0
            self.player_sprite.texture = self.player_texture_idle

        # Collisions
        coins = arcade.check_for_collision_with_list(self.player_sprite, self.scene["Coins"])
        for coin in coins:
            coin.remove_from_sprite_lists()
            arcade.play_sound(self.collect_coin_sound)
            self.score += 75
            self.score_text.text = f"Score: {self.score}"

        if arcade.check_for_collision_with_list(self.player_sprite, self.scene["Don't Touch"]):
            arcade.play_sound(self.gameover_sound)
            self.setup()

        if self.player_sprite.center_x >= self.map_width:
            self.level += 1
            self.reset_score = False
            self.setup()

        # --- CAMERA CLIPPING LOGIC ---
        # 1. Get the screen dimensions relative to the current camera zoom
        screen_center_x = self.window.width / 2
        screen_center_y = self.window.height / 2

        # 2. Determine where the camera WANTS to be (the player)
        target_x = self.player_sprite.center_x
        target_y = self.player_sprite.center_y

        # 3. Clamp X: Ensure camera doesn't show past the Left (0) or Right (map_width) edges
        # We clamp the CENTER point. The center must be at least 'half a screen' away from the edge.
        if target_x < screen_center_x:
            target_x = screen_center_x
        elif target_x > self.map_width - screen_center_x:
            target_x = self.map_width - screen_center_x

        # 4. Clamp Y: Same for Top and Bottom
        if target_y < screen_center_y:
            target_y = screen_center_y
        elif target_y > self.map_height - screen_center_y:
            target_y = self.map_height - screen_center_y

        # 5. Set the camera position to the clamped coordinates
        self.camera.position = (target_x, target_y)

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