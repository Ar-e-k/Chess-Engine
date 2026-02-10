import random
from collections import defaultdict
import time
from dataclasses import dataclass

import cProfile

from gamenew import Game
from interface import Play

inf = 10 ** 6

point_conv = {
    1: 100,
    2: 300,
    3: 300,
    4: 500,
    5: 900,
    6: 000,
    -1:100,
    -2:300,
    -3:300,
    -4:500,
    -5:900,
    -6:000
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

@dataclass(slots=True)
class TTEntry:
    key: int
    depth: int
    score: int
    flag: int
    move: int
    age: int

class Engine:

    def __init__(self, tt_size=20):
        self.tt_size = (1 << tt_size) - 1
        self.tt = [None] * self.tt_size

    def add_tt(self, game, score, move, flag):
        hsh = game.hsh
        idx = hsh & self.tt_size
        if self.tt[idx] is None:
            self.tt[idx] = TTEntry(
                key = hsh, depth=self.depth, score=score,
                move=move[0] * 1000 + move[1][0], flag=0, age=0
            )
        else:
            if self.tt[idx].depth - self.tt[idx].age <= self.depth:
                self.tt[idx] = TTEntry(
                    key = hsh, depth=self.depth, score=score,
                    move=move[0] * 1000 + move[1][0], flag=0, age=0
                )
            else:
                self.tt[idx].age += 0

    def get_tt(self, hsh):
        idx = hsh & self.tt_size
        if self.tt[idx] is None or self.tt[idx].key != hsh:
            return False, -inf
        elif self.tt[idx].depth < self.depth:
            return False, self.tt[idx].score
        return True, self.tt[idx].score

    def make_move(self, game, depth=2):
        if depth == -1:
            return [[0, -game.evaluate(), 0, 0]]
        game.update()
        pos_moves = []
        all_moves = game.possible_moves_out()
        self.depth = 0
        for start, moves in all_moves.items():
            for move in moves:
                game.move(start, move, flag=True)
                pos_moves.append(
                    [None,
                     -self.search(game, 0, -inf, inf),
                     start, move])
                game.undo_move()
        for i in range(1, depth + 1):
            self.depth = i
            pos_moves = sorted(pos_moves, key=lambda x: x[1], reverse=True)
            best = -inf
            for pos, move in enumerate(pos_moves):
                game.move(move[2], move[3], flag=True)
                score = -self.search(game, i, -inf, inf)
                pos_moves[pos][1] = score
                best = max(score, best)
                game.undo_move()

        pos_moves = sorted(pos_moves, key=lambda x: x[1], reverse=True)
        return pos_moves

    def search(self, game, depth, alpha, beta):
        tt = self.get_tt(game.hsh)
        if tt[0]:
            return tt[1]

        if depth == 0:
            best = self.q_search(game, alpha, beta)
            self.add_tt(game, best, (0,(0,0)), 0)
            return best
            #return self.score_position(game)

        best = -inf
        game.update()
        all_moves = game.possible_moves_out()
        if len(all_moves) == 0:
            if len(game.check_out()) == 0:
                return 0
            return -inf

        # BUG sorting moves decreases efficiency
        '''
        moves_ord = []
        for start, moves in all_moves.items():
            for move in moves:
                bet, score = self.get_tt(game.move_hash(start, move))
                moves_ord.append((start, move, score))
        #moves_ord = sorted(moves_ord, key=lambda x: x[2], reverse=False)

        for start, move, _ in moves_ord:
        '''
        for start, moves in all_moves.items():
            for move in moves:
                if alpha >= beta:
                    self.add_tt(game, best, (0,(0,0)), 0)
                    return best
                game.move(start, move, flag=True)
                score = -self.search(game, depth - 1, -beta, -alpha)
                game.undo_move()
                best = max(best, score)
                alpha = max(alpha, score)

        self.add_tt(game, best, (0,(0,0)), 0)
        return best

    def q_search(self, game, alpha, beta):
        game.update_captures()
        all_moves = game.captures_out()
        if len(all_moves) == 0:
            if game.check_end():
                if game.check_out()[1] == 0:
                    return 0
                return -inf
        initial = game.evaluate()
        best = initial
        alpha = max(initial, alpha)

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
            if initial + point_conv[game.position[move]] + 200 < alpha:
                return best
            game.move(start, (move, None), flag=True)
            score = -self.q_search(game, -beta, -alpha)
            game.undo_move()
            best = max(best, score)
            alpha = max(alpha, score)

        return best

def time_test():
    game = Game("r1b1k2r/ppppnppp/2n2q2/2b5/2BNP3/2P1B3/PP3PPP/RN1QK2R b KQkq - 2 7")
    engine = Engine()
    cProfile.runctx(
        'engine.make_move(game, depth=2); print(game.timer)',
        {'game': game, 'engine': engine}, {})

def debug_test():
    game = Game("r1b1k2r/ppppnppp/2n2q2/2b5/2BNP3/2P1B3/PP3PPP/RN1QK2R b KQkq - 2 7")
    #game = Game()
    engine = Engine()

def testing():
    return None

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
