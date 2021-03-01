import numpy as np
import hexy as hx
from random import seed, randint
from datetime import datetime
from piece import Piece, PieceTemplate, EmptyTemplate
from queue import Queue
import yaml

def generate_fixed_board():
    axial_coords = hx.cube_to_axial(hx.get_disk([0, 0, 0], 13))
    game_hexes = []

    for a in axial_coords:
        game_hexes.append(GameHex(a))

    return axial_coords, np.array(game_hexes)

class GameHex(hx.HexTile):
    '''
    Class that holds information about a hexagon
    at specific axial coordinates. Holds information
    on its coordinates and what piece is on the tile.
    '''
    def __init__ (self, axial_coordinates, piece = 0, player = 0, piece_template = EmptyTemplate):
        self.axial_coordinates = axial_coordinates
        self.piece = Piece(axial_coordinates, piece, player, piece_template)

    def get_axial_coords(self):
        return self.axial_coordinates

    def get_piece(self):
        return self.piece

    def set_piece(self, piece, player, piece_template):
        self.piece = Piece(self.axial_coordinates, piece, player, piece_template)

class GameBoard(hx.HexMap):
    '''
    Main game class. Stores the entire game board,
    and allows for players to move their pieces to
    other areas of the board, see what available
    moves they have, and attack other players' pieces.
    '''
    def __init__ (self):
        seed(datetime.now())

        self.player = 1
        self.templates = [EmptyTemplate]
        self.moved_pieces =[]

        with open('settings/settings.yaml') as file:
            test_list = yaml.safe_load(file)
            for piece, info in test_list['pieces'].items():
                self.templates.append(PieceTemplate(info['health'], 
                                                    info['distance'], 
                                                    info['attack']))
        self.axial_coords, self.game_hexes = generate_fixed_board()

        rands = []
        gh_len = len(self.game_hexes)
        tem_len = len(self.templates) - 1
        for i in range(tem_len * 2):
            val = randint(0, gh_len - 1)
            while val in rands:
                val = randint(0, gh_len - 1)
            rands.append(val)

        for i in range(2):
            for p in range(tem_len):
                self.game_hexes[rands[tem_len * i + p]].set_piece(piece = p + 1, 
                                                                player = i + 1, 
                                                                piece_template = self.templates[p + 1])

        hx.HexMap.__setitem__(self, self.axial_coords, self.game_hexes)

    def get_board(self):
        return hx.HexMap.__getitem__(self, self.axial_coords)

    def move_piece(self, old_coords, new_coords):

        # Check to make sure the coordinates are not the same.
        if (np.array_equal(old_coords, new_coords) 
        or any(np.array_equal(cd, old_coords) for cd in self.moved_pieces) 
        or any(np.array_equal(cd, new_coords) for cd in self.moved_pieces)):
            return
        
        # Get the old piece, and create a new piece with 
        old_piece = hx.HexMap.__getitem__(self, old_coords)[0]
        old_piece_check = hx.HexMap.__getitem__(self, new_coords)[0]

        # Check if the piece to be moved is owned by the current player
        if old_piece.get_piece().get_player() != self.player:
            return

        # Check if the piece's new location is owned by the same player
        if old_piece.get_piece().get_player() == old_piece_check.get_piece().get_player():
            return

        valid_moves = self.get_valid_moves(old_piece)
        valid_moves_axials = np.array([i[0] for i in valid_moves])

        # Check if the new coordinate is in the range of valid moves
        if (not new_coords in valid_moves_axials):
            return

        # Check if the piece is the enemy piece. This works
        # because we already checked if the piece at new_coords,
        # is owned by the same player. If the piece at new_coords is
        # not empty as well, then it has to be the enemy's.
        if old_piece_check.get_piece().get_player() != 0:
            index = 0
            for move in valid_moves_axials:
                if np.array_equal(move, new_coords):
                    break
                index += 1

            # Subtract health from the enemy piece. If the health is still
            # above 0, don't move the piece.
            damage = valid_moves[index][1]
            old_piece_check.get_piece().health -= damage
            if old_piece_check.get_piece().health > 0:
                hx.HexMap.__delitem__(self, new_coords)
                hx.HexMap.__setitem__(self, [new_coords], [old_piece_check])
                self.moved_pieces.append(old_coords)
                return
            
        # Create new game hexes at the coordinates, delete the old GameHexes
        # at the coordinates, and replace with the new coordinates.
        piece = GameHex(new_coords, piece = old_piece.get_piece().get_piece_type(), 
                                    player = old_piece.get_piece().get_player(),
                                    piece_template = old_piece.get_piece().get_template())
        empty = GameHex(old_coords)

        coords = np.array([old_coords, new_coords])
        pieces = np.array([empty, piece])

        hx.HexMap.__delitem__(self, coords)
        hx.HexMap.__setitem__(self, coords, pieces)

        self.moved_pieces.append(new_coords)

    def get_valid_moves(self, hex):

        # Get the maximum radius for movement and 
        # attack power for closest attack
        radius = hex.get_piece().get_distance()
        attack = hex.get_piece().get_attack()
        center = hx.axial_to_cube(np.array([hex.get_axial_coords()]))

        move = np.array([[hex.get_axial_coords(), 0]], dtype=object)

        # Create array of possible moves and the matching attack power.
        # The farther out the move is from the center, the weaker the attack.
        for i in range(0, radius):
            ring = hx.get_ring(center, i + 1)
            damage = attack - i
            if damage < 0:
                damage = 0

            new_moves = np.array([[hx.cube_to_axial(np.array([c]))[0].astype(np.int), damage] for c in ring], dtype=object)
            for i in new_moves:
                move = np.vstack([move, i])

        return move

    def end_turn(self):
        self.moved_pieces = []

        if self.player == 1:
            self.player = 2
        elif self.player == 2:
            self.player = 1
        
