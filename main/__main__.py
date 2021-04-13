# This is needed becuase pygame's init() calls for an audio driver,
# which seemed to default to ALSA, which was causing an underrun error.
import os

os.environ['SDL_AUDIODRIVER'] = 'dsp'

import hexy as hx
import numpy as np
import pygame as pg
from tkinter import filedialog, Tk

import game_board as hxgame

COLORS = np.array([
    [96, 171, 127], # new green
    [207, 0, 0],   # red
    [0, 255, 255],   # light blue
    [36, 65, 255]     # ocean blue
])

DIRECTIONS = np.array(["SE", "SW", "W", "NW", "NE", "E"])
TESTING = 0

root = Tk()
root.withdraw()
size = (root.winfo_screenheight() - 50, root.winfo_screenheight() - 50)
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

    surf_size = np.array((maxx - minx, maxy - miny), dtype=np.int32) * 2 + 1
    center = surf_size / 2
    surface = pg.Surface(surf_size)
    surface.set_colorkey((0, 0, 0))

    # Set alpha if color has 4th coordinate.
    if len(color) >= 4:
        surface.set_alpha(color[-1])

    # fill if not hollow.
    if not hollow:
        pg.draw.polygon(surface, color, points.astype(np.int32) + center.astype(np.int32), 0)

    points[sorted_idxs[-1:-4:-1]] += [0, 1]
    # if border is true or hollow is true draw border.
    if border or hollow:
        pg.draw.lines(surface, border_color, True, points.astype(np.int32) + center.astype(np.int32), 1)

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
    def __init__(self, dirname, hex_radius = 20, caption = "Hex Battle Simulator"):

        self.size = np.array(size)
        self.width, self.height = self.size
        #self.center = (0 + hex_radius, 0 + hex_radius)
        self.center = (self.size / 2).astype(np.int32)
        self.hex_radius = int(hex_radius * scale)      # Radius of individual hexagons
        self.original_radius = self.hex_radius
        self.caption = caption
        self.board = hxgame.GameBoard(dirname)
        
        self.win_state = 0
        self.hex_map = hx.HexMap()

        temp_map_list = np.array([*self.board.values()])

        hexes = [VisualHex(coords.get_axial_coords(), 
                            COLORS[0], 
                            self.hex_radius) for coords in temp_map_list]
        
        self.hex_map[np.array([c.get_axial_coords() for c in temp_map_list])] = hexes

        self.movement_hex_image = make_hex_surface(
                (128, 128, 128, 255),               # Highlight color for a hexagon.
                self.hex_radius,                    # radius of individual hexagon
                (255, 255, 255),                    # Border color white
                hollow=True)  

        self.attack_hex_image = make_hex_surface(
                (128, 128, 128, 255),               # Highlight color for a hexagon.
                self.hex_radius,                    # radius of individual hexagon
                (255, 0, 0),                    # Border color white
                hollow=True)  

        self.moved_hex_image = make_hex_surface(
                (128, 128, 128, 255),               # Highlight color for a hexagon.
                self.hex_radius,                    # radius of individual hexagon
                (128, 128, 128, 255))  
        self.move_or_attack = 0

        self.clicked_hex = None
        self.axial_clicked = None
        self.valid_moves = None
        self.axial_moves = None
        self.temp_axial = None
        self.step = 1

        self.movement_counter = CyclicInteger(1, 1, 3)
        self.selected_movement_directions = []

        self.select_direction = CyclicInteger(0, 0, 5)
        self.turn_button = Button((0, 255, 0), int(750 * scale), 
                                                int(20 * scale), 
                                                int(225 * scale),
                                                int(75 * scale), 
                                                'End Turn')

        self.main_surf = None
        self.test_surf = None
        self.font = None
        self.fps_font = None
        self.clock = None
        self.init_pg()

    def init_pg(self):
        pg.init()
        self.main_surf = pg.display.set_mode(self.size)
        self.test_surf = pg.Surface((size[0], size[1] - int(20 * scale) - int(75 * scale)))
        self.test_center = (self.center[0], self.center[1] - int(100 * scale))
        pg.display.set_caption(self.caption)

        pg.font.init()
        self.font = pg.font.SysFont("monospace", self.hex_radius + 7, True)
        self.fps_font = pg.font.SysFont("monospace", int(20 * scale), True)
        self.player_font = pg.font.SysFont('arial', int(40 * scale), True)
        self.health_font = pg.font.SysFont("arial", self.hex_radius - 7, True)
        if TESTING:
            self.test_font = pg.font.SysFont("monospace", 10, True)
        self.clock = pg.time.Clock()

    def regenerate_size_objects(self):
        self.hex_map = hx.HexMap()
        temp_map_list = np.array([*self.board.values()])

        hexes = [VisualHex(coords.get_axial_coords(), 
                            COLORS[0], 
                            self.hex_radius) for coords in temp_map_list]
        
        self.hex_map[np.array([c.get_axial_coords() for c in temp_map_list])] = hexes

        self.movement_hex_image = make_hex_surface(
                (128, 128, 128, 255),               # Highlight color for a hexagon.
                self.hex_radius,                    # radius of individual hexagon
                (255, 255, 255),                    # Border color white
                hollow=True)  

        self.attack_hex_image = make_hex_surface(
                (128, 128, 128, 255),               # Highlight color for a hexagon.
                self.hex_radius,                    # radius of individual hexagon
                (255, 0, 0),                    # Border color white
                hollow=True)  

        self.moved_hex_image = make_hex_surface(
                (128, 128, 128, 255),               # Highlight color for a hexagon.
                self.hex_radius,                    # radius of individual hexagon
                (128, 128, 128, 255))  

        self.font = pg.font.SysFont("monospace", self.hex_radius + 7, True)
        self.health_font = pg.font.SysFont("arial", self.hex_radius - 7, True)

    def handle_events(self):
        running = True
        for event in pg.event.get():
            keys = pg.key.get_pressed()
            pos = pg.mouse.get_pos()
            rel_pos = pg.mouse.get_rel()

            if keys[pg.K_c]:
                self.test_center = (self.center[0], self.center[1] - int(100 * scale))
                self.hex_radius = self.original_radius
                self.regenerate_size_objects()
                
            if event.type == pg.MOUSEBUTTONUP: # Attacking or moving

                # Stops clicking on tiles that are hidden up top.
                if pos[1] <= int(100 * scale):
                    continue

                mouse_pos = np.array([np.array(pos) - self.test_center - [0, int(100 * scale)]])
                self.axial_clicked = hx.pixel_to_axial(mouse_pos, self.hex_radius).astype(np.int32)
                axial_player = self.board[self.axial_clicked]
                if event.button == 1: # Left Click (Move)
                    if self.step == 3:
                        if not np.array_equal(self.axial_clicked, self.temp_axial):
                            self.step = 2
                            self.temp_axial = self.axial_clicked
                            self.temp_axial = None
                            self.selected_movement_directions = []
                            
                    # Selecting a piece to move.
                    if self.step == 1:
                        if not np.array_equal(axial_player, []):
                            axial_player = self.board[self.axial_clicked][0].piece.player
                        else:
                            pass

                        found = False
                        for moved in self.board.moved_pieces:
                            if np.array_equal(moved, self.axial_clicked[0]):
                                found = True
                                break
                        if found:
                            continue
                        if (np.array_equal(self.valid_moves, None)) and axial_player == self.board.player:
                            self.clicked_hex = self.axial_clicked
                            self.axial_moves = self.board.get_valid_moves(self.board[self.clicked_hex][0])
                            self.move_or_attack = 1
                            self.step = 2

                    # Moving the selected piece to a valid coordinate.
                    elif self.step == 2:
                        if (not np.array_equal(self.board[self.axial_clicked], []) and 
                        self.board[self.axial_clicked][0] in self.board[self.valid_moves]):
                            if np.array_equal(self.selected_movement_directions, []):
                                dirs = []
                                for axial in self.axial_moves:
                                    if np.array_equal(self.axial_clicked[0], axial[0:2]):
                                        dirs.append(np.where(DIRECTIONS == axial[3])[0][0])                                    
                                self.select_direction = CyclicInteger(0, 0, len(dirs) - 1)
                                self.selected_movement_directions = np.sort(dirs)
                                self.temp_axial = self.axial_clicked
                                self.step = 3
                                continue
                        else:
                            self.clicked_hex = None
                            self.axial_moves = None
                            self.valid_moves = None
                            self.axial_clicked = None
                            self.temp_axial = None
                            self.selected_movement_directions = []
                            self.step = 1

                    # Choosing a valid direction for the piece at the new coordinates.
                    elif self.step == 3:
                        if (not np.array_equal(self.board[self.axial_clicked], []) and 
                        self.board[self.axial_clicked][0] in self.board[self.valid_moves]):
                            new_dir = DIRECTIONS[self.selected_movement_directions[self.select_direction.value]]
                            self.board.move_piece(self.clicked_hex[0], self.temp_axial[0], new_dir)
                        self.clicked_hex = None
                        self.axial_moves = None
                        self.valid_moves = None
                        self.axial_clicked = None
                        self.temp_axial = None
                        self.selected_movement_directions = []
                        self.step = 1
                
                if event.button == 3: # Right click (Attack)
                    if not np.array_equal(axial_player, []):
                        axial_player = self.board[self.axial_clicked][0].piece.player
                    else:
                        pass

                    found = False
                    for fired in self.board.fired_pieces:
                        if np.array_equal(fired, self.axial_clicked[0]):
                            found = True
                            break
                    if found:
                        continue

                    if (np.array_equal(self.valid_moves, None)) and axial_player == self.board.player:
                        self.clicked_hex = self.axial_clicked
                        self.axial_moves = self.board.get_valid_attacks(self.board[self.clicked_hex][0])
                        self.move_or_attack = 2

                    if not np.array_equal(self.clicked_hex, None) and not np.array_equal(self.valid_moves, None):
                        if (not np.array_equal(self.board[self.axial_clicked], [] and 
                        self.board[self.axial_clicked][0] in self.board[self.valid_moves])):
                            self.board.attack_piece(self.clicked_hex[0], self.axial_clicked[0])
                        self.clicked_hex = None
                        self.axial_moves = None
                        self.valid_moves = None
                        self.axial_clicked = None

            if event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 4:
                    if keys[pg.K_LCTRL]: #Scroll up
                        self.hex_radius += 1
                        self.regenerate_size_objects()
                    else:
                        self.select_direction.increment()
                if event.button == 5:
                    if keys[pg.K_LCTRL]: #scroll down
                        self.hex_radius -= 1
                        if self.hex_radius < 1:
                            self.hex_radius = 1
                        self.regenerate_size_objects()
                    else:
                        self.select_direction.decrement()

                if self.turn_button.isOver(pos):
                    self.win_state = self.board.end_turn()

            # Alternate direction rotation if the scroll wheel is not working
            if event.type == pg.KEYUP:
                if event.key == pg.K_a:
                    self.select_direction.decrement()
                elif event.key == pg.K_d:
                    self.select_direction.increment()
                elif event.key == pg.K_w:
                        self.hex_radius += 2
                        self.regenerate_size_objects()
                elif event.key == pg.K_s:
                    self.hex_radius -= 2
                    if self.hex_radius < 1:
                        self.hex_radius = 1
                    self.regenerate_size_objects()

            if event.type == pg.MOUSEMOTION:
                if event.buttons == (1, 0, 0) and keys[pg.K_LCTRL]:
                    self.test_center = (self.test_center[0] + rel_pos[0], self.test_center[1] + rel_pos[1])
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
        self.test_surf.fill(COLORS[-1])
        for index in sorted_indexes:
            self.test_surf.blit(hexagons[index].image, (hex_positions[index] + self.test_center).astype(np.int32))
            if TESTING:
                v_coords = hexagons[index].get_axial_coords()[0]
                c_text = self.test_font.render(str(v_coords[0]) +"," + str(v_coords[1]), True, (255, 255, 255))
                c_width = self.test_font.size(str(v_coords[0]) +"," + str(v_coords[1]))[0]
                self.test_surf.blit(c_text, (hexagons[index].get_position() + self.test_center - c_width / 2).astype(np.int32))
        #self.test_surf.fill(COLORS[-1])

        # Draw pieces that have already moved.
        if not np.array_equal(self.board.moved_pieces, []):
            moved_hexes = self.hex_map[np.array(self.board.moved_pieces)]
            list(map(self.draw_moved, moved_hexes))

        # Draw pieces that have already attacked.
        if not np.array_equal(self.board.fired_pieces, []):
            attacked_hexes = self.hex_map[np.array(self.board.fired_pieces)]
            list(map(self.draw_attack, attacked_hexes))

        # Draw pieces
        for piece in self.board.values():
            w = piece.piece.p_type
            if w != 0:
                # This index is used to find the two angles for the directional triangle.
                index = np.where(DIRECTIONS == piece.piece.direction)[0][0]
                # Find the radian angles of the direction, and scale to the hex radius
                angles_in_radians = np.deg2rad([60 * i + 30 for i in range(index, index + 2)])
                x = self.hex_radius * np.cos(angles_in_radians)
                y = self.hex_radius * np.sin(angles_in_radians)

                # Merge all points to a single array of a triangle
                points = np.round(np.vstack([x, y]).T)
                points = np.round(np.vstack([points, [0, 0]]))
                
                # Find pixel coordinates for the triangle, then find the middle point of the far edge, and draw the line.
                coords = (points + hx.axial_to_pixel(piece.get_axial_coords(), self.hex_radius))
                start_point = coords[2] + self.test_center
                end_point = (coords[0] + coords[1]) / 2 + self.test_center
                pg.draw.line(self.test_surf, [230, 230, 0], start_point.astype(np.int32), end_point.astype(np.int32), 3)
                
                # Draw piece
                text = self.font.render(str(w), False, COLORS[piece.piece.player])
                #text.set_alpha(160)
                pos = hx.axial_to_pixel(piece.get_axial_coords(), self.hex_radius)
                text_pos = pos + self.test_center
                text_pos -= (text.get_width() / 2, text.get_height() / 2)
                self.test_surf.blit(text, text_pos.astype(np.int32))

        # Draw valid moves if a piece is clicked
        if not np.array_equal(self.clicked_hex, None):

            # Get the valid moves for a piece, and display them.
            axials = np.array([i[0:2] for i in self.axial_moves])
            visual_moves = self.hex_map[axials]

            self.valid_moves = self.axial_moves
            if self.move_or_attack == 1:
                list(map(self.draw_movement, visual_moves))
            elif self.move_or_attack == 2:
                list(map(self.draw_attack, visual_moves))

            if not np.array_equal(self.selected_movement_directions, []):
                index = self.selected_movement_directions[self.select_direction.value]
                angles_in_radians = np.deg2rad([60 * i + 30 for i in range(index, index + 2)])
                x = self.hex_radius * np.cos(angles_in_radians)
                y = self.hex_radius * np.sin(angles_in_radians)

                # Merge all points to a single array of a triangle
                points = np.round(np.vstack([x, y]).T)
                points = np.round(np.vstack([points, [0, 0]]))

                # Find pixel coordinates, and draw the triangle.
                coords = (points.astype(np.int32) + hx.axial_to_pixel(self.temp_axial[0][0:2], self.hex_radius)).astype(np.int32)
                pg.draw.polygon(self.test_surf, COLORS[1], coords + self.test_center, 0)

        # Draw health bars
        for piece in self.board.values():
            w = piece.piece.p_type
            if w != 0:
                mh = piece.get_piece().max_health
                ch = piece.get_piece().health
                
                health_string = str(ch) + "/" + str(mh)
                health_text = self.health_font.render(health_string , True, (50, 50, 50))

                piece_pixel_coords = hx.axial_to_pixel(piece.get_axial_coords(), self.hex_radius)
                piece_centered_coords = piece_pixel_coords + self.test_center
                piece_centered_coords -= (health_text.get_width() / 2, 1.4 * health_text.get_height())
                piece_centered_coords = (int(piece_centered_coords[0]), int(piece_centered_coords[1]))

                self.test_surf.blit(health_text, piece_centered_coords)

        # Display current FPS
        fps_text = self.fps_font.render(" FPS: " + str(int(self.clock.get_fps())), True, (50, 50, 50))
        player_text = self.player_font.render(" Player " + str(self.board.player) + " turn", True, COLORS[self.board.player])
        self.main_surf.blit(fps_text, (5, 0))
        
        # Display current player's turn
        player_width = self.player_font.size(" Player " + str(self.board.player) + " turn")[0]
        self.main_surf.blit(player_text, (int(self.center[0] - player_width / 2), int(20 * scale)))
        self.turn_button.draw(self.main_surf, (0, 0, 0))
        
        self.main_surf.blit(self.test_surf, (0, int(100 * scale)))
        # Update window and keep background  
        pg.display.update()
        self.main_surf.fill(COLORS[-1])
        self.clock.tick(60)

    def draw_movement(self, hexagon):
        self.test_surf.blit(self.movement_hex_image, hexagon.get_draw_position().astype(np.int32) + self.test_center)

    def draw_attack(self, hexagon):
        self.test_surf.blit(self.attack_hex_image, hexagon.get_draw_position().astype(np.int32) + self.test_center)

    def draw_moved(self, hexagon):
        self.test_surf.blit(self.moved_hex_image, hexagon.get_draw_position().astype(np.int32) + self.test_center)

    def quit_app(self):
        pg.quit()

if __name__ == '__main__':

    root = Tk()
    root.withdraw()
    dirname = filedialog.askopenfilename(initialdir = "settings/", title = "Select config file to use")
    root.destroy()
    visual_hex_map = VisualHexMap(dirname)

    while visual_hex_map.main_loop():
        visual_hex_map.draw()

    visual_hex_map.quit_app()
    input("Press enter to close...")
    raise SystemExit
