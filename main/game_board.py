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
    val = (vector1[0] * vector2[0] + vector1[1] * vector2[1] + vector1[2] * vector2[2]) / 2

    if val == 1.0:
        return 0
    elif val == 0.5:
        return 1
    elif val == -0.5:
        return 2
    elif val == -1.0:
        return 3
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
        self.moved_pieces = []
        self.fired_pieces = []
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
                                                info['movement_d'], 
                                                info['attack_d'],
                                                info['power']))

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

        self[self.axial_coords] = self.game_hexes

    def attack_piece(self, attacker, target):
        # Check to make sure the coordinates are not the same.
        if (np.array_equal(attacker, target) 
        or any(np.array_equal(cd, attacker) for cd in self.fired_pieces) 
        or any(np.array_equal(cd, target) for cd in self.fired_pieces)):
            return
        
        # Get the old piece, and create a new piece with 
        attacking_piece = self[attacker][0]
        target_piece = self[target][0]

        # Check if the piece to attack is owned by the current player
        if attacking_piece.piece.player != self.player:
            return

        # Check if the piece's target is owned by the opponent
        elif attacking_piece.piece.player == target_piece.piece.player or target_piece.piece.player == 0:
            return

        valid_moves = self.get_valid_attacks(attacking_piece)
        valid_moves_axials = np.array([i[0:2] for i in valid_moves])
        # Check if the new coordinate is in the range of valid moves
        valid_selection = False

        for move in valid_moves_axials:
            if np.array_equal(target, move):
                valid_selection = True

        if not valid_selection:
            return

        # Check if the piece is the enemy piece. This works
        # because we already checked if the piece at target,
        # is owned by the same player. If the piece at target is
        # not empty as well, then it has to be the enemy's.
        if target_piece.piece.player != 0:
            index = 0
            for move in valid_moves_axials:
                if np.array_equal(move, target):
                    break
                index += 1

            # Subtract health from the enemy piece.
            # Damage = max attack power divided by 1 plus the natural log of the moves's distance.
            # This is then multiplied by a random value, and then floored to preserve integer value.
            damage = np.floor(attacking_piece.piece.power / (1 + np.log(valid_moves[index][2])) * max(0, np.random.normal(1, 0.2)))
            target_piece.piece.health -= int(damage)
            if target_piece.piece.health > 0:
                self.fired_pieces.append(attacker)
                return
            
        # Place the piece at the old coordinates to the new coordinates, and
        # change the piece at the old coordinates to the empty piece.

        if target_piece.piece.player == 1:
            self.player1_pieces -= 1
        elif target_piece.piece.player == 2:
            self.player2_pieces -= 1

        self[target][0].piece = EmptyPiece
        self.fired_pieces.append(attacker)
    
    def move_piece(self, old_coords, new_coords, new_direction):

        # Check to make sure the coordinates are not the same.
        if (np.array_equal(old_coords, new_coords) 
        or any(np.array_equal(cd, old_coords) for cd in self.moved_pieces) 
        or any(np.array_equal(cd, new_coords) for cd in self.moved_pieces)):
            self[old_coords][0].piece.direction = new_direction
            self.moved_pieces.append(new_coords)
            
            return
        
        # Get the piece at the old coordinates and the new coordinates
        old_piece = self[old_coords][0]
        original_piece_at_new = self[new_coords][0]

        # Check if the piece to be moved is owned by the current player
        if old_piece.piece.player != self.player:
            return

        # Check if the piece's new location already has a different piece on it.
        if original_piece_at_new.piece.player != 0:
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

        self[new_coords][0].piece = self[old_coords][0].piece
        self[new_coords][0].piece.direction = new_direction
        self[old_coords][0].piece = EmptyPiece

        self.moved_pieces.append(new_coords)

        # Since we are saving the coordinates of pieces, we need to check if there
        # are any fired coordinates at the old coordinates that need to be moved
        # to the new coordinates
        index = 0
        for piece in self.fired_pieces:
            if np.array_equal(piece, old_coords):
                self.fired_pieces[index] = new_coords
                break
            index += 1

    # Directional breadth first search movement algorithm. Absolutely atrocious runtime.
    def get_valid_moves(self, hex):
        dist = hex.piece.movement_d
        center = hex.get_axial_coords()

        moves = []
        frontier = Queue()

        Directions = np.array(["NW", "NE", "SE", "SW", "E", "W"])

        move = np.array([center[0], center[1], 0, hex.piece.direction], dtype = object)
        frontier.put(move)

        while not frontier.empty():
            current = frontier.get()

            r = current[0]
            q = current[1]
            cost = current[2]
            direction = current[3]

            found = False
            for i in moves[::-1]:
                if np.array_equal(current[0:2], i[0:2]) and current[3] == i[3]:
                    if current[2] < i[2]:
                        del i
                    else:
                        found = True
                        break

            if found:
                continue

            for dir in Directions:
                move_cost = cost + v2_angle(eval(direction), eval(dir))
                if move_cost <= dist:
                    move = np.array([r, q, move_cost, dir], dtype = object)
                    moves.append(move)

                    cube_current = hx.axial_to_cube(np.array([current[0:2]]))
                    neighbor = (cube_current + eval(dir))[0]

                    if move_cost + 1 <= dist:
                        neighbor_move = np.array([neighbor[0], neighbor[2], move_cost + 1, dir], dtype = object)

                        if (np.array_equal(self[neighbor_move[0:2]], []) or self[neighbor_move[0:2]][0].piece.player != 0):
                            continue
                        frontier.put(neighbor_move)

        moves = np.array(moves, dtype=object)
        return moves

    # Breadth first search, but technically implemented incorrectly for directional movement. 
    # However, the shapes formed look quite nice to me as an attack formation.
    def get_valid_attacks(self, hex):
        center = hex.get_axial_coords()
        center_direction = eval(hex.piece.direction)
        center_start = np.array([center[0], center[1], 0])
        moves = np.array([center_start])
        
        frontier = Queue()
        frontier.put(center_start)

        Directions = np.array(["NW", "NE", "SE", "SW", "E", "W"])

        while not frontier.empty():
            current = frontier.get()

            if current[2] > hex.piece.attack_d:
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
                
                if np.array_equal(self[hx.cube_to_axial(next_nb)], []):
                    continue
                
                for i in moves[::-1]:
                    if np.array_equal(next_nb[0][::2], i[0:2]):
                        found = True
                        break

                if found:
                    continue
                else:
                    if current[2] + 1 + v2_angle(center_direction, direction_cube) <= hex.piece.attack_d:
                        new_move = np.array([next_nb[0][0], next_nb[0][2], current[2] + 1 + v2_angle(center_direction, direction_cube)])
                        moves = np.vstack([moves, new_move])
                        frontier.put(new_move)

        return moves

    # Resets temporary variables, changes the current player, and checks to see 
    # if the game has ended.
    def end_turn(self):
        self.moved_pieces = []
        self.fired_pieces = []

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