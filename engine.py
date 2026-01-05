import random
import time
import numpy as np

import cProfile

from game import Game

random.seed(42)

point_conv = {
    1: 1,
    2: 3,
    3: 3,
    4: 5,
    5: 9,
    6: 0
}

def make_move(game, depth=2):
    game.update()
    pos_moves = []
    all_moves = game.possible_moves
    for start, moves in all_moves.items():
        for move in moves:
            game.move(start, move, flag=True)
            pos_moves.append([None, -search(game, depth), start, move])
            game.undo_move()
    pos_moves = sorted(pos_moves, key=lambda x: x[1], reverse=True)
    return pos_moves

def search(game, depth):
    if depth == 0:
        return score_position(game)

    best = -np.inf
    game.update()
    all_moves = game.possible_moves
    if len(all_moves) == 0:
        if len(game.check_check()) == 0:
            return 0
        return np.inf
    for start, moves in all_moves.items():
        for move in moves:
            game.move(start, move, flag=True)
            score = -search(game, depth - 1)
            game.undo_move()
            best = max(best, score)

    return best

def score_position(game):
    own_pieces = game.col_checks(game.position)
    op_pieces = game.col_checks(game.position, op=-1)
    score = 0
    for i in own_pieces:
        score += point_conv[abs(game.position[i])]
    for i in op_pieces:
        score -= point_conv[abs(game.position[i])]

    random_fac = random.random() / 10 ** 2

    return score + random_fac

def time_test():
    game = Game()
    cProfile.run('game = Game(); make_move(game, depth=3)')

def long_test():
    game = Game()
    for i in range(18):
        start_t = time.perf_counter()
        move = make_move(game, depth=2)[0]
        print(move)
        game.update()
        _ = game.move(move[2], move[3])
        print(game.position)
        print(game.fen())
        input(f"Move-end: {time.perf_counter() - start_t}")

def main():
    return None
    game = Game()
    start = time.perf_counter()
    move = make_move(game)
    print(f"Time: {time.perf_counter()- start}")

if __name__ == "__main__":
    #long_test()
    time_test()
