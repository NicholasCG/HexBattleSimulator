import hexy as hx

class PieceTemplate(hx.HexTile):
    '''
    Interntal class to hold basic information
    about piece types. Generated when importing
    from settings file.
    '''
    def __init__(self, health, distance, attack):
        self.health = health
        self.distance = distance
        self.attack = attack

EmptyTemplate = PieceTemplate(0, 0, 0)

class Piece:
    EMPTY = 0
    INFANTRY = 1
    DEFENSE = 2
    SPEED = 3 

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
        self.distance = template.distance
        self.attack = template.attack
        self.direction = direction
        self.template = template

EmptyPiece = Piece(0, 0, "", EmptyTemplate)
