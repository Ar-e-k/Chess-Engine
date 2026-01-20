import random
from collections import defaultdict
import time

import cProfile

from gamenew import Game
from interface import Play

inf = 10 ** 3

point_conv = {
    1: 1,
    2: 3,
    3: 3,
    4: 5,
    5: 9,
    6: 0,
    -1:1,
    -2:3,
    -3:3,
    -4:5,
    -5:9,
    -6:0
}
capture_conv = {
    1: 5,
    2: 10,
    3: 20,
    4: 32,
    5: 64,
    6: 0,
    -1: 5,
    -2: 10,
    -3: 20,
    -4: 32,
    -5: 64,
    -6: 0
}

def make_move(game, depth=2):
    if depth == -1:
        return [[0, score_position(game), 0, 0]]
    game.update()
    pos_moves = []
    all_moves = game.possible_moves_out()
    for start, moves in all_moves.items():
        for move in moves:
            game.move(start, move, flag=True)
            pos_moves.append(
                [None,
                 -search(game, 0, -inf, inf),
                 start, move])
            game.undo_move()
    for i in range(1, depth + 1):
        pos_moves = sorted(pos_moves, key=lambda x: x[1], reverse=True)
        best = -inf
        for pos, move in enumerate(pos_moves):
            game.move(move[2], move[3], flag=True)
            score = -search(game, i, -inf, -best)
            pos_moves[pos][1] = score
            best = max(score, best)
            game.undo_move()

    pos_moves = sorted(pos_moves, key=lambda x: x[1], reverse=True)
    return pos_moves

def search(game, depth, alpha, beta):
    if depth == 0:
        return q_search(game, alpha, beta)
        #return score_position(game)

    best = -inf
    game.update()
    all_moves = game.possible_moves_out()
    if len(all_moves) == 0:
        if len(game.check_out()) == 0:
            return 0
        return -inf

    for start, moves in all_moves.items():
        for move in moves:
            if alpha >= beta:
                return best
            game.move(start, move, flag=True)
            score = -search(game, depth - 1, -beta, -alpha)
            game.undo_move()
            best = max(best, score)
            alpha = max(alpha, score)

    return best

def q_search(game, alpha, beta):
    game.update_captures()
    all_moves = game.captures_out()
    if len(all_moves) == 0:
        game.update()
        if len(game.possible_moves_out()) == 0:
            if game.check_out()[1] == 0:
                return 0
            return -inf
    initial = score_position(game)
    best = initial

    captures = []

    for start, moves in all_moves.items():
        for move in moves:
            move_val = capture_conv[
                game.position[move]] * 6 - capture_conv[game.position[start]]
            captures.append((start, move, move_val))
    captures = sorted(captures, key=lambda x: x[2], reverse=True)

    for start, move, _ in captures:
        if alpha >= beta:
            return best
        game.move(start, (move, None), flag=True)
        score = -q_search(game, -beta, -alpha)
        game.undo_move()
        best = max(best, score)
        alpha = max(alpha, score)

    return best

def score_position(game):
    own_pieces = game.col_checks()
    op_pieces = game.col_checks(op=-1)
    score = score_side(own_pieces, game) - score_side(op_pieces, game)

    return score

def score_side(pieces, game):
    score = 0
    for i in pieces:
        if i == 0:
            continue
        score += score_piece(game, i)
    return score

def score_piece(game, pos):
    piece = game.position[pos]
    return point_conv[piece]

def time_test():
    cProfile.run('game = Game("r1b1k2r/ppppnppp/2n2q2/2b5/2BNP3/2P1B3/PP3PPP/RN1QK2R b KQkq - 2 7"); make_move(game, depth=1); print(game.timer)')

def debug_test():
    game = Game("r1b1k2r/ppppnppp/2n2q2/2b5/2BNP3/2P1B3/PP3PPP/RN1QK2R b KQkq - 2 7")
    make_move(game, depth=2)

def testing():
    game = Game(fen="r1b1k2r/pBppnppp/5q2/8/4P3/2P1b3/PP3PPP/RN1QK2R w KQk - 1 11")
    game = Game(fen="B1b1k2r/p1ppnppp/5q2/8/4P3/2P1b3/PP3PPP/RN1QK2R b KQk - 0 11")
    score = -search(game, 1, -inf, 0)
    print(score * game.state[0])

def main():
    game = Game()
    start = time.perf_counter()
    move = make_move(game)
    print(f"Time: {time.perf_counter()- start}")

if __name__ == "__main__":
    #main()
    time_test()
    #debug_test()
    #testing()
