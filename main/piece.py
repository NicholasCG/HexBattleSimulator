import hexy as hx

class PieceTemplate(hx.HexTile):
    '''
    Interntal class to hold basic information
    about piece types. Generated when importing
    from settings file.
    '''
    def __init__(self, health, movement_d, attack_d, power):
        self.health = health
        self.movement_d = movement_d
        self.attack_d = attack_d
        self.power = power

EmptyTemplate = PieceTemplate(0, 0, 0, 0)

class Piece:
    '''
    Holds information about a piece on the board.
    Stores coordinates, piece type, owner, and 
    the PlayerTemplate it is based on.
    '''
    def __init__ (self, p_type, player, direction, template = EmptyTemplate):
        self.p_type = p_type
        self.player = player
        self.max_health = template.health
        self.health = template.health
        self.movement_d = template.movement_d
        self.attack_d = template.attack_d
        self.power = template.power
        self.direction = direction
        self.template = template

EmptyPiece = Piece(0, 0, "", EmptyTemplate)
