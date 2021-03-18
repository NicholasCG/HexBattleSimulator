# This is needed becuase pygame's init() calls for an audio driver,
# which seemed to default to ALSA, which was causing an underrun error.
import os

os.environ['SDL_AUDIODRIVER'] = 'dsp'

import hexy as hx
import numpy as np
import pygame as pg
import tkinter.filedialog
import tkinter as tk

import hex_board as hxgame

COLORS = np.array([
    #[141, 207, 104],  # green
    [96, 171, 127], # new green
    [207, 0, 0],   # red
    [0, 255, 255],   # light blue
    [36, 65, 255]     # ocean blue
])

HCOLORS = np.array([
    [255, 0, 0], # red
    [0, 255, 0], # green
    [255, 128, 0] # orange

])

DIRECTIONS = np.array(["SE", "SW", "W", "NW", "NE", "E"])
TESTING = False

root = tk.Tk()
root.withdraw()
size = (root.winfo_screenheight(), root.winfo_screenheight())
root.destroy()
scale = size[0] / 1000

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

    surf_size = np.array((maxx - minx, maxy - miny), dtype=np.int) * 2 + 1
    center = surf_size / 2
    surface = pg.Surface(surf_size)
    surface.set_colorkey((0, 0, 0))

    # Set alpha if color has 4th coordinate.
    if len(color) >= 4:
        surface.set_alpha(color[-1])

    # fill if not hollow.
    if not hollow:
        pg.draw.polygon(surface, color, points.astype(np.int) + center.astype(np.int), 0)


    points[sorted_idxs[-1:-4:-1]] += [0, 1]
    # if border is true or hollow is true draw border.
    if border or hollow:
        pg.draw.lines(surface, border_color, True, points.astype(np.int) + center.astype(np.int), 1)

    return surface

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

class Button():
    '''
    Basic Button class for visual interface.
    Code from Tech With Tim. https://www.youtube.com/c/TechWithTim
    '''
    def __init__(self, color, x,y,width,height, text=''):
        self.color = color
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text

    def draw(self,win,outline=None):
        #Call this method to draw the button on the screen
        if outline:
            pg.draw.rect(win, outline, (self.x-2,self.y-2,self.width+4,self.height+4),0)
            
        pg.draw.rect(win, self.color, (self.x,self.y,self.width,self.height),0)
        
        if self.text != '':
            font = pg.font.SysFont('arial', int(50 * scale), True)
            text = font.render(self.text, 1, (0,0,0))
            win.blit(text, (int(self.x + (self.width/2 - text.get_width()/2)), 
                            int(self.y + (self.height/2 - text.get_height()/2))))

    def isOver(self, pos):
        #Pos is the mouse position or a tuple of (x,y) coordinates
        if pos[0] > self.x and pos[0] < self.x + self.width:
            if pos[1] > self.y and pos[1] < self.y + self.height:
                return True
            
        return False

class VisualHex(hx.HexTile):
    '''
    Class for holding information about hexagon tiles
    drawn to the screen.
    '''
    def __init__ (self, axial_coordinates, color, radius):
        self.axial_coordinates = np.array([axial_coordinates])
        self.position = hx.axial_to_pixel(self.axial_coordinates, radius)
        self.color = color
        self.radius = radius
        self.image = make_hex_surface(color, radius, border=True)

    def get_color(self):
        return self.color

    def set_color(self, color):
        self.image = make_hex_surface(color, self.radius)
        self.color = color

    def get_draw_position(self):
        
        draw_pos = self.position[0] - (self.image.get_width() / 2, self.image.get_height() / 2)
        return draw_pos

    def get_position(self):
        return self.position[0]

    def get_axial_coords(self):
        return self.axial_coordinates

