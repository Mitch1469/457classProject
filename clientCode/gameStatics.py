ships = {
    "carrier": 5,
    "battleship": 4,
    "cruiser": 3,
    "submarine": 3,
    "destroyer": 2
}

def create_empty_board():
    return [["~" for _ in range(10)] for _ in range(10)]

def print_board(board):
    columns = "   0 1 2 3 4 5 6 7 8 9"
    print(columns)
    for i, row in enumerate(board):
        row_num = f"{i:<2}"
        print(row_num + " " + " ".join(row))

def validity_checker(board, column, row, direction, length):
        if column < 0 or column >= 10 or row < 0 or row >= 10:
            return False      
        if direction == "v":
            if row + length > 10:
                return False

            for i in range(length):
                if board[row + i][column] != "~":
                    return False
        elif direction == "h":
            if column + length > 10:  
                return False
            for i in range(length):
                if board[row][column + i] != "~": 
                    return False
        return True 

def placement(board, column, row, length, direction, piece_name):    
    if direction == "v":
        for i in range(length):
            board[row + i][column] = piece_name[0]
    if direction == "h":
        for i in range(length):
            board[row][column + i] = piece_name[0]
    return board

def guess_checker(board_guess, guess_column, guess_row):
    s_check = board_guess[guess_row][guess_column]
    if guess_column < 0 or guess_column > 9 or guess_row < 0 or guess_row > 9:
        print("Guess outside board range\n")
        return False
    if(s_check != "~"):
        print("Coordinates Already Guessed")
        return False
    return True
def is_ship_sunk(board, symbol):
    """Check if all parts of a specific ship (given by symbol) are hit (i.e., no cells with the ship's symbol remain)."""
    for row in board:
        if symbol in row:  # If any part of the ship still exists, it's not sunk
            return False
    return True

def are_all_ships_sunk(board):
    for row in board:
        for cell in row:
            if cell not in ["~", "X"]:  
                return False
    return True

def ship_symb(symbol):
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

def checker(board, guess_column, guess_row):
    a_check = board[guess_row][guess_column]
    message = ""
    gamestate = False
    
    if a_check != "~" and a_check != "X":  
        board[guess_row][guess_column] = "X"  
        message = "Hit!\n"
        
        if is_ship_sunk(board, a_check):
            ship = ship_symb(a_check)
            if ship:
                message += f"{ship} has been Sunk!\n"
            
            if are_all_ships_sunk(board):
                message += "All Ships have been sunk!"
                gamestate = True
    else:
        message = "Miss!"  
    
    return board, message, gamestate

def add_to_guess_board(board_guess, guess_column, guess_row, answer):
    mark = None
    if(answer[0] == "H"):
        mark = "X"
    else:
        mark = "O"
    board_guess[guess_row][guess_column] = mark
    return board_guess    
