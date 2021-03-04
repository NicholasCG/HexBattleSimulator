# This is needed becuase pygame's init() calls for an audio driver,
# which seemed to default to ALSA, which was causing an underrun error.
import os

os.environ['SDL_AUDIODRIVER'] = 'dsp'

import yaml
import numpy as np
import hexy as hx
import pygame as pg

COL_IDX = np.random.randint(0, 4, (7 ** 3))
COLORS = np.array([
    [244, 98, 105],   # red
    [251, 149, 80],   # orange
    [141, 207, 104],  # green
    [53, 111, 163],   # water blue
    [85, 163, 193],   # sky blue
])


class Selection:
    class Type:
        RECT = 0
        HEX = 1
        TRIANGLE = 2
        RHOMBUS = 3
        CUSTOM = 4

        @staticmethod
        def to_string(selection_type):
            if selection_type == Selection.Type.RECT:
                return "rectangle"
            elif selection_type == Selection.Type.HEX:
                return "hexagon"
            elif selection_type == Selection.Type.TRIANGLE:
                return "triangle"
            elif selection_type == Selection.Type.RHOMBUS:
                return "rhombus"
            elif selection_type == Selection.Type.CUSTOM:
                return "custom"
            else:
                return "INVALID VALUE"

    @staticmethod
    def get_selection(selection_type, max_range, hex_radius):
        hex_map = hx.HexMap()
        hexes = []
        axial_coordinates = []

        if selection_type == Selection.Type.RECT:
            for r in range(-max_range, max_range + 3):
                r_offset = r >> 1
                for q in range(-max_range - r_offset, max_range - r_offset):
                    c = [q, r]
                    axial_coordinates.append(c)
                    hexes.append(ExampleHex(c, [141, 207, 104, 255], hex_radius))      
  
        elif selection_type == Selection.Type.HEX:
            spiral_coordinates = hx.get_spiral(np.array((0, 0, 0)), 1, max_range) # Gets spiral coordinates from center
            axial_coordinates = hx.cube_to_axial(spiral_coordinates)

            for i, axial in enumerate(axial_coordinates):
                hex_color = list(COLORS[2]) # set color of hex
                hex_color.append(255) #set alpha to 255
                hexes.append(ExampleHex(axial, hex_color, hex_radius)) 

        elif selection_type == Selection.Type.TRIANGLE:
            top = int(max_range / 2)
            for q in range(0, max_range + 1):
                for r in range(0, max_range - q + 1):
                    c = [q, r]
                    axial_coordinates.append(c)
                    hexes.append(ExampleHex(c, [141, 207, 104, 255], hex_radius))

               

        elif selection_type == Selection.Type.RHOMBUS:
            q1 = int(-max_range / 2)
            q2 = int(max_range / 2)
            r1 = -max_range
            r2 = max_range

            # Parallelogram
            for q in range(q1, q2 + 1):
                for r in range(r1, r2 + 1):
                    axial_coordinates.append([q, r])
                    hexes.append(ExampleHex([q, r], [141, 207, 104, 255], hex_radius)) 

        elif selection_type == Selection.Type.CUSTOM:
            axial_coordinates.append([0, 0])
            hexes.append(ExampleHex([0, 0], [141, 207, 104, 255], hex_radius))

        hex_map[np.array(axial_coordinates)] = hexes # create hex map  
        return hex_map


class ClampedInteger:
    """
    A simple class for "clamping" an integer value between a range. Its value will not increase beyond `upper_limit`
    and will not decrease below `lower_limit`.
    """
    def __init__(self, initial_value, lower_limit, upper_limit):
        self.value = initial_value
        self.lower_limit = lower_limit
        self.upper_limit = upper_limit

    def increment(self):
        self.value += 1
        if self.value > self.upper_limit:
            self.value = self.upper_limit

    def decrement(self):
        self.value -= 1
        if self.value < self.lower_limit:
            self.value = self.lower_limit