class VisualHexMap:
    '''
    Class for creating a new GameBoard and drawing
    visuals to the screen. Displays the board, pieces,
    health, and moves for each player's pieces.
    '''
    def __init__(self, hex_radius = 20, caption = "Hex Battle Simulator"):

        self.size = np.array(size)
        self.width, self.height = self.size
        #self.center = (0 + hex_radius, 0 + hex_radius)
        self.center = (self.size / 2).astype(np.int)
        self.hex_radius = int(hex_radius * scale)      # Radius of individual hexagons
        self.caption = caption
        self.board = hxgame.GameBoard()
        self.game_map = self.board.get_board()
        self.win_state = 0

        self.hex_map = hx.HexMap()
        hexes = [VisualHex(coords.get_axial_coords(), 
                            COLORS[0], 
                            self.hex_radius) for coords in self.game_map]
        
        self.hex_map[np.array([c.get_axial_coords() for c in self.game_map])] = hexes

        self.selected_hex_image = make_hex_surface(
                (128, 128, 128, 255),               # Highlight color for a hexagon.
                self.hex_radius,                    # radius of individual hexagon
                (255, 255, 255),                    # Border color white
                hollow=True)  

        self.clicked_hex = None
        self.valid_moves = None
        self.axial_moves = None

        self.select_direction = CyclicInteger(0, 0, 5)
        self.turn_button = Button((0, 255, 0), int(750 * scale), 
                                                int(20 * scale), 
                                                int(225 * scale),
                                                int(75 * scale), 
                                                'End Turn')

        self.main_surf = None
        self.font = None
        self.fps_font = None
        self.clock = None
        self.init_pg()

    def init_pg(self):
        pg.init()
        self.main_surf = pg.display.set_mode(self.size)
        pg.display.set_caption(self.caption)

        pg.font.init()
        self.font = pg.font.SysFont("monospace", self.hex_radius, True)
        self.fps_font = pg.font.SysFont("monospace", int(20 * scale), True)
        self.player_font = pg.font.SysFont('arial', int(40 * scale), True)
        if TESTING:
            self.test_font = pg.font.SysFont("monospace", 10, True)
        self.clock = pg.time.Clock()

    def handle_events(self):
        running = True
        for event in pg.event.get():
            pos = pg.mouse.get_pos()
            if event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:# Left mouse
                    mouse_pos = np.array([np.array(pos) - self.center])
                    axial_clicked = hx.pixel_to_axial(mouse_pos, self.hex_radius).astype(np.int)
                    try:
                        axial_player = self.board.__getitem__(axial_clicked)[0].piece.player
                        if (np.array_equal(self.valid_moves, None)) and axial_player == self.board.player:
                            self.clicked_hex = axial_clicked
                            self.axial_moves = self.board.get_valid_moves(self.board[self.clicked_hex][0])
                            self.axial_moves = np.array([[i[0], i[1]] for i in self.axial_moves])
                    except IndexError:
                        pass

                    if not np.array_equal(self.clicked_hex, None) and not np.array_equal(self.valid_moves, None):
                        try:
                            if self.board.__getitem__(axial_clicked)[0] in self.board.__getitem__(self.valid_moves):

                                self.board.move_piece(self.clicked_hex[0], axial_clicked[0])
                                self.game_map = self.board.get_board()

                        except IndexError:
                            pass

                        finally:
                            self.clicked_hex = None
                            self.axial_moves = None
                            self.valid_moves = None

                if event.button == 4: #Scroll up
                    self.select_direction.increment()
                if event.button == 5: #scroll down
                    self.select_direction.decrement()

                if self.turn_button.isOver(pos):
                    self.win_state = self.board.end_turn()

            if event.type == pg.MOUSEMOTION:
                if self.turn_button.isOver(pos):
                    self.turn_button.color = (0, 194, 0)
                else:
                    self.turn_button.color = (0, 255, 0)
                        

            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                running = False

            if self.win_state != 0:
                print("Player", self.win_state, "has won!")
                running = False

        return running

    def main_loop(self):
        running = self.handle_events()

        return running

    def draw(self):

        hexagons = list(self.hex_map.values())
        hex_positions = np.array([hexagon.get_draw_position() for hexagon in hexagons])
        sorted_indexes = np.argsort(hex_positions[:, 1])

        # Draw game hexagons
        for index in sorted_indexes:
            self.main_surf.blit(hexagons[index].image, (hex_positions[index] + self.center).astype(np.int))
            if TESTING:
                v_coords = hexagons[index].get_axial_coords()[0]
                c_text = self.test_font.render(str(v_coords[0]) +"," + str(v_coords[1]), True, (255, 255, 255))
                c_width = self.test_font.size(str(v_coords[0]) +"," + str(v_coords[1]))[0]
                self.main_surf.blit(c_text, (hexagons[index].get_position() + self.center - c_width / 2).astype(np.int))
        # Draw pieces
        for piece in self.game_map:
            w = piece.piece.p_type
            if w != 0:
                # Draw piece
                text = self.font.render(str(w), False, COLORS[piece.piece.player], (0, 0, 0))
                text.set_alpha(160)
                pos = hx.axial_to_pixel(piece.get_axial_coords(), self.hex_radius)
                text_pos = pos + self.center
                text_pos -= (text.get_width() / 2, text.get_height() / 2)
                self.main_surf.blit(text, text_pos.astype(np.int))

        # Draw valid moves if a piece is clicked
        if not np.array_equal(self.clicked_hex, None):

            # Draw direction of currently selected piece

            # This index is used to find the two angles for the directional triangle.
            index = np.where(DIRECTIONS == self.board[self.clicked_hex][0].piece.direction)[0][0]
            # Find the radian angles of the direction, and scale to the hex radius
            angles_in_radians = np.deg2rad([60 * i + 30 for i in range(index, index + 2)])
            x = self.hex_radius * np.cos(angles_in_radians)
            y = self.hex_radius * np.sin(angles_in_radians)

            # Merge all points to a single array of a triangle
            points = np.round(np.vstack([x, y]).T)
            points = np.round(np.vstack([points, [0, 0]]))

            # Find pixel coordinates, and draw the triangle.
            coords = (points.astype(np.int) + hx.axial_to_pixel(self.clicked_hex, self.hex_radius)).astype(np.int32)
            pg.draw.polygon(self.main_surf, COLORS[-2], coords + self.center, 0)

            # Get the valid moves for a piece, and display them.
            visual_moves = self.hex_map[self.axial_moves]
            self.valid_moves = self.axial_moves

            list(map(self.draw_selected, visual_moves))

        # Draw health bars
        health_scale = scale * self.hex_radius / 20
        for piece in self.game_map:
            w = piece.piece.p_type
            if w != 0:
                mh = piece.get_piece().max_health
                ch = piece.get_piece().health
                pixel_pos = hx.axial_to_pixel(np.array(piece.get_axial_coords()), self.hex_radius)
                corner = (pixel_pos + self.center).astype(np.int) + ( int(-mh / 2 * health_scale), int(-20 * health_scale))
                rect_pos = np.array([corner[0], corner[1], mh * health_scale, 8 * health_scale]).astype(np.int)
                pg.draw.rect(self.main_surf, HCOLORS[0], rect_pos)
                ch_rect_pos = np.array([corner[0], corner[1], ch *health_scale, 8 * health_scale]).astype(np.int)
                pg.draw.rect(self.main_surf, HCOLORS[1], ch_rect_pos)

        # Display current FPS
        fps_text = self.fps_font.render(" FPS: " + str(int(self.clock.get_fps())), True, (50, 50, 50))
        player_text = self.player_font.render(" Player " + str(self.board.player) + " turn", True, COLORS[self.board.player])
        self.main_surf.blit(fps_text, (5, 0))
        
        # Display current player's turn
        player_width = self.player_font.size(" Player " + str(self.board.player) + " turn")[0]
        self.main_surf.blit(player_text, (int(self.center[0] - player_width / 2), int(20 * scale)))
        self.turn_button.draw(self.main_surf, (0, 0, 0))
        
        # Update window and keep background  
        pg.display.update()
        self.main_surf.fill(COLORS[-1])
        self.clock.tick(60)

    def draw_selected(self, hexagon):
        self.main_surf.blit(self.selected_hex_image, hexagon.get_draw_position().astype(np.int) + self.center)

    def quit_app(self):
        pg.quit()
        raise SystemExit

if __name__ == '__main__':

    # root = tk.Tk()
    # root.withdraw()
    # dirname = tk.filedialog.askopenfilename(initialdir = "settings/", title = "Select config file")
    # print(dirname)
    visual_hex_map = VisualHexMap()

    while visual_hex_map.main_loop():
        visual_hex_map.draw()

    visual_hex_map.quit_app()

