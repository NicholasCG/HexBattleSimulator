# This is needed becuase pygame's init() calls for an audio driver,
# which seemed to default to ALSA, which was causing an underrun error.
import os

os.environ['SDL_AUDIODRIVER'] = 'dsp'

import yaml
import numpy as np
import hexy as hx
import pygame as pg
from tkinter import filedialog, Tk

COL_IDX = np.random.randint(0, 4, (7 ** 3))
COLORS = np.array([
    [251, 149, 80],   # orange    [244, 98, 105]
    [207, 0, 0],   # red
    [0, 255, 255],  # sky blue
    [141, 207, 104],   # green
    [85, 163, 193],   # sky blue
])

DIRECTIONS = ["SE", "SW", "W", "NW", "NE", "E"]

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
            for r in range(-max_range, max_range + 1):
                r_offset = r >> 1
                for q in range(-max_range - r_offset, max_range - r_offset):
                    c = [q, r]
                    axial_coordinates.append(c)
                    hexes.append(ExampleHex(c, [141, 207, 104, 255], hex_radius))      
  
        elif selection_type == Selection.Type.HEX:
            spiral_coordinates = hx.get_spiral(np.array((0, 0, 0)), 1, max_range) # Gets spiral coordinates from center
            axial_coordinates = hx.cube_to_axial(spiral_coordinates)

            for i, axial in enumerate(axial_coordinates):
                hex_color = list(COLORS[3]) # set color of hex
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

