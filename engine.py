import random
import time

import cProfile

from gamenew import Game
from heatmaps import piece_heatmap

random.seed(42)

inf = 10 ** 6

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
        if len(game.check_check(game.position.index(6 * game.state[0]))) == 0:
            return 0
        return inf

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
    try:
        game.update()
    except:
        from interface import Play
        print(game.moves_made[-1].sqr1, game.moves_made[-1].sqr2)
        game.undo_move()
        Play(game)
    all_moves = game.possible_moves_out()
    if len(all_moves) == 0:
        if game.check_out()[1] == 0:
            return 0
        return inf
    initial = score_position(game)
    best = initial

    captures = []

    for start, moves in all_moves.items():
        for move in moves:
            if move[1]:
                continue
            move_val = capture_conv[game.position[move[0]]
                                    ] * 6 - capture_conv[game.position[start]]
            captures.append((start, move, move_val))
    captures = sorted(captures, key=lambda x: x[2], reverse=True)

    for start, move, _ in captures:
        if alpha >= beta:
            return best
        #if initial + point_conv[game.position[move[0]]] - point_conv[game.position[start]] < best - 0.1:
        #    continue
        game.move(start, move, flag=True)
        score = -q_search(game, -beta, -alpha)
        game.undo_move()
        best = max(best, score)
        alpha = max(alpha, score)

    return best

def score_position(game):
    own_pieces = game.col_checks()
    op_pieces = game.col_checks(op=-1)
    score = score_side(own_pieces, game) - score_side(op_pieces, game)

    random_fac = (random.random() - 0.5) * 10
    #random_fac = 0

    return int(1000 * score + random_fac)

def score_side(pieces, game):
    score = 0
    for i in pieces:
        if i == 0:
            continue
        score += score_piece(game, i)
    return score

def score_piece(game, pos):
    piece = game.position[pos]
    return point_conv[piece]# * piece_heatmap[piece][pos]

def time_test():
    cProfile.run('game = Game("r1b1k2r/ppppnppp/2n2q2/2b5/2BNP3/2P1B3/PP3PPP/RN1QK2R b KQkq - 2 7"); print(make_move(game, depth=0))')

def debug_test():
    game = Game("r1b1k2r/ppppnppp/2n2q2/2b5/2BNP3/2P1B3/PP3PPP/RN1QK2R b KQkq - 2 7")
    make_move(game, depth=0)

def main():
    game = Game()
    start = time.perf_counter()
    move = make_move(game)
    print(f"Time: {time.perf_counter()- start}")

if __name__ == "__main__":
    #main()
    time_test()
    #debug_test()
