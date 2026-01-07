import random
import time

import cProfile

from game import Game

random.seed(42)

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

def make_move(game, depth=2):
    if depth == -1:
        return [[0, score_position(game), 0, 0]]
    game.update()
    pos_moves = []
    all_moves = game.possible_moves
    for start, moves in all_moves.items():
        for move in moves:
            game.move(start, move, flag=True)
            pos_moves.append(
                [None,
                 search(game, 0, 1000),
                 start, move])
            game.undo_move()
    for i in range(1, depth + 1):
        pos_moves = sorted(pos_moves, key=lambda x: x[1], reverse=True)
        best = -1000
        for pos, move in enumerate(pos_moves):
            game.move(move[2], move[3], flag=True)
            score = -search(game, i, -best)
            pos_moves[pos][1] = score
            best = max(score, best)
            game.undo_move()

    return pos_moves

def search(game, depth, prev):
    if depth == 0:
        return score_position(game)

    best = -1000
    game.update()
    all_moves = game.possible_moves
    if len(all_moves) == 0:
        if len(game.check_check()) == 0:
            return 0
        return 1000

    for start, moves in all_moves.items():
        for move in moves:
            if prev < best:
                return prev
            game.move(start, move, flag=True)
            score = -search(game, depth - 1, -best)
            game.undo_move()
            best = max(best, score)

    return best

def score_position(game):
    own_pieces = game.col_checks()
    op_pieces = game.col_checks(op=-1)
    score = 0
    for i in own_pieces:
        if i == 0:
            continue
        score += point_conv[game.position[i]]
    for i in op_pieces:
        if i == 0:
            continue
        try:
            score -= point_conv[game.position[i]]
        except:
            print(game.moves_made)
            print(i)
            print(game.fen())
            print(sorted(op_pieces))
            print([pos for pos, i in enumerate(game.position) if 0 < i < 7])
            raise KeyboardInterrupt

    random_fac = random.random() / 10 ** 2

    return score + random_fac

def time_test():
    cProfile.run('game = Game("r1b1k2r/ppppnppp/2n2q2/2b5/2BNP3/2P1B3/PP3PPP/RN1QK2R b KQkq - 2 7"); make_move(game, depth=4)')

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
    game = Game()
    start = time.perf_counter()
    move = make_move(game)
    print(f"Time: {time.perf_counter()- start}")

if __name__ == "__main__":
    #main()
    #long_test()
    time_test()