class CyclicInteger:
    """
    A simple helper class for "cycling" an integer through a range of values. Its value will be set to `lower_limit`
    if it increases above `upper_limit`. Its value will be set to `upper_limit` if its value decreases below
    `lower_limit`.
    """
    def __init__(self, initial_value, lower_limit, upper_limit):
        self.value = initial_value
        self.lower_limit = lower_limit
        self.upper_limit = upper_limit

    def increment(self):
        self.value += 1
        if self.value > self.upper_limit:
            self.value = self.lower_limit

    def decrement(self):
        self.value -= 1
        if self.value < self.lower_limit:
            self.value = self.upper_limit

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
    def __init__(self, axial_coordinates, color, radius, hollow = False):
        self.axial_coordinates = np.array([axial_coordinates])
        self.cube_coordinates = hx.axial_to_cube(self.axial_coordinates)
        self.position = hx.axial_to_pixel(self.axial_coordinates, radius)
        self.color = color
        self.radius = radius
        self.image = make_hex_surface(color, radius, hollow = hollow)

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
    def __init__(self, num_pieces, hex_radius=20, caption="Config File Creator"):

        root = Tk()
        size = (root.winfo_screenheight(), root.winfo_screenheight())
        root.destroy()
        
        self.caption = caption              # Controls window caption
        self.size = np.array(size)          # Controls window size
        self.width, self.height = self.size # Width and height of window
        self.center = self.size / 2         # Should be center of window

        self.num_pieces = num_pieces

        self.hex_radius = int(hex_radius * self.size[0] / 1000)      # Radius of individual hexagons

        self.max_coord = ClampedInteger(13, 1, 13) # Controls the radius of the hex map in hexagon shape.
        self.selection = ClampedInteger(1, 0, 4)  # Controls map style selection in step 1.
        self.piece_selection = CyclicInteger(1, 1, num_pieces) # Controls piece type in step 2.
        self.player_selection = CyclicInteger(1, 1, 2) # Controls player in step 2.
        self.direction_selection = CyclicInteger(0, 0, 5) # Controls direction of pieces in step 2.

        self.old_selection = self.selection.value # Saves old selection, used so a new map isn't generated every turn.
        self.old_max = self.max_coord.value # Holds the old maximum size.
        self.old_axial_held = np.array([]) # Hold the old axial coordinates the mouse is at in custom map mode.

        self.clicked_hex = np.array([0, 0])      # Center hex
        self.direction_hex = np.array([])

        self.selected_hex_image = make_hex_surface(
                (128, 128, 128, 255),               # Highlight color for a hexagon.
                self.hex_radius,                    # radius of individual hexagon
                (255, 255, 255),                    # Border color white
                hollow=True)  

        self.hex_map = Selection.get_selection(self.selection.value, self.max_coord.value, self.hex_radius)

        self.b_map = hx.HexMap()
        b_hexes = []
        b_axial_coordinates = []
        for r in range(-self.max_coord.value, self.max_coord.value + 1):
            r_offset = r >> 1
            for q in range(-self.max_coord.value - r_offset, self.max_coord.value - r_offset):
                c = [q, r]
                b_axial_coordinates.append(c)
                b_hexes.append(ExampleHex(c, [141, 207, 250, 255], self.hex_radius, hollow = False))

        self.b_map[np.array(b_axial_coordinates)] = b_hexes

        self.step = 1
        self.player_list = {1: [], 2: []}
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
            if event.type == pg.MOUSEBUTTONUP:
                if event.button == 1:# Left mouse
                    self.clicked_hex = hx.pixel_to_axial(
                            np.array([pg.mouse.get_pos() - self.center]), 
                            self.hex_radius)[0].astype(np.int32)

                    if self.step == 2:
                        if np.array_equal(self.hex_map[self.clicked_hex], []):
                            self.clicked_hex = self.old_axial_held
                            continue

                        if not np.array_equal(self.clicked_hex, self.old_axial_held):
                            self.direction_hex = np.array([])

                        index = 0
                        repeat = False
                        for piece in self.player_list[1]:
                            if np.array_equal(piece[1], self.clicked_hex):
                                del self.player_list[1][index]
                                repeat = True
                            else:
                                index += 1

                        index = 0
                        for piece in self.player_list[2]:
                            if np.array_equal(piece[1], self.clicked_hex):
                                del self.player_list[2][index]
                                repeat = True
                            else:
                                index += 1

                        if repeat:
                            continue

                        if self.clicked_hex.size > 0:
                            if self.direction_hex.size <= 0:
                                self.direction_hex = self.clicked_hex
                            else:
                                self.direction_hex = np.array([])

                                if not repeat:
                                    self.player_list[self.player_selection.value].append([self.piece_selection.value, 
                                                                                        self.clicked_hex, 
                                                                                        self.direction_selection.value])
                                self.direction_selection.value = 0

                        self.old_axial_held = self.clicked_hex
                        
                
            if event.type == pg.MOUSEBUTTONDOWN:
                if self.step == 1:
                    if event.button == 4: #Scroll up
                        self.selection.increment()
                    if event.button == 5: #scroll down
                        self.selection.decrement()
                elif self.step == 2:
                    if event.button == 3:
                        self.player_selection.increment()
                    if event.button == 4: #Scroll up
                        self.direction_selection.increment()
                    if event.button == 5: #scroll down
                        self.direction_selection.decrement()

            if event.type == pg.KEYUP:
                if self.step == 1:
                    if event.key == pg.K_RIGHT:
                        self.max_coord.increment()
                    elif event.key == pg.K_LEFT:
                        self.max_coord.decrement()
                elif self.step == 2:
                    if event.key == pg.K_RIGHT:
                        self.piece_selection.increment()
                    elif event.key == pg.K_LEFT:
                        self.piece_selection.decrement()
                    elif event.key == pg.K_a:
                        self.direction_selection.decrement()
                    elif event.key == pg.K_d:
                        self.direction_selection.increment()

            if event.type == pg.KEYDOWN:
                if event.key == pg.K_RETURN:
                    self.step += 1
                if event.key == pg.K_ESCAPE or self.step > 2:
                    running = False

            # Check if we are in the map-making step, and it is a custom map.
            if self.step == 1 and self.selection.value == Selection.Type.CUSTOM:

                # Check that the left mouse is being held down and the mouse is moving.
                if event.type == pg.MOUSEMOTION and event.buttons == (1, 0, 0):
                    mouse_pos = np.array([np.array(pg.mouse.get_pos()) - self.center])
                    axial_clicked = hx.pixel_to_axial(mouse_pos, self.hex_radius).astype(np.int32)[0]

                    # Check if within the map boundaries and the mouse is not on the same tile as before.
                    if not np.array_equal(self.b_map[axial_clicked], []) and not np.array_equal(axial_clicked, self.old_axial_held):

                            # Check if a tile already exists. If not, create one. If one does, delete it.
                            if np.array_equal(self.hex_map[axial_clicked], []):
                                self.hex_map[[axial_clicked]] = [ExampleHex(axial_clicked, [141, 207, 104, 255], self.hex_radius)]
                            else:
                                del self.hex_map[axial_clicked]

                            # Save the axial coordinates so the tile is not added and delete every other frame.
                            self.old_axial_held = axial_clicked
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
                
            if self.selection.value != self.old_selection or self.max_coord.value != self.old_max:
                self.hex_map = Selection.get_selection(self.selection.value, self.max_coord.value, self.hex_radius)
                self.old_selection = self.selection.value
                self.old_max = self.max_coord.value

            # show all hexes
            hexagons = list(self.hex_map.values())
            hex_positions = np.array([hexagon.get_draw_position() for hexagon in hexagons])
            sorted_indexes = np.argsort(hex_positions[:, 1])
            for index in sorted_indexes:
                self.main_surf.blit(hexagons[index].image, (hex_positions[index] + self.center).astype(int)) #Draws the hexagons on
                #hexagons[index].image uses an image created in example_hex from make_hex_surface

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
                self.main_surf.blit(hexagons[index].image, (hex_positions[index] + self.center).astype(np.int32))

            if self.direction_hex.size > 0:
                pixels = self.hex_map[self.clicked_hex][0].get_draw_position() + self.center
                self.main_surf.blit(self.selected_hex_image, pixels.astype(np.int32))
                # This index is used to find the two angles for the directional triangle.
                index = self.direction_selection.value
                # Find the radian angles of the direction, and scale to the hex radius
                angles_in_radians = np.deg2rad([60 * i + 30 for i in range(index, index + 2)])
                x = self.hex_radius * np.cos(angles_in_radians)
                y = self.hex_radius * np.sin(angles_in_radians)

                # Merge all points to a single array of a triangle
                points = np.round(np.vstack([x, y]).T)
                points = np.round(np.vstack([points, [0, 0]]))
                
                # Find pixel coordinates for the triangle, then find the middle point of the far edge, and draw the line.
                coords = (points + hx.axial_to_pixel(self.clicked_hex, self.hex_radius))
                start_point = coords[2] + self.center
                end_point = (coords[0] + coords[1]) / 2 + self.center
                pg.draw.line(self.main_surf, [230, 230, 0], start_point.astype(np.int32), end_point.astype(np.int32), 3)

            player_text = self.font.render(
                "Current Player: " + str(self.player_selection.value),
                True, 
                (50, 50, 50))
            piece_selection_text = self.font.render(
                    "Piece Type: " + str(self.piece_selection.value),
                    True,
                    (50, 50, 50))

            for piece1 in self.player_list[1]:
                text = self.font.render(str(piece1[0]), False, COLORS[1])
                pos = hx.axial_to_pixel(piece1[1], self.hex_radius)
                text_pos = pos + self.center
                text_pos -= (text.get_width() / 2, text.get_height() / 2)
                self.main_surf.blit(text, text_pos.astype(np.int32))

                # This index is used to find the two angles for the directional triangle.
                index = piece1[2]
                # Find the radian angles of the direction, and scale to the hex radius
                angles_in_radians = np.deg2rad([60 * i + 30 for i in range(index, index + 2)])
                x = self.hex_radius * np.cos(angles_in_radians)
                y = self.hex_radius * np.sin(angles_in_radians)

                # Merge all points to a single array of a triangle
                points = np.round(np.vstack([x, y]).T)
                points = np.round(np.vstack([points, [0, 0]]))
                
                # Find pixel coordinates for the triangle, then find the middle point of the far edge, and draw the line.
                coords = (points + hx.axial_to_pixel(piece1[1], self.hex_radius))
                start_point = coords[2] + self.center
                end_point = (coords[0] + coords[1]) / 2 + self.center
                pg.draw.line(self.main_surf, [230, 230, 0], start_point.astype(np.int32), end_point.astype(np.int32), 3)

            for piece2 in self.player_list[2]:
                text = self.font.render(str(piece2[0]), False, COLORS[2])
                pos = hx.axial_to_pixel(piece2[1], self.hex_radius)
                text_pos = pos + self.center
                text_pos -= (text.get_width() / 2, text.get_height() / 2)
                self.main_surf.blit(text, text_pos.astype(np.int32))

                # This index is used to find the two angles for the directional triangle.
                index = piece2[2]
                # Find the radian angles of the direction, and scale to the hex radius
                angles_in_radians = np.deg2rad([60 * i + 30 for i in range(index, index + 2)])
                x = self.hex_radius * np.cos(angles_in_radians)
                y = self.hex_radius * np.sin(angles_in_radians)

                # Merge all points to a single array of a triangle
                points = np.round(np.vstack([x, y]).T)
                points = np.round(np.vstack([points, [0, 0]]))
                
                # Find pixel coordinates for the triangle, then find the middle point of the far edge, and draw the line.
                coords = (points + hx.axial_to_pixel(piece2[1], self.hex_radius))
                start_point = coords[2] + self.center
                end_point = (coords[0] + coords[1]) / 2 + self.center
                pg.draw.line(self.main_surf, [230, 230, 0], start_point.astype(np.int32), end_point.astype(np.int32), 3)

            self.main_surf.blit(player_text, (5, 20))
            self.main_surf.blit(piece_selection_text, (5, 40))

        # Update screen at 30 frames per second
        pg.display.update()
        self.main_surf.fill(COLORS[-1])
        self.clock.tick(30)

    def quit_app(self):
        board = dict()
        onepieces = dict()
        twopieces = dict()

        hexagons = list(self.hex_map.values())

        board['board'] = [hex.axial_coordinates[0].astype(np.int32).tolist() for hex in hexagons]

        # TODO: Allow player to pick the direction of each piece. For now, have dummy direction.
        #print(DIRECTIONS[self.player_list[1][0][2]])
        # print(self.player_list[1][0])
        # print(self.player_list[1][0][2])
        onepieces['player1'] = {i + 1: [self.player_list[1][i][0], 
                                        self.player_list[1][i][1].tolist(), 
                                        DIRECTIONS[self.player_list[1][i][2]]] 
                                for i in range(0, len(self.player_list[1]))}

        twopieces['player2'] = {i + 1: [self.player_list[2][i][0], 
                                        self.player_list[2][i][1].tolist(), 
                                        DIRECTIONS[self.player_list[2][i][2]]] 
                                for i in range(0, len(self.player_list[2]))}
        pg.quit()
        return board, onepieces, twopieces

