import numpy as np
import hexy as hx
from piece import Piece, PieceTemplate, EmptyTemplate, EmptyPiece
import yaml
from queue import Queue
from os import path

SE = np.array((0, -1, 1))
SW = np.array((-1, 0, 1))
W = np.array((-1, 1, 0))
NW = np.array((0, 1, -1))
NE = np.array((1, 0, -1))
E = np.array((1, -1, 0))

def v2_angle(vector1, vector2):
    '''
    Finds the angle between two direction vectors, and then
    returns the 'depth cost' of the angle between the two vectors.
    The function assumes the vectors being worked with
    are the directional vectors defined in the hexy library.
    :param vector1: first direction vector.
    :param vector2: second direction vector.
    '''
    val = (np.dot(vector1, vector2)) / 2

    if val == 1.0:
        return 1
    elif val == 0.5:
        return 2
    elif val == -0.5:
        return 3
    elif val == -1.0:
        return 4
    else:
        print("something's wrong")
        print(vector1, vector2)
        return int(0.954929658551372 * np.arccos(val))

class GameHex(hx.HexTile):
    '''
    Class that holds information about a hexagon
    at specific axial coordinates. Holds information
    on its coordinates and what piece is on the tile.
    '''
    def __init__ (self, axial_coordinates, piece = 0, player = 0, piece_template = EmptyTemplate):
        self.axial_coordinates = axial_coordinates
        self.piece = Piece(piece, player, piece_template)

    def get_axial_coords(self):
        return self.axial_coordinates

    def get_piece(self):
        return self.piece

    def set_piece(self, piece, player, piece_template):
        self.piece = Piece(piece, player, piece_template)

