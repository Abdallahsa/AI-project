import pygame as p
from Chess import ChessEngine
import chessAI
import sys
from multiprocessing import Process, Queue
import os
import random
from main import *

BOARD_WIDTH = BOARD_HEIGHT = 512
MOVE_LOG_PANEL_WIDTH = 250
MOVE_LOG_PANEL_HEIGHT = BOARD_HEIGHT
DIMENSION = 8
SQUARE_SIZE = BOARD_HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}


def loadImages():
    """
    Initialize a global directory of images.
    """
    pieces = ['wp', 'wR', 'wN', 'wB', 'wK',
              'wQ', 'bp', 'bR', 'bN', 'bB', 'bK', 'bQ']
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("images/" + piece + ".png"), (SQUARE_SIZE, SQUARE_SIZE))
        print(os.getcwd())

def main(dep,algo):
    """
    The main driver for our code.
    This will handle user input and updating the graphics.
    """
    p.init()
    screen = p.display.set_mode(
        (BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))
    clock = p.time.Clock()
    screen.fill(p.Color("white"))
    game_state = ChessEngine.GameState()
    valid_moves = game_state.getValidMoves()
    move_made = False  # flag variable for when a move is made
    animate = False  # flag variable for when we should animate a move
    loadImages()  # do this only once before while loop
    running = True
    # no square is selected initially, this will keep track of the last click of the user (tuple(row,col))
    square_selected = ()
    computer_clicks = []  # this will keep track of player clicks (two tuples)
    game_over = False
    ai_thinking = False
    move_undone = False
    move_finder_process = None
    move_log_font = p.font.SysFont("Arial", 14, False, False)
    player_one = True  # if computer is playing white, then this will be True, else False
    player_two = False  # if computer is playing white, then this will be True, else False

    while running:
        computer_turn = (game_state.white_to_move and player_one) or (
            not game_state.white_to_move and player_two)

        ## apply the event of closing the window
        events = p.event.get()
        if any(event.type == p.QUIT for event in events):
            p.quit()
            sys.exit()
       #check if game is over
        if not game_over:
             if computer_turn and not move_made:  # Check if it's the computer's turn and no move has been made yet
                 valid_moves = game_state.getValidMoves() ## retrieves the list of valid moves for the current game state
                 if len(valid_moves) > 0:
                        # Select a random move from the list of valid moves
                        random_move = random.choice(valid_moves)
                        game_state.makeMove(random_move)
                        move_made = True ## to indicate that a move has been made by the computer.
                        animate = True ##  to enable animation for the move.

        # AI agent that applies the algorithms
        if not game_over and not computer_turn and not move_undone:
            if not ai_thinking:
                ai_thinking = True
                return_queue = Queue()  # used to pass data between threads

                depth = dep  # Specify the desired depth level here
                ##print("THEDEPTH: : : ",depth)
                

############################################################################
                print(algo)                 #   Work with specific algorithm
                if algo == "Alpha Beta":

                    move_finder_process = Process(target = chessAI.findBestMoveAlphaBeta, args=(
                        game_state, valid_moves, return_queue, depth))
                    move_finder_process.start()
                else:
                    move_finder_process = Process(target=chessAI.findBestMoveMiniMax, args=(
                        game_state, valid_moves, return_queue, depth))
                    move_finder_process.start()


##################################################################################
            if not move_finder_process.is_alive():
                ai_move = return_queue.get()
                if ai_move is None:
                    ai_move = chessAI.findRandomMove(valid_moves)  # if I have many best solutions, I select any of them
                game_state.makeMove(ai_move)
                move_made = True
                animate = True
                ai_thinking = False
    #check on moves are done
        if move_made:
            if animate:
                animateMove(game_state.move_log[-1],
                            screen, game_state.board, clock)
            valid_moves = game_state.getValidMoves()
            move_made = False
            animate = False
            move_undone = False

        drawGameState(screen, game_state, valid_moves, square_selected)

        if not game_over:
            drawMoveLog(screen, game_state, move_log_font)

        if game_state.checkmate:
            game_over = True
            if game_state.white_to_move:
                drawEndGameText(screen, "Black wins by checkmate")
            else:
                drawEndGameText(screen, "White wins by checkmate")

        elif game_state.stalemate:
            game_over = True
            drawEndGameText(screen, " Draw by Stalemate")

        clock.tick(MAX_FPS)
        p.display.flip()

      #draw game in screen
def drawGameState(screen, game_state, valid_moves, square_selected):
    """
    Responsible for all the graphics within current game state.
    """
    drawBoard(screen)  # draw squares on the board
    highlightSquares(screen, game_state, valid_moves, square_selected)
    drawPieces(screen, game_state.board)  # draw pieces on top of those squares


