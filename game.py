import time
import itertools
from dataclasses import dataclass

translate = {
    "p": 1,
    "n": 2,
    "b": 3,
    "r": 4,
    "q": 5,
    "k": 6
}

fen_translate = {
    0: "",
    1: "p",
    2: "n",
    3: "b",
    4: "r",
    5: "q",
    6: "k"
}

knight_moves = [
    12, 8, 21, 19,
    -12, -8, -21, -19
]
king_moves = [
    1, 9, 10, 11,
    -1, -9, -10, -11
]

@dataclass
class Undo:
    sqr1:int; old1:int
    sqr2:int; old2:int
    sqr3:int; sqr4:int
    csl:str
    eps:int; epm:int

class Game:

    str_moves = {
        "ver_plus": lambda x: x + 10,
        "ver_min": lambda x: x - 10,
        "hor_plus": lambda x: x + 1,
        "hor_min": lambda x: x - 1,
        "deg_45": lambda x: x + 11,
        "deg_135": lambda x: x + 9,
        "deg_225": lambda x: x - 11,
        "deg_315": lambda x: x - 9
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
        self.timer = 0
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
            self.position = []

            for i in range(8):
                self.position.append(10)
                pos = 0
                for j in fen[i]:
                    if j.isdigit():
                        pos += int(j)
                    else:
                        self.position += [0] * pos
                        self.position += [translate[j.lower()] * (-1 + 2 * j.isupper())]
                        pos = 0
                self.position += [0] * pos
                self.position.append(10)

            self.position = [10] * 20 + self.position
            self.position += [10] * 21

        self.moves_made = []

    def fen(self):
        return None
        # TODO fix
        fen = ""
        for row in self.position:
            empty = 0
            for i in row:
                if i == 0:
                    empty += 1
                    continue
                else:
                    if empty != 0:
                        fen += str(empty)
                        empty = 0
                let = fen_translate[abs(i)]
                if i > 0:
                    fen += let.upper()
                else:
                    fen +=let
            if empty != 0:
                fen += str(empty)
            fen += "/"
        fen = fen[:-1]
        fen += " "
        if self.state[0] == 1:
            fen += "w "
        else:
            fen += "b "
        fen += self.state[1] + " "
        if self.state[2] == "-":
            fen += "-"
        else:
            fen +=  chr(self.state[2][0] + 97) + str(8 - self.state[2][1])
        fen += " " + str(self.state[3]) + " " + str(self.state[4])
        return fen

    def update(self):
        self.possible_moves = self.generate_moves()

    def col_checks(self, other):
        return [pos for pos, i in enumerate(other)
                if 7 > i * self.state[0] > 0]

    def col_check(self, pos, op=1):
        return self.position[pos] * self.state[0] * op > 0

    def bound_check(self, pos):
        return self.position[pos] == 10

    def undo_move(self):
        move = self.moves_made.pop()
        self.position[move.sqr1] = move.old1
        self.position[move.sqr2] = move.old2
        self.position[move.epm] = 1 * self.state[0]
        self.position[move.sqr3] = -4 * self.state[0]
        self.position[move.sqr4] = 0
        self.position[-1] = 0
        self.state[4] -= (self.state[0] + 1) // 2
        self.state[0] *= -1
        self.state[3] = (self.state[3] - 1) % 2
        self.state[1] = move.csl
        self.state[2] = move.eps

    def move(self, start, end, promotion=None, flag=False, same=False):
        if same:
            self.position[start] = 0
            return True
        elif flag or end in self.possible_moves[start]:
            c1, c2, ep = -1, -1, -1
            cs, es = self.state[1:3]

            if abs(self.position[start]) == 1:
                if abs(start - end) == 20:
                    self.state[2] = start - self.state[0] * 10
                elif end == self.state[2]:
                    ep = self.state[2] + self.state[0] * 10
                    self.position[ep] = 0
                    self.state[2] = "-"
                else:
                    self.state[2] = "-"

                #if end[0] in [0, 7]:
                #    self.position[start] = promotion
            else:
                self.state[2] = "-"

            if self.position[start] == 6:
                self.state[1] = self.state[1].replace("K", "")
                self.state[1] = self.state[1].replace("Q", "")

                if end - start == 2:
                    self.position[98] = 0
                    self.position[96] = 4
                    c1 = 98
                    c2 = 96
                elif end - start == -2:
                    self.position[91] = 0
                    self.position[94] = 4
                    c1 = 91
                    c2 = 94
            elif self.position[start] == -6:
                self.state[1] = self.state[1].replace("k", "")
                self.state[1] = self.state[1].replace("q", "")

                if end - start == 2:
                    self.position[28] = 0
                    self.position[26] = -4
                    c1 = 28
                    c2 = 26
                elif end - start == -2:
                    self.position[21] = 0
                    self.position[24] = -4
                    c1 = 21
                    c2 = 24
            elif abs(self.position[start]) == 4:
                if start == 12:
                    self.state[1] = self.state[1].replace("q", "")
                elif start == 19:
                    self.state[1] = self.state[1].replace("k", "")
                elif start == 82:
                    self.state[1] = self.state[1].replace("Q", "")
                elif start == 99:
                    self.state[1] = self.state[1].replace("K", "")

            move_s = Undo(
                sqr1=start, old1=self.position[start],
                sqr2=end, old2=self.position[end],
                sqr3=c1, sqr4=c2,
                csl=cs,
                eps=es, epm=ep
            )
            self.moves_made.append(move_s)

            self.position[end] = self.position[start]
            self.position[start] = 0
            self.state[0] *= -1
            self.state[3] = (self.state[3] + 1) % 2
            self.state[4] += (self.state[0] + 1) // 2
            return True
        print(f"Illegal move: {start, end}")
        return False

    def check_check(self, king=None, s_dir=None):
        if s_dir is None:
            dir_check = lambda _: True
        else:
            dir_check = lambda x: x in s_dir
        checks = []
        if king is None:
            king = self.position.index(6 * self.state[0])
        for key, item in self.str_moves.items():
            dr = key.split("_")[0]
            if not dir_check(key):
                continue
            out, end = self.str_move(king, key)
            if end is None:
                continue

            if abs(end) == 1 and len(out) == 1:
                if dr == "deg" and self.col_check(end):
                    checks.append(out)
            elif abs(end) in self.piece_checks[dr]:
                checks.append(out)
            elif abs(end) == 6 and len(out) == 1:
                checks.append(out)

        if not dir_check("a"):
            return checks

        knights = self.kn_move(king)
        for pos in knights:
            fig = self.position[pos]
            if fig * self.state[0] == -2:
                checks.append([pos])

        return checks

    def generate_moves(self):
        pieces = self.col_checks(self.position)

        move_count = 0
        moves = {}
        king = self.position.index(6 * self.state[0])
        check = self.check_check(king)
        check_flag = False
        d_check = False

        if len(check) != 0:
            if len(check) > 1:
                d_check = True
            else:
                check = set(check[0])
                check_flag = True

        for start in pieces:
            piece = abs(self.position[start])
            if d_check and piece != 6:
                continue
            p_moves = self.find_moves(
                start, check, king, check_flag, piece)
            moves[start] = p_moves
            move_count += len(p_moves)

        if len(moves) == 0:
            return False

        return moves

    def find_moves(self, start, check, king, check_flag, piece):
        out = []
        no_flag = False

        if piece == 6:
            self.position[start] = 0
            for i in king_moves:
                move = start + i
                if self.col_check(move) or self.bound_check(move):
                    continue
                check = len(self.check_check(king=move)) > 0
                if not check:
                    out.append(move)
                else:
                    continue

                if check_flag:
                    continue

                if (i == 1 and
                    ((self.state[0] == 1 and "K" in self.state[1]) or
                    (self.state[0] == -1 and "k" in self.state[1]))):
                    move = move + i
                    if self.position[move] != 0:
                        continue
                    check = len(self.check_check(move)) > 0
                    if not check:
                        out.append(move)
                elif (i == -1 and
                    (self.state[0] == 1 and "Q" in self.state[1]) or
                    (self.state[0] == -1 and "q" in self.state[1])):
                    move = move + i
                    if self.position[move] != 0:
                        continue
                    check = len(self.check_check(move)) > 0
                    thrd = move + i
                    if not check and self.position[thrd] == 0:
                        out.append(move)

            self.position[start] = 6 * self.state[0]
            return out

        king_dif = start - king
        if king_dif % 10 == 0:
            if king_dif > 0:
                s_dir = ["ver_plus"]
            else:
                s_dir = ["ver_min"]
        elif king_dif // 10 == 0:
            if king_dif > 0:
                s_dir = ["hor_plus"]
            else:
                s_dir = ["hor_min"]
        elif king_dif % 11 == 0:
            if king_dif > 0:
                s_dir = ["deg_45"]
            else:
                s_dir = ["deg_225"]
        elif king_dif % 9 == 0:
            if king_dif > 0:
                s_dir = ["deg_135"]
            else:
                s_dir = ["deg_315"]
        else:
            s_dir = []
        if len(s_dir) != 0:
            self.position[start] = 0
            no_check = self.check_check(king=king, s_dir=s_dir)
            if len(no_check) == 1 and not check_flag or len(no_check) == 2:
                no_flag = True
            self.position[start] = piece * self.state[0]

        if piece == 1:
            if self.state[0] == 1:
                move = "ver_min"
                take_1 = "deg_225"
                take_2 = "deg_315"
            else:
                move = "ver_plus"
                take_1 = "deg_45"
                take_2 = "deg_135"

            hard = 1
            if start // 10 == 8 or start // 10 == 3:
                hard = 2

            fw, take = self.str_move(start, move, hard)
            if not take is None:
                fw.pop()
            out += fw

            for take in [take_1, take_2]:
                take, take_c = self.str_move(start, take, 1)
                if len(take) == 0:
                    continue
                if take_c is None:
                    if self.state[2] != take[0]:
                        continue
                out += take
        elif piece == 2:
            out = self.kn_move(start)
        elif piece in [3, 4, 5]:
            for name in self.piece_moves[piece]:
                moves, take = self.str_move(start, name)
                out += moves

        if len(out) == 0:
            return []

        if no_flag:
            out_check = []
            for i in out:
                for check in no_check:
                    if i in check:
                        out_check.append(i)
            return out_check
        if check_flag:
            out_check = []
            for i in out:
                if i in check:
                    out_check.append(i)
            return out_check

        return out

    def str_move(self, pos, move, hard=8):
        move = self.str_moves[move]
        out = []
        end = None
        counter = 0

        while counter < hard:
            pos = move(pos)
            counter += 1
            if self.col_check(pos):
                break
            elif self.bound_check(pos):
                break
            elif self.position[pos] != 0:
                end = self.position[pos]
                out.append(pos)
                break
            out.append(pos)
        return out, end

    def kn_move(self, pos):
        out = []

        for move in knight_moves:
            new_pos = move + pos
            if self.bound_check(new_pos) or self.col_check(new_pos):
                continue
            out.append(new_pos)

        return out

def tests():
    game = Game()
    game.move([6, 4], [4, 4])
    return game

if __name__ == "__main__":
    tests()

game = Game()
start_t = time.perf_counter()
game.update()
print(f"Update: {time.perf_counter() - start_t}")