class GameBoard(hx.HexMap):
    '''
    Main game class. Stores the entire game board,
    and allows for players to move their pieces to
    other areas of the board, see what available
    moves they have, and attack other players' pieces.
    '''
    def __init__ (self, file_name):

        self.player = 1
        self.templates = [EmptyTemplate]
        self.moved_pieces =[]
        self.player1_pieces = 0
        self.player2_pieces = 0

        if (not path.exists('settings/default_settings.yaml')):
            print("This program cannot run if default_settings.yaml is missing.")
            raise SystemExit

        try:
            file = open(file_name)
            test_list = yaml.safe_load(file)
        except:
            if file_name == ():
                print("No file selected, defaulting to default_settings.yaml...")
            else:
                print("The selected file is in an invalid format, using default_settings.yaml...")
            try:
                file = open('settings/default_settings.yaml')
                test_list = yaml.safe_load(file)
            except:
                print("This program cannot run if default_settings.yaml is missing or is in an invalid format.")
                raise SystemExit

        # Create piece templates
        for piece, info in test_list['pieces'].items():
            self.templates.append(PieceTemplate(info['health'], 
                                                info['distance'], 
                                                info['attack']))

        # Import board from settings
        self.axial_coords = np.array([np.array(i) for i in test_list['board']])

        self.game_hexes = []

        for a in self.axial_coords:
            self.game_hexes.append(GameHex(a))

        self.game_hexes = np.array(self.game_hexes)

        # Set player 1 pieces on the board.
        for piece, piece_info in test_list['player1'].items():
            index = 0
            self.player1_pieces += 1
            for a in self.axial_coords:
                if np.array_equal(piece_info[1], a):
                    self.game_hexes[index].piece = Piece(p_type = piece_info[0],
                                                    player = 1,
                                                    direction = piece_info[2],
                                                    template = self.templates[piece_info[0]])
                index += 1

        # Set player 2 pieces on the board.
        for piece, piece_info in test_list['player2'].items():
            index = 0
            self.player2_pieces += 1
            for a in self.axial_coords:
                if np.array_equal(piece_info[1], a):
                    self.game_hexes[index].piece = Piece(p_type = piece_info[0],
                                                    player = 2,
                                                    direction = piece_info[2],
                                                    template = self.templates[piece_info[0]])
                index += 1

        hx.HexMap.__setitem__(self, self.axial_coords, self.game_hexes)

    def move_piece(self, old_coords, new_coords):

        # Check to make sure the coordinates are not the same.
        if (np.array_equal(old_coords, new_coords) 
        or any(np.array_equal(cd, old_coords) for cd in self.moved_pieces) 
        or any(np.array_equal(cd, new_coords) for cd in self.moved_pieces)):
            return
        
        # Get the old piece, and create a new piece with 
        old_piece = self[old_coords][0]
        original_at_new = self[new_coords][0]

        # Check if the piece to be moved is owned by the current player
        if old_piece.piece.player != self.player:
            return

        # Check if the piece's new location is owned by the same player
        if old_piece.piece.player == original_at_new.piece.player:
            return

        valid_moves = self.get_valid_moves(old_piece)
        valid_moves_axials = np.array([i[0:2] for i in valid_moves])
        # Check if the new coordinate is in the range of valid moves
        valid_selection = False

        for move in valid_moves_axials:
            if np.array_equal(new_coords, move):
                valid_selection = True

        if not valid_selection:
            return

        # Check if the piece is the enemy piece. This works
        # because we already checked if the piece at new_coords,
        # is owned by the same player. If the piece at new_coords is
        # not empty as well, then it has to be the enemy's.
        if original_at_new.piece.player != 0:
            index = 0
            for move in valid_moves_axials:
                if np.array_equal(move, new_coords):
                    break
                index += 1

            # Subtract health from the enemy piece.
            # Damage = max attack power divided by 1 plus the natural log of the moves's distance.
            # This is then multiplied by a random value, and then floored to preserve integer value.
            damage = np.floor(old_piece.piece.attack / (1 + np.log(valid_moves[index][2])) * max(0, np.random.normal(1, 0.2)))
            original_at_new.piece.health -= damage
            if original_at_new.piece.health > 0:
                self.moved_pieces.append(old_coords)
                return
            
        # Place the piece at the old coordinates to the new coordinates, and
        # change the piece at the old coordinates to the empty piece.

        if original_at_new.piece.player == 1:
            self.player1_pieces -= 1
        elif original_at_new.piece.player == 2:
            self.player2_pieces -= 1

        self[new_coords][0].piece = self[old_coords][0].piece
        self[old_coords][0].piece = EmptyPiece

        self.moved_pieces.append(new_coords)

    # Partially implemented directional movement.
    # TODO: Check for all directions in a hex, then if that direction
    # is reachable, check if the neighbor can be reached.
    def get_valid_moves(self, hex):
        center = hex.get_axial_coords()
        center_direction = eval(hex.piece.direction)
        center_start = np.array([center[0], center[1], 0])
        w = center_start.tostring()
        moves = np.array([center_start])
        
        frontier = Queue()
        frontier.put(w)

        Directions = np.array(["NW", "NE", "SE", "SW", "E", "W"])

        # for i in Directions:
        #     print("the " + i + " neightbor of 0 0 is ", hx.cube_to_axial(hx.get_neighbor([[0, 0, 0]], eval("hx." + i))))
        while not frontier.empty():
            current = np.fromstring(frontier.get(), dtype=np.int64)
            
            if current[2] > hex.piece.distance:
                continue

            cube_current = hx.axial_to_cube(np.array([current[0:2]]))
            neighbors = np.array([hx.get_neighbor(cube_current, hx.NW),
                                hx.get_neighbor(cube_current, hx.NE),
                                hx.get_neighbor(cube_current, hx.SE),
                                hx.get_neighbor(cube_current, hx.SW),
                                hx.get_neighbor(cube_current, hx.E),
                                hx.get_neighbor(cube_current, hx.W)
                                ])

            index = 0
            for next_nb in neighbors:
                direction_cube = eval("hx." + Directions[index])
                index += 1
                found = False
                #  or
                #  (self[hx.cube_to_axial(next_nb)][0].piece.player != hex.piece.player and 
                #  self[hx.cube_to_axial(next_nb)][0].piece.player != 0))
                if np.array_equal(self[hx.cube_to_axial(next_nb)], []):
                    continue
                
                for i in moves[::-1]:
                    if np.array_equal(next_nb[0][::2], i[0:2]):
                        found = True
                        break

                if found:
                    continue
                else:
                    if current[2] + v2_angle(center_direction, direction_cube) <= hex.piece.distance:
                        new_move = np.array([next_nb[0][0], next_nb[0][2], current[2] + v2_angle(center_direction, direction_cube)])
                        moves = np.vstack([moves, new_move])
                        w = new_move.tostring()
                        frontier.put(w)
        return moves

    def end_turn(self):
        self.moved_pieces = []

        if self.player == 1:
            self.player = 2
        elif self.player == 2:
            self.player = 1

        if self.player1_pieces == 0:
            return 2
        elif self.player2_pieces == 0:
            return 1
        else:
            return 0
            