def drawBoard(screen):
    """
    Draw the squares in the board.
    The top left square is always light.
    """
    global colors
    colors = [p.Color("white"), p.Color("gray")]
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            color = colors[((row + column) % 2)]
            p.draw.rect(screen, color, p.Rect(column * SQUARE_SIZE,
                        row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))


def highlightSquares(screen, game_state, valid_moves, square_selected):
    """
    Highlight square selected and moves for piece selected.
    """
    if (len(game_state.move_log)) > 0:
        last_move = game_state.move_log[-1]
        s = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
        s.set_alpha(100)
        s.fill(p.Color('blue'))
        screen.blit(s, (last_move.end_col * SQUARE_SIZE,
                    last_move.end_row * SQUARE_SIZE))
    if square_selected != ():
        row, col = square_selected
        if game_state.board[row][col][0] == (
                'w' if game_state.white_to_move else 'b'):  # square_selected is a piece that can be moved
            # highlight selected square
            s = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
            # transparency value 0 -> transparent, 255 -> opaque
            s.set_alpha(100)
            s.fill(p.Color('blue'))
            screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))
            # highlight moves from that square
            s.fill(p.Color('yellow'))
            for move in valid_moves:
                if move.start_row == row and move.start_col == col:
                    screen.blit(s, (move.end_col * SQUARE_SIZE,
                                move.end_row * SQUARE_SIZE))


def drawPieces(screen, board):
    """
    Draw the pieces on the board using the current game_state.board
    """
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            piece = board[row][column]
            if piece != "--":
                screen.blit(IMAGES[piece], p.Rect(
                    column * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

   # show moves on screen
def drawMoveLog(screen, game_state, font):
    """
    Draws the move log.
    """
    move_log_rect = p.Rect(
        BOARD_WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    p.draw.rect(screen, p.Color('gray'), move_log_rect)
    move_log = game_state.move_log
    move_texts = []
    for i in range(0, len(move_log), 2):
        move_string = str(i // 2 + 1) + '. ' + str(move_log[i]) + " "
        if i + 1 < len(move_log):
            move_string += str(move_log[i + 1]) + "  "
        move_texts.append(move_string)

    moves_per_row = 3
    padding = 5
    line_spacing = 2
    text_y = padding
    for i in range(0, len(move_texts), moves_per_row):
        text = ""
        for j in range(moves_per_row):
            if i + j < len(move_texts):
                text += move_texts[i + j]

        text_object = font.render(text, True, p.Color('black'))
        text_location = move_log_rect.move(padding, text_y)
        screen.blit(text_object, text_location)
        text_y += text_object.get_height() + line_spacing


def drawEndGameText(screen, text):
    font = p.font.SysFont("Helvetica", 32, True, False)
    text_object = font.render(text, False, p.Color("gray"))
    text_location = p.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT).move(BOARD_WIDTH / 2 - text_object.get_width() / 2,
                                                                 BOARD_HEIGHT / 2 - text_object.get_height() / 2)
    screen.blit(text_object, text_location)
    text_object = font.render(text, False, p.Color('black'))
    screen.blit(text_object, text_location.move(2, 2))


def animateMove(move, screen, board, clock):
    """
    Animating a move
    """
    global colors
    d_row = move.end_row - move.start_row
    d_col = move.end_col - move.start_col
    frames_per_square = 10  # frames to move one square
    frame_count = (abs(d_row) + abs(d_col)) * frames_per_square
    for frame in range(frame_count + 1):
        row, col = (move.start_row + d_row * frame / frame_count,
                    move.start_col + d_col * frame / frame_count)
        drawBoard(screen)
        drawPieces(screen, board)
        # erase the piece moved from its ending square
        color = colors[(move.end_row + move.end_col) % 2]
        end_square = p.Rect(move.end_col * SQUARE_SIZE,
                            move.end_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
        p.draw.rect(screen, color, end_square)
        # draw captured piece onto rectangle
        if move.piece_captured != '--':
            if move.is_enpassant_move:
                enpassant_row = move.end_row + \
                    1 if move.piece_captured[0] == 'b' else move.end_row - 1
                end_square = p.Rect(
                    move.end_col * SQUARE_SIZE, enpassant_row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            screen.blit(IMAGES[move.piece_captured], end_square)
        # draw moving piece
        screen.blit(IMAGES[move.piece_moved], p.Rect(
            col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
        p.display.flip()
        clock.tick(60)


if __name__ == "__main__":
     depth=WelcomeScreen().getDepth()
     algo=WelcomeScreen.get_algorithm()
     main(depth,algo)
