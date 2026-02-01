"""
Platformer Game

python -m arcade.examples.platform_tutorial.14_multiple_levels
"""
import arcade

# Constants
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Platformer"

# Constants used to scale our sprites from their original size
TILE_SCALING = 0.5
COIN_SCALING = 0.5

# Movement speed of player, in pixels per frame
PLAYER_MOVEMENT_SPEED = 5
GRAVITY = 1
PLAYER_JUMP_SPEED = 20


class GameView(arcade.Window):
    """
    Main application class.
    """

    def __init__(self):

        # Call the parent class and set up the window
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)

        # Variable to hold our texture for our player
        self.player_texture_walk_right = None
        self.player_texture_walk_left = None
        self.player_texture_jump_right= None
        self.player_texture_jump_left = None
        self.player_texture_fall_right = None
        self.player_texture_fall_left = None
        self.player_texture_idle = None

        #walking animation sequence
        self.walk_textures_right = []
        self.walk_textures_left = []
        self.walk_index = 0

        # Separate variable that holds the player sprite
        self.player_sprite = None

        # Variable to hold our Tiled Map
        self.tile_map = None

        # Replacing all of our SpriteLists with a Scene variable
        self.scene = None

        # A variable to store our camera object
        self.camera = None

        # A variable to store our gui camera object
        self.gui_camera = None

        # This variable will store our score as an integer.
        self.score = 0

        # This variable will store the text for score that we will draw to the screen.
        self.score_text = None

        # Where is the right edge of the map?
        self.end_of_map = 0

        # Level number to load
        self.level = 1

        # Should we reset the score?
        self.reset_score = True

        # facing direction (default is idle)
        self.facing_right = True

        # Load sounds
        self.collect_coin_sound = arcade.load_sound(":resources:sounds/coin1.wav")
        self.jump_sound = arcade.load_sound(":resources:sounds/jump1.wav")
        self.gameover_sound = arcade.load_sound(":resources:sounds/gameover1.wav")

    def setup(self):
        """Set up the game here. Call this function to restart the game."""
        layer_options = {
            "Platforms": {
                "use_spatial_hash": True
            }
        }

        # Load our TileMap
        self.tile_map = arcade.load_tilemap(
            f":resources:tiled_maps/map2_level_{self.level}.json",
            scaling=TILE_SCALING,
            layer_options=layer_options,
        )

        # Create our Scene Based on the TileMap
        self.scene = arcade.Scene.from_tilemap(self.tile_map)
        # right movement sprites
        for i in range(8):
            self.player_texture_walk_right = arcade.load_texture(
            f":resources:/images/animated_characters/male_person/malePerson_walk{i}.png")
            self.walk_textures_right.append(self.player_texture_walk_right)
            self.walk_textures_left.append(self.player_texture_walk_right.flip_left_right())
        self.player_texture_jump_right = arcade.load_texture(
            ":resources:images/animated_characters/male_person/malePerson_jump.png")
        self.player_texture_fall_right = arcade.load_texture(
            ":resources:images/animated_characters/male_person/malePerson_fall.png")

        # idle sprite remains the same
        self.player_texture_idle = arcade.load_texture(":resources:/images/animated_characters/male_person/malePerson_idle.png")



        # Left movement sprites

        self.player_texture_walk_left = self.player_texture_walk_right.flip_left_right()
        self.player_texture_jump_left = self.player_texture_jump_right.flip_left_right()
        self.player_texture_fall_left = self.player_texture_fall_right.flip_left_right()



        # Add Player Spritelist before "Foreground" layer. This will make the foreground
        # be drawn after the player, making it appear to be in front of the Player.
        # Setting before using scene.add_sprite allows us to define where the SpriteList
        # will be in the draw order. If we just use add_sprite, it will be appended to the
        # end of the order.
        self.scene.add_sprite_list_after("Player", "Foreground")

        self.player_sprite = arcade.Sprite(self.player_texture_idle)
        self.player_sprite.center_x = 128
        self.player_sprite.center_y = 128
        self.scene.add_sprite("Player", self.player_sprite)

        # Create a Platformer Physics Engine, this will handle moving our
        # player as well as collisions between the player sprite and
        # whatever SpriteList we specify for the walls.
        # It is important to supply static to the walls parameter. There is a
        # platforms parameter that is intended for moving platforms.
        # If a platform is supposed to move, and is added to the walls list,
        # it will not be moved.
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, walls=self.scene["Platforms"], gravity_constant=GRAVITY
        )

        # Initialize our camera, setting a viewport the size of our window.
        self.camera = arcade.Camera2D()

        # Initialize our gui camera, initial settings are the same as our world camera.
        self.gui_camera = arcade.Camera2D()

        # Reset the score if we should
        if self.reset_score:
            self.score = 0
        self.reset_score = True

        # Initialize our arcade.Text object for score
        self.score_text = arcade.Text(f"Score: {self.score}", x=0, y=5)

        self.background_color = arcade.csscolor.CORNFLOWER_BLUE

        # Calculate the right edge of the map in pixels
        self.end_of_map = (self.tile_map.width * self.tile_map.tile_width)
        self.end_of_map *= self.tile_map.scaling
        self.facing_right = True
        print(self.end_of_map)

    def on_draw(self):
        """Render the screen."""

        # Clear the screen to the background color
        self.clear()

        # Activate our camera before drawing
        self.camera.use()

        # Draw our Scene
        self.scene.draw()

        # Activate our GUI camera
        self.gui_camera.use()

        # Draw our Score
        self.score_text.draw()

    def on_update(self, delta_time):
        """Movement and Game Logic"""

        #1. Move the player using our physics engine
        self.physics_engine.update()

        # 2. Determine Facing Direction based on velocity
        # If moving right, set facing_right = True
        if self.player_sprite.change_x > 0:
            self.facing_right = True
        # If moving left, set facing_right = False
        elif self.player_sprite.change_x < 0:
            self.facing_right = False

        # 3. Select Texture based on state

        # CASE A: Jumping or Falling (Airborne)
        if not self.physics_engine.can_jump():
            if self.player_sprite.change_y > 0:

                # RISING (Jumping)
                if self.facing_right:
                    self.player_sprite.texture = self.player_texture_jump_right
                else:
                    self.player_sprite.texture = self.player_texture_jump_left
            else:
                # FALLING
                if self.facing_right:
                    self.player_sprite.texture = self.player_texture_fall_right
                else:
                    self.player_sprite.texture = self.player_texture_fall_left

        # CASE B: Walking (Grounded and moving)
        elif abs(self.player_sprite.change_x) > 0:
            # 1. Update the animation frame
            # We use a smaller increment (like 0.2) to slow down the animation speed
            self.walk_index += 0.2
            if self.walk_index >= len(self.walk_textures_right):
                self.walk_index = 0

            # 2. Assign the texture
            if self.facing_right:
                self.player_sprite.texture = self.walk_textures_right[int(self.walk_index)]
            else:
                self.player_sprite.texture = self.walk_textures_left[int(self.walk_index)]

        # CASE C: Idle (Grounded and still)
        else:
            self.walk_index = 0
            # If you want directional idle:
            if self.facing_right:
                self.player_sprite.texture = self.player_texture_idle
            else:
                self.player_sprite.texture = self.player_texture_idle
        # See if we hit any coins
        coin_hit_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.scene["Coins"]
        )

        # Loop through each coin we hit (if any) and remove it
        for coin in coin_hit_list:
            # Remove the coin
            coin.remove_from_sprite_lists()
            arcade.play_sound(self.collect_coin_sound)
            self.score += 75
            self.score_text.text = f"Score: {self.score}"

        if arcade.check_for_collision_with_list(
            self.player_sprite, self.scene["Don't Touch"]
        ):
            arcade.play_sound(self.gameover_sound)
            self.setup()

        # Check if the player got to the end of the level
        if self.player_sprite.center_x >= self.end_of_map:
            # Advance to the next level
            self.level += 1

            # Turn off score reset when advancing level
            self.reset_score = False

            # Reload game with new level
            self.setup()

        # Center our camera on the player
        self.camera.position = self.player_sprite.position

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed."""

        if key == arcade.key.ESCAPE:
            self.setup()

        if key == arcade.key.UP or key == arcade.key.W:
            if self.physics_engine.can_jump():
                self.player_sprite.change_y = PLAYER_JUMP_SPEED
                arcade.play_sound(self.jump_sound)

        if key == arcade.key.LEFT or key == arcade.key.A:
            self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED

    def on_key_release(self, key, modifiers):
        """Called whenever a key is released."""

        if key == arcade.key.LEFT or key == arcade.key.A:
            self.player_sprite.change_x = 0
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player_sprite.change_x = 0


def main():
    """Main function"""
    window = GameView()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()