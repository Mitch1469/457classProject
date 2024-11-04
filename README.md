# Battleship Game

This is a simple Tic-Tac-Toe game implemented using Python and sockets.

**Updates**
Game functionality included. Initial board generation, placing of pieces, guess board showing previous hits misses, code for exchanging guess and identification of players ships and what has been hit.

Turn loop included for the server that allows for players to take turns and exchange information

Conditions set for premature ending of game, and for when a game finishes

Chat function has been disabled due to issues with game implementation. 

**How to play:**
1. **Start the server:** Run the `server.py` with the ip and port wanted for the server script.
2. **Connect clients:**  Run the `client.py` script on two different machines or terminals with the ip and port of the       server
3. **Play the game:** Players take turns entering their moves, after setting their pieces. 

**Technologies used:**
* Python
* Sockets
* Threading

**Message Protocols**
* chat
  Used to pass non-game or server option messages between clients 
* command
  * quit
    Quits the game, closes connections, sends other player message telling the game has ended and removes game from acti    ve games
  * current_games 
    Lists number of active games and the player names of each game
  * partner_connections
    Lists socket information of both clients in the asking clients game
  * gameplay
    will tell the server of the update board, guess for ship location and other game specific information
  * game_init 
    The servers sends a game_init message to tell the clients to start a new board and have the players set there pieces  

**Files Included**
* server.py       -- Acts the middle man between two clients. Takes requests and processes the game.
* serverlib.py    -- Contains methods for use by server.py and gamesetup.py
* gamesetup.py    -- Contains the script for the game
* client.py       -- Contains the main script for sending and receiving information from the sever and displaying it for*                    the user
* clientlib       -- Contains the methods for client.py to run
* clientGameState -- ** REMOVED ** placing, validation and guessing placed in client code
* gameStatics     -- Contains statics such as game rules and piece information and the checking for valid placements and*                    moves
* GameStateClient -- Contains the code for setting peices on the board for the clients

**Additional resources:**
* [Link to Python documentation]
* [Link to sockets tutorial]
    
