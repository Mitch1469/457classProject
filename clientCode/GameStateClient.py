import gameStatics
import clientlib
import threading
import socket

"""Contains GameSession class and GameStateClient classes. 
    GameSession is used to track all variables used throughout the program
    GameStateClient is used for the initial piece placement on the board
    """

class GameSession:
    def __init__(self, s_conn, logger): # Object creation for all program variables
        self.conn = s_conn
        self.gameState = None # Has circular refrence with board objects created from gamestatics and stored in GameStateClient
        self.stop_event = threading.Event() # Event flag to terminate threads
        self.flag = None
        self.restart_flag = False
        self.logger = logger

        # Declaring variables and creation of signal socket
        self.signal_sock_recv, self.signal_sock_send = socket.socketpair() 
        self.signal_sock_recv.setblocking(False)
        self.signal_sock_send.setblocking(False)
        self.lock = threading.Lock()


    def reset(self):
        # Reset the session for a new game.
        self.gameState = None
        self.stop_event.clear()
        self.flag = None
        self.restart_flag = False

    def set_gameState(self, new_board, gameVar): # Allows for circular refrence
        self.gameState = GameStateClient(new_board, gameVar)

    def set_restart_flag(self):
        # Thread-safe setter for restart_flag
        with self.lock:
            self.restart_flag = True
    def is_restart_flag_set(self):
        # Thread-safe getter for restart_flag
        with self.lock:
            return self.restart_flag

class GameStateClient:
    def __init__(self, board, gameVar):
        self.gameVar = gameVar # Circular refrence
        self.board = board # Board containing the players ship board
        self.guess_board = gameStatics.create_empty_board() # Create a empty board for guess board
        self.gameover = False
    

 
    def place_pieces(self):
        """Method that will be threaded. Places pieces on the players ship board. Threaded as this can 
            take a while and inhibit recieving updates and messages from the server"""
        try:
            print("To place pieces, provide a starting position and direction (h for horizontal, v for vertical).")
            print("Only numbers 0 through 9 are valid for rows and columns.")
            gameStatics.print_board(self.board)

            for ship_name, length in gameStatics.ships.items(): # Iterates through the list containing all the placeable ships
                print(f"\nPlacing {ship_name} (length {length})") # Current ship and associated length
                while not self.gameVar.stop_event.is_set():  # Check stop_event in the loop

                    # Checks for escape options throughout for each selection
                    column = clientlib.inputValidation("Select Column\n", "num", self.gameVar.conn)
                    row = clientlib.inputValidation("Select Row\n", "num", self.gameVar.conn)
                    direction = input("Select Direction (h or v)\n")

                    #Validity checkers
                    if direction in ("h", "v") and gameStatics.validity_checker(self.board, column, row, direction, length):
                        self.board = gameStatics.placement(self.board, column, row, length, direction, ship_name)
                        break
                    else:
                        print("Invalid placement. Try again.")

                if self.gameVar.stop_event.is_set(): # if event flag is set, the loop ends after the current ship placement iteration
                    print("Other Player Quit.")
                    return

            print("All ships placed!")
            gameStatics.print_board(self.board)
            self.gameVar.stop_event.set()  # Signal that placement is done and sets the event for the listener to stop

        except Exception as e:
            self.gameVar.stop_event.set()
            print(f"An error occurred during placement: {e}")
    