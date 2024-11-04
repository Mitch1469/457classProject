import selectors
import json
import time

def create_empty_board():
        return [["." for _ in range(10)] for _ in range(10)]

class GameState:
    def __init__(self, gameboard1, gameboard2):
        self.gameboard1 = gameboard1
        self.gameboardguess1 = create_empty_board()
        self.gameboard2 = gameboard2
        self.gameboardguess2 = create_empty_board()
        self.move = ""

    
    
