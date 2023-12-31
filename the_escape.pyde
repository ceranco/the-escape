"""
Assets taken from:
* https://chroma-dave.itch.io/pixelart-adventure-pack
* https://shikashipx.itch.io/shikashis-fantasy-icons-pack
"""

import random
import copy

WINDOW_WIDTH = 1800
WINDOW_HEIGHT = 1000

JUMP_KEY = " "
JUMP_KEY_NAME = "SPACE"

BLACK = color(0)
WHITE = color(255)
RED = color(255, 0, 0)
GREEN = color(0, 255, 0)
BLUE = color(0, 0, 255)
PURPLE = color(255, 0, 255)

GROUND_HEIGHT = 700
INITIAL_VELOCITY = 7
INITIAL_JUMP_VELOCITY = -10
FINAL_JUMP_VELOCITY = -22
JUMP_LEN = 150
GRAVITY = 1.01

SEGMENT_REGULAR = 0
SEGMENT_PIT = 1
SEGMENT_TYPES = [SEGMENT_REGULAR, SEGMENT_PIT]

OBSTACLE_GROUND = 0
OBSTACLE_AIR = 1
OBSTACLE_ALTERNATING = 2
OBSTACLE_TYPES = [None, OBSTACLE_GROUND, OBSTACLE_AIR, OBSTACLE_ALTERNATING]
OBSTACLE_PROBS = [20, 6, 3, 3]
OBSTACLE_CYCLE = 90
OBSTACLE_AIR_HEIGHT = 200

POWER_UP_LIFETIME = 300

FALL_THRESHHOLD = 45

player_spritesheet = None
bat_spritesheet = None
warrior_spritesheet = None
world_tiles = None
double_jump_icon = None
screen = None

def setup():
    size(WINDOW_WIDTH, WINDOW_HEIGHT)
    
    # Load assets
    global player_spritesheet, bat_spritesheet, warrior_spritesheet, world_tiles, double_jump_icon
    noSmooth() # For some reason this doesn't work outside of the setup function, so it's here as well.
    player_spritesheet = SpriteSheet("player_spritesheet.png", 32, 32, 6, 7)
    bat_spritesheet = SpriteSheet("bat_spritesheet.png", 32, 32, 3, 7)
    warrior_spritesheet = SpriteSheet("warrior_spritesheet.png", 48, 32, 6, 7, True)
    world_tiles = WorldTiles("world_tiles.png")
    double_jump_icon = loadImage("double_jump.png")

    # Set initial screen
    global screen
    screen = TitleScreen(player_spritesheet.clone(), warrior_spritesheet.clone(), bat_spritesheet.clone())
    
def draw():  
    background(WHITE)
    screen.update()
    
    screen.show()
    # warrior_spritesheet.update()
    # warrior_spritesheet.show(0, 0, 150, 100)
    
def keyPressed():
    screen.key_pressed()
    
def keyReleased():
    screen.key_released()    

class Screen(object):
    """Base class for all 'screens' in the game; exposes a update -> show cycle with key pressed / released event handling."""
    
    def update(self):
        pass
    
    def show(self):
        pass
        
    def key_pressed(self):
        pass
        
    def key_released(self):
        pass
            
        
