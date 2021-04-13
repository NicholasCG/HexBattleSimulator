from datetime import datetime
import numpy as np

def init_log(game):
    day = datetime.now()
    location = "logs/" + day.strftime("%d_%m_%Y-%H_%M_%S") + ".txt"
    file = open(location, "x")
    
    for x in range(1, len(game.templates)):
        template = game.templates[x]
        info_list = [str(template.health), str(template.movement_d), str(template.attack_d), str(template.power)]
        info = " ".join(info_list) + "\n"
        file.write(info)
    file.write("-\n")

    for ignore, tile in game.items():
        file.write(str(tile.axial_coordinates[0]) + " " + str(tile.axial_coordinates[1]) + " ")
    file.write("\n-\n")
    file.close()

    return location

def parse_turn(game, file):
    f = open(file, "a")
    for ignore, tile in game.items():
        if tile.piece.player == 1:
            info_list = [str(tile.piece.player), 
                        str(tile.piece.p_type), 
                        str(tile.axial_coordinates[0]), 
                        str(tile.axial_coordinates[1]), 
                        str(tile.piece.direction), 
                        str(tile.piece.health)]
            f.write(" ".join(info_list) + "\n")

    for ignore, tile in game.items():
        if tile.piece.player == 2:
            info_list = [str(tile.piece.player), 
                        str(tile.piece.p_type), 
                        str(tile.axial_coordinates[0]), 
                        str(tile.axial_coordinates[1]), 
                        str(tile.piece.direction), 
                        str(tile.piece.health)]
            f.write(" ".join(info_list) + "\n")

    f.write("-\n")
    f.close()