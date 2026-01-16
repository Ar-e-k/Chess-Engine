import time
import itertools
from dataclasses import dataclass

import timeit
import cProfile

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
    sqr1:int; old1:int; id1:int
    sqr2:int; old2:int; id2:int
    sqr3:int; sqr4:int; idc:int
    csl:str
    eps:int; epm:int; ide:int

class Game:

    str_dirs = [
        "ver_plus",
        "ver_min",
        "hor_plus",
        "hor_min",
        "deg_45",
        "deg_135",
        "deg_225",
        "deg_315",
    ]

    str_moves = {
        "ver_plus": 10,
        "ver_min": -10,
        "hor_plus": 1,
        "hor_min": -1,
        "deg_45": 11,
        "deg_135": 9,
        "deg_225": -11,
        "deg_315": -9
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

        self.pieces = [
            [pos for pos, i in enumerate(self.position) if 7 > i > 0] + [0],
            [pos for pos, i in enumerate(self.position) if 7 > -i > 0] + [0]
        ]

    def fen(self):
        fen = ""
        i = 0
        c1 = 0
        empty = 0
        while c1 < 64:
            i += 1
            fig = self.position[i]
            if fig == 10:
                continue
            if c1 % 8 == 0 and c1 != 0:
                if empty != 0:
                    fen += str(empty)
                    empty = 0
                fen += "/"
            c1 += 1
            if fig == 0:
                empty += 1
                continue
            if empty != 0:
                fen += str(empty)
                empty = 0
            let = fen_translate[abs(fig)]
            if fig > 0:
                fen += let.upper()
            else:
                fen +=let
        fen += " "
        if self.state[0] == 1:
            fen += "w "
        else:
            fen += "b "
        fen += self.state[1] + " "
        if self.state[2] == "-":
            fen += "-"
        else:
            fen +=  chr(self.state[2] // 10 + 95) + str(9 - self.state[2] % 10)
        fen += " " + str(self.state[3]) + " " + str(self.state[4])
        return fen

    def update(self):
        self.possible_moves = self.generate_moves()

    def possible_moves_out(self):
        return self.possible_moves

    def col_checks(self, op=1):
        return self.pieces[(self.state[0] * op - 1) // -2][:-1]

    def col_check(self, pos, op=1):
        return self.position[pos] * self.state[0] * op > 0

    def bound_check(self, pos):
        return self.position[pos] == 10

    def undo_move(self):
        move = self.moves_made.pop()
        p_index = (-self.state[0] - 1) // -2
        self.position[move.sqr1] = move.old1
        self.position[move.sqr2] = move.old2
        self.position[move.epm] = 1 * self.state[0]
        self.position[move.sqr3] = -4 * self.state[0]
        self.position[move.sqr4] = 0
        self.position[-1] = 0
        self.pieces[p_index][move.id1] = move.sqr1
        self.pieces[(p_index + 1) % 2][move.id2] = move.sqr2
        self.pieces[(p_index + 1) % 2][move.ide] = move.epm
        self.pieces[p_index][move.idc] = move.sqr3
        self.state[4] -= (self.state[0] + 1) // 2
        self.state[0] *= -1
        self.state[3] = (self.state[3] - 1) % 2
        self.state[1] = move.csl
        self.state[2] = move.eps

    def pone_moved(self, start, end, promotion):
        if self.position[start] in [1, -1]:
            if abs(start - end) == 20:
                self.state[2] = start - self.state[0] * 10
            elif end == self.state[2]:
                ep = self.state[2] + self.state[0] * 10
                self.position[ep] = 0
                self.state[2] = "-"
                o_index = (-self.state[0] - 1) // -2
                ide = self.pieces[o_index].index(ep)
                self.pieces[o_index][ide] = 0
                return ep, ide
            else:
                self.state[2] = "-"

            if end // 10 in [2, 9]:
                self.position[start] = 5 * self.state[0]
        else:
            self.state[2] = "-"
        return -1, -1

    def king_move(self, start, end):
        if self.position[start] == 6:
            self.state[1] = self.state[1].replace("K", "")
            self.state[1] = self.state[1].replace("Q", "")

            if end - start == 2:
                return 98, 96, self.castle(98, 96, 0, 1)
            elif end - start == -2:
                return 91, 94, self.castle(91, 94, 0, 1)
        elif self.position[start] == -6:
            self.state[1] = self.state[1].replace("k", "")
            self.state[1] = self.state[1].replace("q", "")

            if end - start == 2:
                return 28, 26, self.castle(28, 26, 1, -1)
            elif end - start == -2:
                return 21, 24, self.castle(21, 24, 1, -1)
        return -1, -1, -1

    def castle(self, start, end, p_index, side):
        self.position[start] = 0
        self.position[end] = side * 4
        idc = self.pieces[p_index].index(start)
        self.pieces[p_index][idc] = end
        return idc

    def move(self, start, end, promotion=None, flag=False):
        if flag or end in self.possible_moves[start]:
            end = end[0]
            cs, es = self.state[1:3]
            id2 = -1
            p_index = (self.state[0] - 1) // -2
            id1 = self.pieces[p_index].index(start)
            old1 = self.position[start]

            self.pieces[p_index][id1] = end
            if self.position[end] != 0:
                o_index = (p_index + 1) % 2
                id2 = self.pieces[o_index].index(end)
                self.pieces[o_index][id2] = 0

            ep, ide = self.pone_moved(start, end, promotion)
            c1, c2, idc = self.king_move(start, end)

            if self.position[start] in [4, -4]:
                if start == 21:
                    self.state[1] = self.state[1].replace("q", "")
                elif start == 28:
                    self.state[1] = self.state[1].replace("k", "")
                elif start == 91:
                    self.state[1] = self.state[1].replace("Q", "")
                elif start == 98:
                    self.state[1] = self.state[1].replace("K", "")

            move_s = Undo(
                sqr1=start, old1=old1, id1=id1,
                sqr2=end, old2=self.position[end], id2=id2,
                sqr3=c1, sqr4=c2, idc=idc,
                csl=cs,
                eps=es, epm=ep, ide=ide
            )
            self.moves_made.append(move_s)

            self.position[end] = self.position[start]
            self.position[start] = 0
            self.state[0] *= -1
            self.state[3] = (self.state[3] + 1) % 2
            self.state[4] += (self.state[0] + 1) // 2
            return True
        return False

    def check_out(self):
        king = self.position.index(6 * self.state[0])
        return self.check_check(king)

    def check_check(self, king, s_dir=None):
        checks = []
        dirs = s_dir or self.str_dirs
        for key in dirs:
            out, end = self.str_move(king, key)
            if end is None:
                continue

            if abs(end) == 1 and len(out) == 1:
                if key[:3] == "deg" and king * end < out[0][0] * end:
                    checks.append([out[0][0]])
            elif abs(end) in self.piece_checks[key[:3]]:
                checks.append([i[0] for i in out])
            elif abs(end) == 6 and len(out) == 1:
                checks.append([out[0][0]])

        if not s_dir is None:
            return checks

        knights = self.kn_move(king)
        for pos in knights:
            fig = self.position[pos[0]]
            if fig * self.state[0] == -2:
                checks.append([pos[0]])

        return checks

    def generate_moves(self):
        pieces = self.col_checks()

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
            if start == 0:
                continue
            piece = abs(self.position[start])
            if d_check and piece != 6:
                continue
            p_moves = self.find_moves(
                start, check, king, check_flag, piece)
            if len(p_moves) != 0:
                moves[start] = p_moves

        if len(moves) == 0:
            return {}

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
                check = len(self.check_check(move)) > 0
                if not check:
                    out.append((move, self.position[move] == 0))
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
                        out.append((move, True))
                elif (i == -1 and
                    ((self.state[0] == 1 and "Q" in self.state[1]) or
                    (self.state[0] == -1 and "q" in self.state[1]))):
                    move = move + i
                    if self.position[move] != 0:
                        continue
                    check = len(self.check_check(move)) > 0
                    thrd = move + i
                    if not check and self.position[thrd] == 0:
                        out.append((move, True))

            self.position[start] = 6 * self.state[0]
            return out

        king_dif = start - king
        if king_dif % 10 == 0:
            if king_dif > 0:
                s_dir = ["ver_plus"]
            else:
                s_dir = ["ver_min"]
        elif king_dif // 8 in [0, -1]:
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
            no_check = self.check_check(king, s_dir=s_dir)
            if len(no_check) != 0:
                no_flag = True
                dr = s_dir[0][:3]
            self.position[start] = piece * self.state[0]

        if piece == 1:
            if no_flag:
                if dr == "hor":
                    return []
                elif dr == "ver":
                    out = self.pone_move(start)
                elif dr == "deg":
                    out = self.pone_take(start, s_dir[0])
            else:
                out = self.pone_move(start) + self.pone_take(start)
        elif piece == 1:
            mx_fw = 1
            mx_tk = [1, 1]
            if start // 10 == 8 or start // 10 == 3:
                mx_fw = 2
            if no_flag:
                if dr == "hor":
                    return []
                if dr != "ver":
                    mx_fw = 0
                if dr != "deg":
                    mx_tk = [0, 0]

            if self.state[0] == 1:
                move = "ver_min"
                takes = ["deg_225", "deg_315"]
            else:
                move = "ver_plus"
                takes = ["deg_45", "deg_135"]
            if no_flag:
                if dr == "deg":
                    if takes[:1] == s_dir:
                        mx_tk = [1, 0]
                    elif takes[1:] == s_dir:
                        mx_tk = [0, 1]

            fw, take = self.str_move(start, move, mx_fw)
            if not take is None:
                fw.pop()
            out += fw

            for i in [0, 1]:
                take = takes[i]
                take, take_c = self.str_move(start, take, mx_tk[i])
                if len(take) == 0:
                    continue
                if take_c is None:
                    if self.state[2] != take[0]:
                        continue
                out += take
        elif piece == 2:
            if no_flag:
                return []
            out = self.kn_move(start)
        elif piece in [3, 4, 5]:
            for name in self.piece_moves[piece]:
                if no_flag:
                    if name[:3] != dr:
                        continue
                    if dr == "deg":
                        if int(name[4]) % 2 != int(s_dir[0][4]) % 2:
                            continue
                moves, take = self.str_move(start, name)
                out += moves

        # Should be redunant TODO test
        '''
        if no_flag:
            out_check = []
            for i in out:
                for check in no_check:
                    if i in check:
                        out_check.append(i)
            return out_check
        '''
        if check_flag:
            out_check = []
            for i in out:
                if i[0] in check:
                    out_check.append(i)
            return out_check

        return out

    def pone_move(self, start):
        one = start - self.state[0] * 10
        if self.position[one] == 0:
            if start // 10 == 8 or start // 10 == 3:
                two = one - self.state[0] * 10
                if self.position[two] == 0:
                    return [(one, True), (two, True)]
                else:
                    return [(one, True)]
            else:
                return [(one, True)]
        return []

    def pone_take(self, start, dr=None):
        out = []
        if start % 10 != 8 and (dr is None or int(dr[4]) % 2 == 0):
            right = start - self.state[0] * 11
            if not self.col_check(right) and self.position[right] != 0:
                out.append((right, False))
            elif right == self.state[2]:
                out.append((right, False))
        if start % 10 != 1 and (dr is None or int(dr[4]) % 2 == 1):
            left = start - self.state[0] * 9
            if not self.col_check(left) and self.position[left] != 0:
                out.append((left, False))
            elif left == self.state[2]:
                out.append((left, False))
        return out

    def str_move(self, pos, move, hard=8):
        move = self.str_moves[move]
        out = []
        end = None
        counter = 0

        while counter < hard:
            pos += move
            counter += 1
            if self.col_check(pos) or self.bound_check(pos):
                break
            elif self.position[pos] != 0:
                end = self.position[pos]
                out.append((pos, False))
                break
            out.append((pos, True))
        return out, end

    def kn_move(self, pos):
        out = []

        for move in knight_moves:
            new_pos = move + pos
            if self.bound_check(new_pos) or self.col_check(new_pos):
                continue
            out.append((new_pos, self.position[new_pos] == 0))

        return out

game = Game()
start_t = time.perf_counter()
game.update()
print(f"Update: {time.perf_counter() - start_t}")

def update_loads(num, game):
    for _ in range(num):
        game.update()

#cProfile.run('game = Game("r1b1k2r/ppppnppp/2n2q2/2b5/2BNP3/2P1B3/PP3PPP/RN1QK2R b KQkq - 2 7"); update_loads(10 ** 4, game)')
