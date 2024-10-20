ships = {
    "carrier": 5,
    "battleship": 4,
    "cruiser": 3,
    "submarine": 3,
    "destroyer": 2
}

def create_empty_board():
    """Creates an empty 10x10 board."""
    return [["." for _ in range(10)] for _ in range(10)]

def print_board(board):
    """Prints the board in a readable format."""
    columns = "  A B C D E F G H I J"
    print(columns)
    for i, row in enumerate(board):
        row_num = f"{i+1:<2}"
        print(row_num + " " + " ".join(row))