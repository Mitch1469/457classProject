"""Provides static variables and methods"""

# Ship names and lengths for access in placement and verification
ships = {
    "Carrier": 1,
    "Battleship": 1,
    "cruiser": 1,
    "Submarine": 1,
    "Destroyer": 1
}

# Creates a empty board object
def create_empty_board():
    return [["~" for _ in range(10)] for _ in range(10)]

# Prints a more legitable board
def print_board(board):
    columns = "   0 1 2 3 4 5 6 7 8 9"
    print(columns)
    for i, row in enumerate(board):
        row_num = f"{i:<2}"
        print(row_num + " " + " ".join(row))

# Determines if ship placement is valid
def validity_checker(board, column, row, direction, length):
    if not isinstance(column, int) or not isinstance(row, int) or not isinstance(length, int):
        return False

    # Check if starting position is within bounds
    if column < 0 or column >= 10 or row < 0 or row >= 10:
        return False

    # Check if ship placement stays within bounds
    if direction == "v" and row + length > len(board):
        return False
    if direction == "h" and column + length > len(board[0]):
        return False

    # Check for overlapping ships
    if direction == "v":
        for r in range(row, row + length):
            if board[r][column] != "~":  # Assuming '~' represents water (empty cell)
                return False
    elif direction == "h":
        for c in range(column, column + length):
            if board[row][c] != "~":
                return False

    return True

# Places the ship on a board object during setup after verification
def placement(board, column, row, length, direction, piece_name):
    "row and board are used as a staring point, direction determines what direction from that point. Length identifies how far to place"
    if direction == "v":
        for i in range(length):
            board[row + i][column] = piece_name[0]
    if direction == "h":
        for i in range(length):
            board[row][column + i] = piece_name[0]
    return board

# guess checker verifies that the guess is within board range, and has not already been guessed
def guess_checker(board_guess, guess_column, guess_row):
    if guess_column < 0 or guess_column > 9 or guess_row < 0 or guess_row > 9: # Checks for values between 0 and 9
        print("Guess outside board range\n")
        return False
    
    s_check = board_guess[guess_row][guess_column]
    if(s_check != "~"): # Checks if coordinates have either X or O, indicating a previous guess
        print("Coordinates Already Guessed")
        return False
    return True

def is_ship_sunk(board, symbol): # Used to check board for unique ship symbol
    for row in board: # Checks all 2d values for unique symbol
        if symbol in row:  
            return False # returns a false if symbol is found
    return True

def are_all_ships_sunk(board): # Checks for any ship symbols to determine if the game is over
    for row in board:
        for cell in row:
            if cell not in ["~", "X"]:  # if there are any ship symbols the game continues
                return False
    return True

def ship_symb(symbol): # Translates ship symbols to names
    if symbol == "C":
        return "Carrier"
    if symbol == "B":
        return "Battleship"
    if symbol == "c":
        return "Cruiser"
    if symbol == "S":
        return "Submarine"
    if symbol == "D":
        return "Destroyer"
    return None

def checker(board, guess_column, guess_row): # Used to determine if the other playes guess is a hit or a miss
    a_check = board[guess_row][guess_column] # Guess Coordinates
    message = "" # Contains miss/hit info and additional identifying information
    is_over = False # bool value from are_all_ships_sunk method, False means the game continues
    
    if a_check != "~" and a_check != "X":  # Checks if guess coordinates contains a unique ship symbol, indicating a hit
        board[guess_row][guess_column] = "X" # Replaces uniqu symbol with a hit marker
        message = "Hit!\n"
        if is_ship_sunk(board, a_check): # checks if there are ships remaining
            ship = ship_symb(a_check)
            if ship:
                message += f"{ship} has been Sunk!\n"
            
            if are_all_ships_sunk(board):
                message += "All Ships have been sunk!"
                is_over = True
    else:
        message = "Miss!"  

    print(message) # hit/miss
    print_board(board) # board with ship status    
    return board, message, is_over

def add_to_guess_board(board_guess, guess_column, guess_row, answer): # adds hit/miss markers to guess_board
    mark = None
    if(answer[0] == "H"):
        mark = "X"
    else:
        mark = "O"
    board_guess[guess_row][guess_column] = mark
    return board_guess    

