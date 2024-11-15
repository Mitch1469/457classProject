import gameStatics



class GameStateClient:
    def __init__(self, board):
        self.board = board
        self.guess_board = gameStatics.create_empty_board()
        self.gameover = False
    

    def place_pieces(self):
        print("To place peices give starting position then select direction, i.e. horizontal(h) or vertical(v)")
        gameStatics.print_board(self.board)
        print("\nCarrier is 5")
        while(True):
            carrierColumn = int(input("Select Column\n"))
            carrierRow = int(input("Select Row\n"))
            while(True):
                carrierDirection = input("Select Direction\n")
                if carrierDirection == "v" or carrierDirection == "h":
                    break
            if gameStatics.validity_checker(self.board, carrierColumn, carrierRow, carrierDirection, 5) == True:
                self.board = gameStatics.placement(self.board, carrierColumn, carrierRow, 5, carrierDirection, "Carrier")
                break

        gameStatics.print_board(self.board)
        print("\nBattleship is 4\n")
        while(True):
            battleshipColumn = int(input("Select Column\n"))
            battleshipRow = int(input("Select Row\n"))
            while(True):
                battleshipDirection = input("Select Direction\n")
                if battleshipDirection == "v" or battleshipDirection == "h":
                    break
            if gameStatics.validity_checker(self.board, battleshipColumn, battleshipRow, battleshipDirection, 4) == True:
                self.board = gameStatics.placement(self.board, battleshipColumn, battleshipRow, 4, battleshipDirection, "Battleship")
                break
        
        gameStatics.print_board(self.board)
        print("\nCruiser is 3\n")
        while(True):
            cruiserColumn = int(input("Select Column\n"))
            cruiserRow = int(input("Select Row\n"))
            while(True):
                cruiserDirection = input("Select Direction\n")
                if cruiserDirection == "v" or cruiserDirection == "h":
                    break
            if gameStatics.validity_checker(self.board, cruiserColumn, cruiserRow, cruiserDirection, 3) == True:
                self.board = gameStatics.placement(self.board, cruiserColumn, cruiserRow, 3, cruiserDirection, "cruiser")
                break
        
        gameStatics.print_board(self.board)
        print("\nSubmarine is 3\n")
        while(True):
            subColumn = int(input("Select Column\n"))
            subRow = int(input("Select Row\n"))
            while(True):
                subDirection = input("Select Direction\n")
                if subDirection == "v" or subDirection == "h":
                    break
            if gameStatics.validity_checker(self.board, subColumn, subRow, subDirection, 3) == True:
                self.board = gameStatics.placement(self.board, subColumn, subRow, 3, subDirection, "Sub")
                break
        gameStatics.print_board(self.board)
        print("\nDestroyer is 2\n")
        while(True):
            destColumn = int(input("Select Column\n"))
            destRow = int(input("Select Row\n"))
            while(True):
                destDirection = input("Select Direction\n")
                if destDirection == "v" or destDirection == "h":
                    break
            if gameStatics.validity_checker(self.board, destColumn, destRow, destDirection, 2) == True:
                self.board = gameStatics.placement(self.board, destColumn, destRow, 2, destDirection, "Dest")
                break

    