class TitleScreen(Screen):
    """The initial game screen."""
    
    def __init__(self, player_spritesheet, warrior_spritesheet, bat_spritesheet):
        self.player_spritesheet = player_spritesheet
        self.warrior_spritesheet = warrior_spritesheet
        self.bat_spritesheet = bat_spritesheet
    
    def update(self):
        player_spritesheet.update()
        warrior_spritesheet.update()
        bat_spritesheet.update()
    
    def show(self):
        # Fill up the whole screen with the empty tile
        world_tiles.show_empty(0, 0, max(WINDOW_WIDTH, WINDOW_HEIGHT))
        
        player_spritesheet.show(250, 350, 250, 250)
        warrior_spritesheet.show(1250, 350, 400, 250)
        bat_spritesheet.show(750, 600, 250, 250)
        
        fill(WHITE)
        textAlign(CENTER, CENTER)
        textSize(120)

        text("The Escape",  WINDOW_WIDTH // 2, 200)

        textSize(72)
        text("Press " + JUMP_KEY_NAME + " to start!", WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50)
        
    def key_pressed(self):
        if key == JUMP_KEY:
            global screen
            screen = GameScreen()
        
class GameScreen(Screen):
    """The game itself."""
    def __init__(self):
        self.space_pressed = False
        self.landscape = Landscape(world_tiles)
        self.player = Player(self.landscape, player_spritesheet)
        self.counter = ScoreCounter()
        self.counter.start()
        
    def update(self):
        self.player.update()
        self.landscape.update()
        self.counter.update()
        
        if not self.player.alive:
            self._end_game()
    
    def show(self):
        self.landscape.show()
        self.counter.show()
        self.player.show()
            
    def key_pressed(self):
        if key == JUMP_KEY:
            self.player.jump_press()
            self.space_pressed = True
            
    def key_released(self):
        if key == JUMP_KEY:
            self.player.jump_release()
            self.space_pressed = False
            
    def _end_game(self):
        """End-of-run routine."""
        global screen

        self.counter.stop()
        ellapsed = "{:.1f}".format(self.counter.get_ellapsed() / 1000.0)
        score = self.counter.get_score()
        
        message = "Total run time: " + str(ellapsed) + "s\nScore: " + str(score)
        screen = EndScreen(message, self)


class EndScreen(Screen):
    """The end-of-run screen, which can draw itself ontop of another screen."""
    
    def __init__(self, message, prev_screen = None):
        """Creates a new end-of-run screen, which will (optionally) draw itself ontop of the given screen with the given message."""
        self.message = message
        self.prev_screen = prev_screen
        
    def show(self):
        if self.prev_screen is not None:
            self.prev_screen.show()

        fill(WHITE)
        textSize(100)
        textAlign(CENTER, CENTER)
        text(self.message, WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        
        textSize(72)
        text("Press " + JUMP_KEY_NAME + " to start!", WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 200)

        
    def key_pressed(self):
        if key == JUMP_KEY:
            global screen
            screen = GameScreen()
            
            
class Player(object):
    """The controllable player."""
    
    def __init__(self, landscape, spritesheet):
        self.size = PVector(50, 100)
        self.draw_size = PVector(100, 100)
        self.position = PVector(150, GROUND_HEIGHT - self.size.y)
        self.velocity = PVector()
        self.landscape = landscape
        self.on_land = True
        self.mid_jump = False
        self.jump_started = 0
        self.power_up = None
        self.alive = True
        self.spritesheet = spritesheet
    
    def update(self):
        self.spritesheet.update()
        self.position += self.velocity
        self.velocity.y += GRAVITY
        
        if self.mid_jump:
            delta = millis() - self.jump_started
        
            self.velocity.y = self._get_jump_velocity(delta)
            self.mid_jump &= delta <= JUMP_LEN
        
        # Check if on land
        is_land_segment = self.landscape.segment_type_at(self.position.x + self.size.x // 2) == SEGMENT_REGULAR 
        self.on_land = is_land_segment and 0 <= self.position.y + self.size.y - self.landscape.height <= FALL_THRESHHOLD
        
        if self.on_land:
            self.position.y = self.landscape.height - self.size.y
            self.velocity.y = 0
            
        # Check collisions - either with land or obstacles.
        if is_land_segment and not self.on_land and self.landscape.height <= self.position.y + self.size.y:
            # print("BOOM")
            # self.position.y = self.landscape.height - self.size.y
            # self.on_land = True
            self.alive = False
            if self.power_up is not None:
                self.power_up.on_ground_collision(self)
            
        if self.landscape.check_obstacle_collision(self.position, self.size):
             # print("OBSTACLE " + str(millis()))
            self.alive = False
            if self.power_up is not None:
                self.power_up.on_obstacle_collision(self)
          
        power_up = self.landscape.check_power_up_collision(self.position, self.size) 
        if power_up is not None:
            self.power_up = power_up
             
        if self.power_up is not None:
            self.power_up.update()
            
            if self.power_up.lifetime == 0:
                self.power_up = None

        
    def show(self):
        self.spritesheet.show(self.position.x - 45, self.position.y, self.draw_size.x, self.draw_size.y)
        
        if self.power_up is not None:
            self.power_up.show(50, 100)
            
    def jump_press(self):
        """
        Start jumping.
        
        The vertical velocity will increase up to a set maximum as long as `jump_release` is not called.
        In this way, the height of the jump may be controlled to allow for more granular control of the player.
        """
        if self.power_up is not None:
            self.power_up.on_jump(self)
        
        if self.on_land:
            self.mid_jump = True
            self.jump_started = millis()
            self.velocity.y = INITIAL_JUMP_VELOCITY
            self.on_land = False
            
    def jump_release(self):
        """Stop jumping."""
        if self.mid_jump:
            delta = millis() - self.jump_started
            self.velocity.y = self._get_jump_velocity(delta)
            
        self.mid_jump = False
                
    def _get_jump_velocity(self, delta):
        """Calculates the jump velocity matching a jump key press of delta milliseconds."""
        ratio = min(1.0, float(delta) / JUMP_LEN)
        return map(ratio * FINAL_JUMP_VELOCITY, 0, FINAL_JUMP_VELOCITY, INITIAL_JUMP_VELOCITY, FINAL_JUMP_VELOCITY)
        
        
        
class Landscape(object):
    """
    The environment, which consistes of the landscape that the player runs on and the obstacles.
    
    The logical representation of the landscape will be an array that always has at least 11 elements, where each 
    element's width is exactly 1/10 of the window size.
    As the landscape scrolls by, old segments will be discarded and new segment generated dynamically.
    An obstacle array of exactly 11 is also generated, with at most one obstacle per segment.
    
    At any given point, at most (parts of) 11 segments will be seen.
    """
    
    def __init__(self, world_tiles):
        self.height = GROUND_HEIGHT
        self.width = WINDOW_WIDTH
        self.position = 5
        self.velocity = INITIAL_VELOCITY
        self.num_segments = 10
        self.segments = [SEGMENT_REGULAR for _ in range(self.num_segments + 1)]
        self.obstacles = [None for _ in self.segments]
        self.power_ups = [None for _ in self.segments]
        self.gap = self.width // self.num_segments
        self.power_up_size = 75
        self.power_up_offset = 50
        self.world_tiles = world_tiles
                
    def update(self):
        self.position += self.velocity
        self.velocity += 0.001
        
        if self.position >= self.gap:
            # Generate a new segment and an optional obstacles.
            self.position -= self.gap
            del self.segments[0]
            del self.obstacles[0]
            del self.power_ups[0]
            
            # Only generate new terrain if needed.
            if len(self.segments) == self.num_segments:
                new_segments, new_obstacles, new_power_ups = self.random_configuration()
                
                self.segments += new_segments
                self.obstacles += new_obstacles
                self.power_ups += new_power_ups
            
        for obstacle, power_up in zip(self.obstacles, self.power_ups):
            if obstacle is not None:
                obstacle.update()
            
            # if power_up is not None:
                # power_up.update()
        
    def show(self):
        # Fill up the whole screen with the empty tile
        self.world_tiles.show_empty(0, 0, max(WINDOW_WIDTH, WINDOW_HEIGHT))
        
        x = -self.position
        for segment, obstacle, power_up in zip(self.segments, self.obstacles, self.power_ups):
            if segment == SEGMENT_REGULAR:
                self.world_tiles.fill_brick(x, self.height, self.gap, WINDOW_HEIGHT - self.height, self.gap)
                # rect(x, self.height, self.gap, WINDOW_HEIGHT - self.height)
                
            elif segment == SEGMENT_PIT:
                pass
                
            if obstacle is not None:
                obstacle.show(x + self.gap // 2 - obstacle.size.x // 2)
                
            if power_up is not None:
                power_up.show(x + self.gap // 2 , self.height - self.power_up_offset, self.power_up_size)
                
            x += self.gap
            
    def segment_type_at(self, x):
        """Get the segment type in the given x coordinate."""
        idx = int(x + self.position) // self.gap 

        return self.segments[idx]
    
    def check_obstacle_collision(self, position, size):
        """Checks if the given rect intersects any of the obstacles."""
        # I gave up on making this clever and just check all obstacles.
        seg_x = -self.position
        for obstacle in self.obstacles:
            if obstacle is not None:
                obs_position = PVector(seg_x + self.gap // 2 - obstacle.size.x // 2,
                                       obstacle.y)      
                obs_size = obstacle.size
                
                if (position.x < obs_position.x + obs_size.x and position.x + size.x > obs_position.x and
                    position.y + size.y > obs_position.y and position.y < obs_position.y + obs_size.y):
                    return True
                
            seg_x += self.gap
            
        return False
    
    def check_power_up_collision(self, position, size):
        seg_x = -self.position
        for idx, power_up in enumerate(self.power_ups):
            if power_up is not None:
                power_up_position = PVector(seg_x + self.gap // 2, self.height - self.power_up_offset)
                
                closest = PVector(constrain(power_up_position.x, position.x, position.x + size.x),
                                  constrain(power_up_position.y, position.y, position.y + size.y))
                
                distance = PVector(power_up_position.x - closest.x, power_up_position.y - closest.y)
                distance_squared = PVector.dot(distance, distance)
                
                radius = self.power_up_size / 2
                if distance_squared <= radius * radius:
                    self.power_ups[idx] = None
                    return power_up
            
            seg_x += self.gap

    
    def random_configuration(self):
        """
        Generate a random environment configuration, which is a sequence of 0, 1 or 2 pits enclosed in regular landscape (only 1 segment for 0 pits).
        For each configuration there is at most 1 obstacle or powerup on the regular segments.
        """
        num_pits = random_choice([0, 1, 2], [14, 5, 3])
        segments = [SEGMENT_REGULAR] + [SEGMENT_PIT] * num_pits + ([SEGMENT_REGULAR] if num_pits > 0 else [])
        
        obstacle_idx = random.randint(-1, 0)
        obstacle_type = random_choice(OBSTACLE_TYPES, OBSTACLE_PROBS) if num_pits < 2 else None
        obstacles = [None] * len(segments)
        obstacles[obstacle_idx] = Obstacle(obstacle_type) if obstacle_type is not None else None 
        
        power_ups = [None] * len(segments)
        possible_idxs = [None]
        for idx in range(len(power_ups)):
            if segments[idx] == SEGMENT_REGULAR and obstacles[idx] is None:
                possible_idxs.append(idx)
        
        power_up_idx = random_choice(possible_idxs, [len(possible_idxs) * 2 + 5] + [1] * (len(possible_idxs) - 1))
        if power_up_idx is not None:
            power_ups[power_up_idx] = PowerUp.random()
            
                    
        return segments, obstacles, power_ups
        
    
class Obstacle(object):
    def __init__(self, type):
        self.type = type
        self.size = PVector(100, 100)
        self.display_size = self.size
        self.t = 0.0
        
        if self.type == OBSTACLE_GROUND or self.type == OBSTACLE_ALTERNATING:
            self.y = GROUND_HEIGHT - self.size.y
            
        elif self.type == OBSTACLE_AIR:
            self.y = OBSTACLE_AIR_HEIGHT
            
        # Select asset
        if self.type == OBSTACLE_AIR or self.type == OBSTACLE_ALTERNATING:
            self.asset = bat_spritesheet.clone()
            self.display_size = PVector(140, 140)
            
        else:
            obs = world_tiles.get_obstacle()
            self.asset, self.display_size = random.choice([(obs, self.display_size), (warrior_spritesheet.clone(), PVector(200, 100))])

    def update(self):
        if self.type == OBSTACLE_ALTERNATING:
            self.t += 1.0 / 60.0
            self.y = map(ease_in_out_blend(self.t), 0.0, 1.0, GROUND_HEIGHT - self.size.y, OBSTACLE_AIR_HEIGHT)

        self.asset.update()    
        
    def show(self, x):
        self.asset.show(x - (self.display_size.x - self.size.x) // 2, 
                        self.y - (self.display_size.y - self.size.y) // 2, 
                        self.display_size.x, 
                        self.display_size.y)
    
class PowerUp(object):
    """Base powerup class, exposes behavior hooks for player events."""
    
    def __init__(self, icon):
        self.lifetime = POWER_UP_LIFETIME
        # self.color = color(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        self.icon = icon 
    
    def on_jump(self, player):
        pass
        
    def on_obstacle_collision(self, player):
        pass
        
    def on_ground_collision(self, player):
        pass
        
    def update(self):
        self.lifetime -= 1

    def show(self, x, y, size = 50):
        if self.lifetime > 0:
            pushStyle()
            
            # fill(self.color, int(255 * self.lifetime / POWER_UP_LIFETIME))
            # noStroke()
            # circle(x, y, size)
            
            tint(255, int(255 * self.lifetime / POWER_UP_LIFETIME))
            image(self.icon, x - size // 2, y - size // 2, size, size)


            popStyle()
            
    @staticmethod
    def random():
        """Generate a random powerup."""
        return DoubleJump()
                
class DoubleJump(PowerUp):
    def __init__(self):
        super(DoubleJump, self).__init__(double_jump_icon)
        self.used = False
        
    def on_jump(self, player):
        if player.on_land:
            self.used = False
            
        elif not self.used:
            player.on_land = True
            self.used = True


class ScoreCounter(object):
    """Keeps track of the score for a run."""
    
    def _init(self):
        self.started = millis()
        self.stopped = self.started
        self.running = False
    
    def __init__(self):
        self._init()
        
    def start(self):
        """Start the counter - future calls to `update()` will affect it."""
        self._init()
        self.running = True
        
    def stop(self):
        """Stop the counter - future calls to `update()` will not affect it."""
        self.stopped = millis()
        self.running = False    
        
    def get_ellapsed(self):
        """Gets the time the counter was / is running."""
        if self.running:
            return millis() - self.started
        
        return self.stopped - self.started
        
    def get_score(self):
        """Gets the current score."""
        return self.get_ellapsed() // 500
    
    def update(self):
        pass
        
    def show(self):
        pushStyle()
        
        textAlign(LEFT)
        textSize(45)
        fill(WHITE)
        message = "Score: " + str(self.get_score())
        text(message, 25, 50)
        
        popStyle()
    
class SpriteSheet(object):
    def __init__(self, path, size_x, size_y, count, change_time, flip_x = False):
        noSmooth()
        self.sheet = loadImage(path)
        self.sprites = []
        for i in range(count):
             self.sprites.append(self.sheet.get(size_x * i, 0, size_x, size_y))
        self.current = 0
        self.counter = 0
        self.change_time = change_time
        self.flip_x = flip_x
    
    def clone(self):
        return copy.copy(self)
    
    def update(self):
        self.counter += 1
        if self.counter >= self.change_time:
            self.counter = 0
            self.current = (self.current + 1) % len(self.sprites)
        
    def show(self, x, y, width, height):
        noSmooth()
        pushMatrix()
        if self.flip_x:
            translate(x + width, y)
            scale(-1, 1)
        else:
            translate(x, y)
            
        image(self.sprites[self.current], 0, 0, width, height)
        popMatrix()
     
class Image(object):
    """Wraps a PImage with the update / show  pattern."""
    def __init__(self, img):
        self.img = img
        
    def update(self):
        pass
        
    def show(self, x, y, width, height):
        image(self.img, x, y, width, height)
       
class WorldTiles(object):
    def __init__(self, path):
        noSmooth()
        self.tile_size = 160
        self.tile_sheet_size = (1280, 1600)
        self.tile_sheet = loadImage(path)
        self.tiles = []
        
        for row_idx in range(self.tile_sheet_size[1] // self.tile_size):
            row = []
            for col_idx in range(self.tile_sheet_size[0] // self.tile_size):
                row.append(self.tile_sheet.get(self.tile_size * col_idx, self.tile_size * row_idx, self.tile_size, self.tile_size))
            self.tiles.append(row)
        
    def show_empty(self, x, y, size = 160):
        world_tiles._show(5, 1, x, y, size)
        
    def fill_empty(self, x, y, width, height, size = 160):
        self._fill(5, 1, x, y, size, width, height)
        
    def show_brick(self, x, y, size = 160):
        world_tiles._show(1, 1, x, y, size)
        
    def fill_brick(self, x, y, width, height, size = 160):
        self._fill(1, 1, x, y, size, width, height)
        
    def show_obstacle(self, x, y, size = 160):
        self._show(5, 3, x, y, size)
        
    def _show(self, row, col, x, y, size):
        image(self.tiles[row][col], x, y, size, size)
        
    def _fill(self, row, col, x, y, size, width, height):
        for j in range(ceil(float(width) / size)):
            for i in range(ceil(float(height) / size)):
                self._show(row, col, x + j * size, y + i * size, size) 
         
    def get_obstacle(self):
        return self._get_image(3, 5)
                   
    def _get_image(self, row, col):
        return Image(self.tiles[row][col])
        
    
def random_choice(ls, probs):
    """Returns a random element from the list with the probability distribution given by probs."""
    assert(len(ls) == len(probs))
    
    total = sum(probs)
    probs = [float(p) / total for p in probs]
    
    rnd = random.uniform(0, 1)
    
    threshold = 0
    for idx, p in enumerate(probs):
        if threshold <= rnd <= threshold + p:
            return ls[idx]
        threshold += p
        
    return ls[-1]

def ease_in_out_blend(t):
    """
    A Bezier blend curve, which may be used to animate movement with ease-in-out behavior in a repeating pattern.
    """
    t = abs(((t - 1) % 2) - 1)
    return t * t * (3.0 - 2.0 * t) 