if __name__ == '__main__':
    print("\n\nInstructions for use:\n")
    print("Step 1: Piece templates. Input the number of piece templates to be created, ")
    print("and give the maximum health, attack power, and moving distance for each template.\n")

    print("Step 2: Create the board. A window should pop up that allows you to create a board from")
    print("a select number of types. Use the left and right arrow keys to change the size of the map.")
    print("A custom board mode is in development.\n")

    print("Step 3: Place pieces on the board. The window will stay open, but will now not allow you")
    print("to change the board. Use the scroll wheel to cycle through piece templates, and use the")
    print("right mouse to alternate between players 1 and 2.\n")

    settings = dict()
    num_pieces = int(input('Number of piece types: '))

    while num_pieces <= 0:
        print("Invalid number of pieces.")
        num_pieces = int(input('Number of piece types: '))

    pieces_list = dict()
    for i in range(1, num_pieces + 1):
        print("Settings for piece type {}:".format(i))
        health = int(input("health: "))
        distance = int(input("movement distance: "))
        attack_d = int(input("attack distance: "))
        power = int(input("attack power: "))
        pieces_list[i] = {'health': health, 'movement_d': distance, 'attack_d': attack_d, 'power': power}

    settings['pieces'] = pieces_list

    example_hex_map = ExampleHexMap(num_pieces)

    while example_hex_map.main_loop():
        example_hex_map.draw()

    board, player1, player2 = example_hex_map.quit_app()

    root = Tk()
    root.withdraw()
    f = filedialog.asksaveasfile(mode='w', initialdir = 'settings/', defaultextension=".yaml")
    root.destroy()
    if not f is None:
        f.write("---\n")
        yaml.dump(settings, f, sort_keys=False)
        yaml.dump(player1, f, default_flow_style=None)
        yaml.dump(player2, f, default_flow_style=None)
        yaml.dump(board, f, default_flow_style = None)
        f.write("...")
        f.close()

    input("Press enter to close...")
    raise SystemExit
