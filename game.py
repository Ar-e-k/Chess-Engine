import itertools
from copy import copy
import numpy as np

translate = {
    "p": 1,
    "n": 2,
    "b": 3,
    "r": 4,
    "q": 5,
    "k": 6
}

one_x = np.array([1, 0])
one_y = np.array([0, 1])

class Game:

    str_moves = {
        "ver_plus": lambda x: x + one_x,
        "ver_min": lambda x: x - one_x,
        "hor_plus": lambda x: x + one_y,
        "hor_min": lambda x: x - one_y,
        "deg_45": lambda x: x + one_x + one_y,
        "deg_135": lambda x: x - one_x + one_y,
        "deg_225": lambda x: x - one_x - one_y,
        "deg_315": lambda x: x + one_x - one_y
    }

    piece_checks = {
        "ver": [4, 5],
        "hor": [4, 5],
        "deg": [3, 5]
    }

    piece_moves = {
        3: ["deg_45", "deg_135", "deg_225", "deg_315"],
        4: ["ver_plus", "ver_min", "hor_plus", "hor_min"],
        5: ["deg_45", "deg_135", "deg_225", "deg_315",
            "ver_plus", "ver_min", "hor_plus", "hor_min"]
    }


    def __init__(self, fen=None, game=None):
        if not game is None:
            self.position, self.state = game
        else:
            if fen is None:
                fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
            fen = fen.split("/")
            state = []
            for i in fen[7].split(" "):
                state.append(i)

            fen[7] = state[0]
            state.pop(0)
            state[0] = -1 + 2 * (state[0] == "w")
            state[3] = int(state[3])
            state[4] = int(state[4])

            self.state = state
            self.position = np.zeros((8, 8), dtype=np.int8)

            for i in range(8):
                pos = 0
                for j in fen[i]:
                    if j.isdigit():
                        pos += int(j)
                    else:
                        self.position[i][pos] = translate[j.lower()] * (-1 + 2 * j.isupper())
                        pos += 1

    def update(self):
        self.possible_moves = self.generate_moves()

    def copy(self):
        return copy(self.position), copy(self.state)

    def col_check(self, other):
        return other * self.state[0] > 0

    def move(self, start, end, promotion=None):
        if end == start or end in np.array(self.possible_moves[start]):
            if abs(self.position[start]) == 1:
                if abs(start[0] - end[0]) == 2:
                    self.state[2] = (start[0] - self.state[0], start[1])
                elif end == self.state[2]:
                    self.position[start[0], end[1]] = 0
                    self.state[2] = "-"
                else:
                    self.state[2] = "-"

                if end[0] in [0, 7]:
                    self.position[start] = promotion
            else:
                self.state[2] = "-"

            if self.position[start] == 6:
                self.state[1] = self.state[1].replace("K", "")
                self.state[1] = self.state[1].replace("Q", "")

                if end[1] - start[1] == 2:
                    self.position[7, 7] = 0
                    self.position[7, 5] = 4
                elif end[1] - start[1] == -2:
                    self.position[7, 0] = 0
                    self.position[7, 3] = 4
            elif self.position[start] == -6:
                self.state[1] = self.state[1].replace("k", "")
                self.state[1] = self.state[1].replace("q", "")

                if end[1] - start[1] == 2:
                    self.position[0, 7] = 0
                    self.position[0, 5] = 4
                elif end[1] - start[1] == -2:
                    self.position[0, 0] = 0
                    self.position[0, 3] = 4
            elif abs(self.position[start]) == 4:
                if start == (0, 0):
                    self.state[1] = self.state[1].replace("q", "")
                elif start == (0, 7):
                    self.state[1] = self.state[1].replace("k", "")
                elif start == (7, 0):
                    self.state[1] = self.state[1].replace("Q", "")
                elif start == (7, 7):
                    self.state[1] = self.state[1].replace("K", "")

            self.position[end] = self.position[start]
            self.position[start] = 0
            self.state[0] *= -1
            self.state[3] = (self.state[3] + 1) % 2
            self.state[4] += (self.state[0] + 1) // 2
            if end != start:
                self.update()
            return self.position, self.state
        print("Illegal move")
        return False

    def check_check(self, king=None):
        checks = []
        if king is None:
            king = np.where(self.position == 6 * self.state[0])
            king = np.array(king[0][0], king[1][0])
        for key, item in self.str_moves.items():
            dr = key.split("_")[0]
            out, end = self.str_move(king, item)
            if end is None:
                continue

            if abs(end) == 1 and len(out) == 1:
                print(out)
                if dr == "deg" and king[0] + end == out[0][0]:
                    checks.append(out)
            elif abs(end) in self.piece_checks[dr]:
                checks.append(out)
            elif abs(end) == 6:
                if np.all(abs(king - out) <= 1):
                    checks.append(out)

        knights = self.kn_move(king)
        for pos in knights:
            fig = self.position[*pos]
            if fig * self.state[0] == -2:
                checks.append([pos])

        return checks

    def generate_moves(self):
        # Finds positions of all pieces of current colour
        rows, cols = np.where(self.col_check(self.position))

        move_count = 0
        moves = {}
        for start in zip(rows, cols):
            p_moves = self.find_moves(start)
            moves[start] = p_moves
            move_count += len(p_moves)

        # Handels case where no moves can be made
        if len(moves) == 0:
            return False

        return moves

    def find_moves(self, start):
        piece = abs(self.position[start])
        out = []
        check_flag = False
        no_flag = False

        no_position = Game(game=self.copy())
        no_position.move(start, start)

        if piece == 6:
            no_position.state[0] *= -1
            pos = np.array(start)
            for i in itertools.permutations([1, -1, 0], 2):
                i = np.array(i)
                move = pos + i
                if np.all(0 <= move) and np.all(move <= 7):
                    if self.col_check(self.position[*move]):
                        continue
                    check = len(no_position.check_check(move)) > 0
                    if not check:
                        out.append(move)

                    if (np.all(i == [0, -1]) and
                        (self.state[0] == 1 and "K" in self.state[1]) or
                        (self.state[0] == -1 and "k" in self.state[1])):
                        move = pos + i
                        if self.col_check(self.position[*move]):
                            continue
                        check = len(no_position.check_check(move)) > 0
                        if not check:
                            out.append(move)
                    elif (np.all(i == [0, 1]) and
                        (self.state[0] == 1 and "K" in self.state[1]) or
                        (self.state[0] == -1 and "k" in self.state[1])):
                        move = pos + i
                        if self.col_check(self.position[*move]):
                            continue
                        check = len(no_position.check_check(move)) > 0
                        thrd = move + i
                        if not check and self.position[*thrd] == 0:
                            out.append(move)

            return out

        check = self.check_check()
        if len(check) != 0:
            if len(check) > 1:
                return []
            check = check[0]
            check_flag = True
        no_check = no_position.check_check()
        if len(no_check) == 1 and not check_flag or len(no_check) == 2:
            no_flag = True

        if piece == 1:
            if self.state[0] == 1:
                move = self.str_moves["ver_min"]
                take_1 = self.str_moves["deg_45"]
                take_2 = self.str_moves["deg_135"]
            else:
                move = self.str_moves["ver_plus"]
                take_1 = self.str_moves["deg_225"]
                take_2 = self.str_moves["deg_315"]

            hard = 1
            if start[0] == 6:
                hard = 2

            fw, take = self.str_move(start, move, hard)
            if not take is None:
                fw.pop()
            out += fw

            for take in [take_1, take_2]:
                take, take_c = self.str_move(start, take_1, 1)
                if take is None:
                    if self.state[2] != take[0]:
                        take = []
                out += take
        elif piece == 2:
            out = self.kn_move(start)
        elif piece in [3, 4, 5]:
            for name in self.piece_moves[piece]:
                moves, take = self.str_move(start, self.str_moves[name])
                out += moves

        if len(out) == 0:
            return []

        out = np.array(out)
        if no_check:
            for icheck in no_check:
                temp = (out[:, None] == check).all(-1).any(-1)
                out = out[temp]
        elif check_flag:
            temp = (out[:, None] == check).all(-1).any(-1)
            out = out[temp]

        return out

    def str_move(self, start, move, hard=8):
        out = []
        pos = np.array(start)
        end = None
        counter = 0

        while counter < hard:
            pos = move(pos)
            if not (np.all(0 <= pos) and np.all(pos <= 7)):
                break
            counter += 1
            if self.col_check(self.position[*pos]):
                break
            elif self.position[*pos] != 0:
                end = self.position[*pos]
                out.append(pos)
                break
            out.append(pos)
        return out, end

    def kn_move(self, start):
        out = []
        pos = np.array(start)

        for move in itertools.permutations([1, -1, 2, -2], 2):
            if abs(move[0]) == abs(move[1]):
                continue
            move = np.array(move)
            move += pos
            if np.all(0 <= move) and np.all(move <= 7):
                if self.col_check(self.position[*move]):
                    continue
                out.append(move)

        return out

def tests():
    game = Game()
    game.move([6, 4], [4, 4])
    return game

if __name__ == "__main__":
    tests()
