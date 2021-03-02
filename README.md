# Hexagon Battle Simulator

This is a basic hexagon-based strategy game meant to
roughly simulate large-scale combat for analysis purposes.

If there are any issues with the program, please let me know at [mailto](mailto:nicholascgray@knights.ucf.edu).

#### Installation instruction for required packages

```bash
git clone https://github.com/NicholasCG/HexBattleSimulator
cd HexBattleSimulator
pip install -r requirements.txt # If you're not using a virtual environment, you might need to use sudo.
cd main
python3 game_visuals.py
```

#### Initializing a new game

```python
import hex_board as hxgame
hex_game = hxgame.GameBoard() # Initializes a new game board, pulling from settings.yaml,
                              # or default_settings.yaml is settings.yaml is missing.
map = hex_game.get_board()    # Returns a list of GameHex objects, which represents the current game state.
# Various actions after analyzing map...
hex_game.end_turn()           # Ends the current turn.
map = hex_game.get_board()    # Pulls the new game state.
```

#### Game Functions

- `GameBoard()`: Creates a new game, based on the settings from settings.yaml/default_settings.yaml.
- `get_board()`: Returns the current state of the game board.
- `get_valid_moves(hexagon)`: Gives the possible moves for the piece that is current at a tile.
- `move_piece(old_coords, new_coords)`: Moves a piece at `old_coords` to `new_coords`, or attacks the piece at `new_coords`, depending on if the move is valid.
- `end_turn()`: Ends the current turn, resets record of moved pieces, and changes to the next player's turn. If all of a player's pieces are removed from the board, the function returns the winning opponent's number.

### Warning!
Do not alter default_settings.yaml, unless you are sure that the file is still in a valid format.
If settings.yaml is invalid or missing, the program defaults to default_settings.yaml, and will
not run if it is missing or invalid.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