def make_hex_surface(color, radius, border_color=(100, 100, 100), border=True, hollow=False):
    """
    Draws a hexagon with gray borders on a pygame surface.
    :param color: The fill color of the hexagon.
    :param radius: The radius (from center to any corner) of the hexagon.
    :param border_color: Color of the border.
    :param border: Draws border if True.
    :param hollow: Does not fill hex with color if True.
    :return: A pygame surface with a hexagon drawn on it
    """
    angles_in_radians = np.deg2rad([60 * i + 30 for i in range(6)])
    x = radius * np.cos(angles_in_radians)
    y = radius * np.sin(angles_in_radians)
    points = np.round(np.vstack([x, y]).T)

    sorted_x = sorted(points[:, 0])
    sorted_y = sorted(points[:, 1])
    minx = sorted_x[0]
    maxx = sorted_x[-1]
    miny = sorted_y[0]
    maxy = sorted_y[-1]

    sorted_idxs = np.lexsort((points[:, 0], points[:, 1]))

    surf_size = np.array((maxx - minx, maxy - miny)) * 2 + 1
    center = surf_size / 2
    surface = pg.Surface(surf_size.astype(int))
    surface.set_colorkey((0, 0, 0))

    # Set alpha if color has 4th coordinate.
    if len(color) >= 4:
        surface.set_alpha(color[-1])

    # fill if not hollow.
    if not hollow:
        pg.draw.polygon(surface, color, (points + center).astype(int), 0)


    points[sorted_idxs[-1:-4:-1]] += [0, 1]
    # if border is true or hollow is true draw border.
    if border or hollow:
        pg.draw.lines(surface, border_color, True, (points + center).astype(int), 1)

    return surface


class ExampleHex(hx.HexTile):
    def __init__(self, axial_coordinates, color, radius):
        self.axial_coordinates = np.array([axial_coordinates])
        self.cube_coordinates = hx.axial_to_cube(self.axial_coordinates)
        self.position = hx.axial_to_pixel(self.axial_coordinates, radius)
        self.color = color
        self.radius = radius
        self.image = make_hex_surface(color, radius)

    def get_draw_position(self):
        """
        Get the location to draw this hex so that the center of the hex is at `self.position`.
        :return: The location to draw this hex so that the center of the hex is at `self.position`.
        """
        draw_position = self.position[0] - [self.image.get_width() / 2, self.image.get_height() / 2]
        return draw_position

    def get_position(self):
        """
        Retrieves the location of the center of the hex.
        :return: The location of the center of the hex.
        """
        return self.position[0]

