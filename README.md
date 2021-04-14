# Hexagon Battle Simulator

This is a basic hexagon-based strategy game meant to
roughly simulate combat for analysis purposes.

If there are any issues with the program, please let me know at [nicholascgray@knights.ucf.edu](mailto:nicholascgray@knights.ucf.edu).

## General Information

When running the program, it will ask you to select a configuration file in the settings folder to
use for the simulation. An example configuration file named default_settings.yaml is already in the settings
folder. If no configuration file is selected, or the selected file is invalid, the program will default to
using default_settings.yaml. The main program will then start, with the FPS, current player's turn, an
End Turn button, and the game board displayed. Pieces start with a given direction and template from
the configuration file.

![Alt text](/HSB.png?raw=true "Main Program Screen")

You can zoom the board in and out with the scroll wheel or W/S, and move the board itself around by
holding down left control and the left mouse button and dragging it around. The program ends when
one player runs out of pieces. A log of the game will be created in the logs folder, which records
the piece templates, board, and the pieces at each turn in the game.

### Warning!
Do not alter default_settings.yaml, unless you are sure that the file is still in a valid format. If the selected
configuration file is not valid, the main program defaults to using default_settings.yaml.

## Controls for Main Program

Use the left mouse button to move pieces and use the right mouse button to attack with pieces.

When moving pieces, first click on the piece you would like to move. The available tiles will be
outlined in white. Next, select the tile you would like to move to by left clicking. 
Then use the mouse scroll wheel or the A and D keys to choose a direction, and left click on the tile
to finalize your choice. For a selected piece, you can click on a different tile to change what tile
you would like to move to, or click outside of the valid moves to deselect that piece. Pieces that
have already moved will be placed on gray tiles.

When using a piece to attack, right click on the piece you would like to attack with. The attackable
tiles will be outlined in red. Then, right click on the tile you would like to attack. If you right
click outside of the valid attack tiles, the piece will be deselected. Pieces that have already attacked
will have a red outline around them.

To zoom in and out the board, press left control and use the scroll. Alternatively, you can use the W
and S keys to zoom in and out. To move the board itself, hold down left control and the left mouse button,
and move the board to its desired location. To center and reset the board's zoom, press C.

## Instructions for the Configuration File Creator.

Included with the main program is a configuration file creator, `config_creator.py`. The configuration 
file creator works in three steps: piece template creation, board creation, and piece placement. 

The piece template creation is a terminal interface where you enter the number of templates you wish to
create, and the health, movement distance, attack range, and attack power for each template. 

After creating the piece templates, a new window will appear for creating the game board. 
There are a number of preset board shapes, and a custom map mode. You can change between the map types 
by using your scroll wheel or the A/D keys. To change the size of the preset map, use the left and right
arrow keys. In custom mode, hold down the left mouse button and drag your mouse to add or delete tiles. 
To finalize the map, press enter. The maximum map size for the configuration file creator is shown with
the light blue tiles in the background.

After finalizing the map, the window will change to allow you to place pieces on the board. The possible piece
types you can place are dependent on the piece templates you entered in on the first step. To place pieces
onto the board, left click on the tile you wish to place a piece on. The tile will be outlined in white, and 
you can use your scroll wheel or the A/D keys to choose the direction of the piece. Then, left click on the
tile again to place the piece. To delete a piece, simply click on it and it will be deleted. To change the 
player, use the right mouse button. To change when piece template you are using, use the left and right 
arrow keys. To finalize your piece placement, press enter.

After you finalize your piece placement. The window will close, and you will be asked to save the new configuration
in the settings folder. You can name the file whatever you wish, as you can choose what configuration file to
use in the main program. However, it is not recommended to name it default_settings.yaml, as that is already given
as an example file. 

The configuration files are written in the YAML format, so they can be manually edited in a text editor.

## Installation instructions for required packages and running the program

```bash
git clone https://github.com/NicholasCG/HexBattleSimulator
cd HexBattleSimulator
pip install -r requirements.txt # If you're not using a virtual environment, you might need to use sudo.
cd main
python __main__.py
```

### Game Functions

- `GameBoard()`: Creates a new game, based on the settings from settings.yaml/default_settings.yaml.
- `get_valid_moves(hex)`: Gives the possible moves for the piece that is at the given tile.
- `move_piece(old_coords, new_coords)`: Moves a piece at `old_coords` to `new_coords` if it is an empty tile.
- `get_valid_attacks(hex)`: Gives the tiles in range for a piece at the given tile to attack.
- `attack_piece(attacker, target)`: `Attacker` attacks the piece at `target` if `target` is an enemy piece.
- `end_turn()`: Ends the current turn, resets record of moved pieces, and changes to the next player's turn. If all of a player's pieces are removed from the board, the function returns the winning opponent's number.

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