class ExampleHexMap:
    def __init__(self, num_pieces, size=(1000, 1000), hex_radius=20, caption="Config File Creator"):
        self.caption = caption              # Controls window caption
        self.size = np.array(size)          # Controls window size
        self.width, self.height = self.size # Width and height of window
        self.center = self.size / 2         # Should be center of window

        self.num_pieces = num_pieces

        self.hex_radius = hex_radius        # Radius of individual hexagons

        self.max_coord = 13                 # Controls the radius of the hex map in hexagon shape.

        self.selection = ClampedInteger(1, 0, 4)  # Clamps the radius to a default of 3, with a min of 1 and max of 5. This
                                            # is related to the ring and disk functions.

        self.piece_selection = ClampedInteger(1, 1, num_pieces)
        self.player_selection = ClampedInteger(1, 1, 2)

        self.old_selection = self.selection.value
        self.clicked_hex = np.array([0, 0, 0])      # Center hex

        self.hex_map = Selection.get_selection(self.selection.value, self.max_coord, self.hex_radius)

        self.b_map = hx.HexMap()
        b_hexes = []
        b_axial_coordinates = []
        for r in range(-self.max_coord, self.max_coord + 3):
            r_offset = r >> 1
            for q in range(-self.max_coord - r_offset, self.max_coord - r_offset):
                c = [q, r]
                b_axial_coordinates.append(c)
                b_hexes.append(ExampleHex(c, [141, 207, 250, 255], hex_radius))

        self.b_map[np.array(b_axial_coordinates)] = b_hexes

        self.step = 1

        # pygame specific variables
        self.main_surf = None # Pygame surface
        self.font = None      # Pygame font
        self.clock = None     # Pygame fps
        self.init_pg()        # Starts pygame

    def init_pg(self):
        pg.init()
        self.main_surf = pg.display.set_mode(self.size) # Turns main_surf into a display
        pg.display.set_caption(self.caption)

        pg.font.init()
        self.font = pg.font.SysFont("monospace", 20, True)
        self.clock = pg.time.Clock()

    def handle_events(self):
        running = True # Program is running
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

            if event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:# Left mouse
                    self.clicked_hex = hx.pixel_to_cube(
                            np.array([pg.mouse.get_pos() - self.center]), 
                            self.hex_radius)
                    self.clicked_hex = self.clicked_hex[0]

                if self.step == 1:
                    if event.button == 4: #Scroll up
                        self.selection.increment()
                    if event.button == 5: #scroll down
                        self.selection.decrement()
                elif self.step == 2:
                    if event.button == 4: #Scroll up
                        self.piece_selection.increment()
                    if event.button == 5: #scroll down
                        self.piece_selection.decrement()

            if event.type == pg.KEYUP:
                if self.step == 2:
                    if event.key == pg.K_RIGHT:
                        self.player_selection.increment()
                    elif event.key == pg.K_LEFT:
                        self.player_selection.decrement()

            if event.type == pg.KEYDOWN:
                if event.key == pg.K_RETURN:
                    self.step += 1
                if event.key == pg.K_ESCAPE or self.step > 2:
                    running = False

        return running

    def main_loop(self):
        running = self.handle_events()

        return running

    def draw(self):

        if self.step == 1:
            b_hexagons = list(self.b_map.values())
            b_hex_positions = np.array([hexagon.get_draw_position() for hexagon in b_hexagons])
            b_sorted_indexes = np.argsort(b_hex_positions[:, 1])
            for index in b_sorted_indexes:
                self.main_surf.blit(b_hexagons[index].image, (b_hex_positions[index] + self.center).astype(int)) #Draws the hexagons on
                    #hexagons[index].image uses an image created in example_hex from make_hex_surface
            self.b_start = True
                
            if self.selection.value != self.old_selection:
                self.hex_map = Selection.get_selection(self.selection.value, self.max_coord, self.hex_radius)
                self.old_selection = self.selection.value

            # show all hexes
            hexagons = list(self.hex_map.values())
            hex_positions = np.array([hexagon.get_draw_position() for hexagon in hexagons])
            sorted_indexes = np.argsort(hex_positions[:, 1])
            for index in sorted_indexes:
                self.main_surf.blit(hexagons[index].image, (hex_positions[index] + self.center).astype(int)) #Draws the hexagons on
                #hexagons[index].image uses an image created in example_hex from make_hex_surface


            mouse_pos = np.array([np.array(pg.mouse.get_pos()) - self.center])
            cube_mouse = hx.pixel_to_axial(mouse_pos, self.hex_radius)

            selection_type_text = self.font.render(
                    "Board Shape: " + Selection.Type.to_string(self.selection.value),
                    True,
                    (50, 50, 50))
            self.main_surf.blit(selection_type_text, (5, 30))

        if self.step == 2:
            hexagons = list(self.hex_map.values())
            hex_positions = np.array([hexagon.get_draw_position() for hexagon in hexagons])
            sorted_indexes = np.argsort(hex_positions[:, 1])
            for index in sorted_indexes:
                self.main_surf.blit(hexagons[index].image, (hex_positions[index] + self.center).astype(int))

            player_text = self.font.render(
                "Current Player: " + str(self.player_selection.value),
                True, 
                (50, 50, 50))
            piece_selection_text = self.font.render(
                    "Piece Type: " + str(self.piece_selection.value),
                    True,
                    (50, 50, 50))

            # TODO: Have pieces added to the board when the player clicks, keep the pieces in a list
            # and then dump the player list and board to the config file.
            
            self.main_surf.blit(player_text, (5, 20))
            self.main_surf.blit(piece_selection_text, (5, 40))

        fps_text = self.font.render(" FPS: " + str(int(self.clock.get_fps())), True, (50, 50, 50))
        self.main_surf.blit(fps_text, (5, 0))    

        # Update screen at 30 frames per second
        pg.display.update()
        self.main_surf.fill(COLORS[-1])
        self.clock.tick(30)

    def quit_app(self):
        board = dict()
        hexagons = list(self.hex_map.values())

        #print(list(hexagons[0].axial_coordinates[0]))
        board['board'] = [hex.axial_coordinates[0].tolist() for hex in hexagons]
        pg.quit()
        return board

if __name__ == '__main__':
    #file = open('settings/settings.yaml')
    #test_list = yaml.safe_load(file)
    #print(test_list)

    settings = dict()
    num_pieces = int(input('Number of piece types: '))

    while num_pieces <= 0:
        print("Invalid number of pieces.")
        num_pieces = int(input('Number of piece types: '))

    pieces_list = dict()
    for i in range(1, num_pieces + 1):
        print("Settings for piece type {}:".format(i))
        health = int(input("health: "))
        distance = int(input("distance: "))
        attack = int(input("attack power: "))
        pieces_list[i] = {'health': health, 'distance': distance, 'attack': attack}

    #print(pieces_list)
    settings['pieces'] = pieces_list
        
    file = open(r'settings/test_writer.yaml', 'w')
    file.write("---\n")
    docs = yaml.dump(settings, file, sort_keys=False)

    example_hex_map = ExampleHexMap(num_pieces)

    while example_hex_map.main_loop():
        example_hex_map.draw()

    board = example_hex_map.quit_app()
    board_docs = yaml.dump(board, file, default_flow_style = None)
    file.write("...")