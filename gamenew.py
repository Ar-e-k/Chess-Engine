import time
import itertools
from collections import defaultdict
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

zero_func = lambda: 0

def print_bits(bits):
    for pos, i in enumerate(f"{bits:064b}"):
        if pos % 8 != 7:
            print(i, end="")
        else:
            print(i)

@dataclass
class Undo:
    sqr1:int; old1:int; id1:int
    sqr2:int; old2:int; id2:int
    sqr3:int; sqr4:int; idc:int
    csl:str
    eps:int; epm:int; ide:int
    bit_map:dict; bitc:int; bito:int

class Game:

    str_dirs = [
        "ver_plus",
        "ver_min",
        "hor_plus",
        "hor_min",
        "deg_45",
        "deg_225",
        "deg_135",
        "deg_315",
    ]

    str_moves = {
        "ver_plus": 10,
        "ver_min": -10,
        "hor_plus": 1,
        "hor_min": -1,
        "deg_45": 11,
        "deg_225": -11,
        "deg_135": 9,
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
        white = 0
        for i in self.pieces[0][:-1]:
            white |= 1 << self.pos_convert(i)
        black = 0
        for i in self.pieces[1][:-1]:
            black |= 1 << self.pos_convert(i)
        self.piece_bitmap = [white, black]

        self.bitboards = [0] * 121
        self.make_bitboard()

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

    def make_bitboard(self):
        for pos, start in enumerate(self.position):
            if start == 0 or start == 10:
                continue
            if start == -self.state[0]:
                self.state[0] *= -1
                self.bitboards[pos] = self.find_moves(pos, abs(start))
                self.state[0] *= -1
            else:
                self.bitboards[pos] = self.find_moves(pos, abs(start))

    def pos_convert(self, num):
        return (num // 10 - 2) * 8 + num % 10 - 1

    def rev_convert(self, num):
        return (num // 8 + 2) * 10 + num % 8 + 1

    def one_convert(self, num):
        return (num - 1) // -2

    def zero_convert(self, num):
        return -(2 * num) + 1

    def update(self):
        self.possible_moves = self.generate_moves()

    def possible_moves_out(self):
        out = {}
        for start, move in self.possible_moves.items():
            row = []
            for pos, i in enumerate(f"{move:64b}"[::-1]):
                if i == "1":
                    row.append((
                        self.rev_convert(pos),
                        1 << pos & self.piece_bitmap[
                            self.one_convert(-self.state[0])] == 0))
            if row == []:
                continue
            out[start] = row
        return out

    def return_check(self):
        attacks = self.make_attacks()
        out = []
        king = self.position.index(6 * self.state[0])
        checks = self.check_check(king, attacks)[0]

        for pos, check in enumerate(f'{checks & self.piece_bitmap[self.one_convert(-self.state[0])]:064b}'[::-1]):
            if check == "1":
                out.append(self.rev_convert(pos))
        return out

    def col_checks(self, op=1):
        return self.pieces[(self.state[0] * op - 1) // -2][:-1]

    def col_check(self, pos, op=1):
        return self.position[pos] * self.state[0] * op > 0

    def bound_check(self, pos):
        return self.position[pos] == 10

    def undo_move(self):
        move = self.moves_made.pop()
        p_index = (-self.state[0] - 1) // -2
        o_index = (p_index + 1) % 2
        self.position[move.sqr1] = move.old1
        self.position[move.sqr2] = move.old2
        self.position[move.epm] = 1 * self.state[0]
        self.position[move.sqr3] = -4 * self.state[0]
        self.position[move.sqr4] = 0
        self.position[-1] = 0
        self.piece_bitmap[o_index] ^= move.bito
        self.piece_bitmap[p_index] ^= move.bitc
        self.pieces[p_index][move.id1] = move.sqr1
        self.pieces[o_index][move.id2] = move.sqr2
        self.pieces[o_index][move.ide] = move.epm
        self.pieces[p_index][move.idc] = move.sqr3
        self.state[4] -= (self.state[0] + 1) // 2
        self.state[0] *= -1
        self.state[3] = (self.state[3] - 1) % 2
        self.state[1] = move.csl
        self.state[2] = move.eps
        for start, bits in move.bit_map.items():
            self.bitboards[start] = bits

    def update_bitboards(self, start, end, bit_change, takes):
        piece = self.position[start]
        self.position[start] = 0
        new_ray = self.find_moves(end, abs(piece))
        self.bitboards[end] = new_ray

        deltas_old = self.check_rays(start)
        for pos, delta in deltas_old.items():
            if pos == end:
                continue
            bit_change.setdefault(pos, self.bitboards[pos])
            self.bitboards[pos] |= delta
        if takes:
            self.position[start] = piece
            return bit_change
        deltas_new = self.check_rays(end)
        for pos, delta in deltas_new.items():
            bit_change.setdefault(pos, self.bitboards[pos])
            self.bitboards[pos] ^= delta
            self.bitboards[pos] |= 1 << self.pos_convert(end)

        self.position[start] = piece
        return bit_change

    def pone_moved(self, start, end, promotion, bit_change, deltao):
        if self.position[start] in [1, -1]:
            if abs(start - end) == 20:
                self.state[2] = start - self.state[0] * 10
            elif end == self.state[2]:
                ep = self.state[2] + self.state[0] * 10
                self.position[ep] = 0
                o_index = (-self.state[0] - 1) // -2
                ide = self.pieces[o_index].index(ep)
                self.pieces[o_index][ide] = 0

                piece = self.position[start]
                self.position[start] = 0
                taken = 1 << self.pos_convert(self.state[2])
                deltas_old = self.check_rays(self.state[2])
                for pos, delta in deltas_old.items():
                    bit_change[pos] = self.bitboards[pos]
                    self.bitboards[pos] |= delta
                self.position[start] = piece

                deltao = 1 << self.pos_convert(ep)
                self.state[2] = "-"
                return ep, ide, bit_change, deltao
            else:
                self.state[2] = "-"

            if end // 10 in [2, 9]:
                self.position[start] = 5 * self.state[0]
            else:
                pass
        else:
            self.state[2] = "-"
        return -1, -1, bit_change, deltao

    def king_move(self, start, end, bit_change, deltac):
        if self.position[start] == 6:
            self.state[1] = self.state[1].replace("K", "")
            self.state[1] = self.state[1].replace("Q", "")

            if end - start == 2:
                rays = ["hor_min", "ver_min"]
                bit_change[98] = self.bitboards[98]
                idc, dlc = self.castle(98, 96, 0, 1, rays)
                return 98, 96, idc, bit_change, deltac | dlc
            elif end - start == -2:
                rays = ["hor_plus", "ver_min"]
                bit_change[91] = self.bitboards[91]
                idc, dlc = self.castle(91, 94, 0, 1, rays)
                return 91, 94, idc, bit_change, deltac | dlc
        elif self.position[start] == -6:
            self.state[1] = self.state[1].replace("k", "")
            self.state[1] = self.state[1].replace("q", "")

            if end - start == 2:
                rays = ["hor_min", "ver_plus"]
                idc, dlc = self.castle(28, 26, 1, -1, rays)
                bit_change[28] = self.bitboards[28]
                return 28, 26, idc, bit_change, deltac | dlc
            elif end - start == -2:
                rays = ["hor_plus", "ver_plus"]
                idc, dlc = self.castle(21, 24, 1, -1, rays)
                bit_change[21] = self.bitboards[21]
                return 21, 24, idc, bit_change, deltac | dlc
        return -1, -1, -1, bit_change, deltac

    def castle(self, start, end, p_index, side, rays):
        self.position[start] = 0
        self.position[end] = side * 4
        idc = self.pieces[p_index].index(start)
        self.pieces[p_index][idc] = end
        deltac = 1 << self.pos_convert(start) | 1 << self.pos_convert(end)
        moves = 0
        for ray in rays:
            moves |= self.str_move(end, ray)[0]
        self.bitboards[end] = moves
        return idc, deltac

    def move(self, start, end, promotion=None, flag=False):
        if flag or end in self.possible_moves_out()[start]:
            end = end[0]
            delta = {end: self.bitboards[end]}
            cs, es = self.state[1:3]
            id2 = -1
            p_index = self.one_convert(self.state[0])
            o_index = (p_index + 1) % 2
            id1 = self.pieces[p_index].index(start)
            old1 = self.position[start]
            old2 = self.position[end]

            deltac = 1 << self.pos_convert(start) | 1 << self.pos_convert(end)
            deltao = 0

            self.pieces[p_index][id1] = end
            if self.position[end] != 0:
                id2 = self.pieces[o_index].index(end)
                self.pieces[o_index][id2] = 0
                deltao = 1 << self.pos_convert(end)

            ep, ide, delta, deltao = self.pone_moved(start, end, promotion, delta, deltao)
            delta = self.update_bitboards(start, end, delta, old2!=0)
            c1, c2, idc, delta, deltac = self.king_move(start, end, delta, deltac)

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
                sqr2=end, old2=old2, id2=id2,
                sqr3=c1, sqr4=c2, idc=idc,
                csl=cs,
                eps=es, epm=ep, ide=ide,
                bit_map=delta, bitc=deltac, bito=deltao
            )
            self.moves_made.append(move_s)

            self.piece_bitmap[p_index] ^= deltac
            self.piece_bitmap[o_index] ^= deltao
            self.position[end] = self.position[start]
            self.position[start] = 0
            self.state[0] *= -1
            self.state[3] = (self.state[3] + 1) % 2
            self.state[4] += (self.state[0] + 1) // 2
            return True
        return False

    def make_attacks(self, op=-1):
        out = 0
        for i in self.col_checks(op):
            out |= self.bitboards[i]
        return out

    def check_rays(self, start):
        deltas = defaultdict(zero_func)
        rays = []
        for key in self.str_dirs:
            out, end = self.str_move(start, key)
            rays.append((out, end, key[:3]))
        i = -1
        for out, end, key in rays:
            i += 1
            if end is None or end == start:
                continue
            piece = abs(self.position[end])

            if piece in self.piece_checks[key]:
                deltas[end] |= rays[i + self.zero_convert(i % 2)][0] | 1 << self.pos_convert(start)
            elif piece == 6 and out.bit_count() == 1:
                deltas[end] |= 1 << self.pos_convert(start)

        return deltas

    def check_check_old(self, king, attacks):
        if attacks & (1 << self.pos_convert(king)) == 0:
            return 0, 0, attacks

        checks = 0
        out = 0
        bitmap = self.piece_bitmap[self.one_convert(-self.state[0])]
        for i in [1, 2, 3, 4]:
            moves = self.find_moves(king, i)
            attacks =  moves & bitmap
            if attacks == 0:
                continue
            attack2 = None
            attack = len(f'{attacks:b}') - 1
            if i in [3, 4]:
                unique = attacks - 2 ** attack
                if unique != 0:
                    attack2 = self.rev_convert(len(f'{unique:b}') - 1)
            attack = self.rev_convert(attack)
            piece = self.position[attack]
            if (piece in [-i, i] or (i in [3, 4] and piece in [-5, 5])):
                checks += 1
                out |= (moves & self.bitboards[attack] | attacks)
            if not attack2 is None:
                piece = self.position[attack2]
                if (piece in [-i, i] or (i in [3, 4] and piece in [-5, 5])):
                    checks += 1
                    out |= (moves & self.bitboards[attack2] | attacks)

        return out, checks

    def check_out(self):
        king = self.position.index(6 * self.state[0])
        attacks = self.make_attacks()
        return self.check_check(king, attacks)

    def check_check(self, king, attacks):
        if attacks & (1 << self.pos_convert(king)) == 0:
            return 0, 0, attacks

        checks = 0
        out = 0
        bitmap = self.piece_bitmap[self.one_convert(-self.state[0])]
        for i in [1, 2]:
            moves = self.find_moves(king, i)
            p_attacks =  moves & bitmap
            if p_attacks == 0:
                continue
            attack = self.rev_convert(len(f'{p_attacks:b}') - 1)
            piece = self.position[attack]
            if piece in [-i, i]:
                checks += 1
                out |= (moves & self.bitboards[attack] | p_attacks)

        for i in range(0, 8, 2):
            attack_ray = self.str_move(king, self.str_dirs[i])[0]
            delta_ray = self.str_move(king, self.str_dirs[i + 1])[0]
            p_attacks = attack_ray & bitmap
            flag = False
            if p_attacks == 0:
                attack_ray, delta_ray = delta_ray, attack_ray
                p_attacks = attack_ray & bitmap
                flag = True
            if p_attacks == 0:
                continue
            attack = self.rev_convert(len(f'{p_attacks:b}') - 1)
            piece = abs(self.position[attack])
            if piece in [3,4,5] and self.str_dirs[i] in self.piece_moves[piece]:
                checks += 1
                out |= (attack_ray & self.bitboards[attack] | p_attacks)
                attacks |= delta_ray
            if flag:
                continue
            attack_ray, delta_ray = delta_ray, attack_ray
            p_attacks = attack_ray & bitmap
            if p_attacks == 0:
                continue
            attack = self.rev_convert(len(f'{p_attacks:b}') - 1)
            piece = abs(self.position[attack])
            if piece in [3,4,5] and self.str_dirs[i] in self.piece_moves[piece]:
                checks += 1
                out |= (attack_ray & self.bitboards[attack] | p_attacks)
                attacks |= delta_ray

        return out, checks, attacks

    def generate_moves(self):
        pieces = self.col_checks()

        attacks = self.make_attacks()
        moves = {}
        king = self.position.index(6 * self.state[0])
        check, check_num, attacks = self.check_check(king, attacks)
        check_flag = False
        d_check = False

        if check_num != 0:
            if check_num > 1:
                d_check = True
            else:
                check_flag = True

        for start in pieces:
            if start == 0:
                continue
            piece = abs(self.position[start])
            if d_check and piece != 6:
                continue
            p_moves = self.find_legal_moves(
                start, check, king, check_flag, piece, attacks)
            lis = []
            moves[start] = p_moves
            #if len(p_moves) != 0:
            #    moves[start] = p_moves

        if len(moves) == 0:
            return {}

        return moves

    def find_legal_moves(self, start, check, king, check_flag, piece, attacks):
        moves = self.bitboards[start]
        temp = moves & self.piece_bitmap[self.one_convert(self.state[0])]
        moves ^= temp
        if piece == 1:
            if self.state[2] == "-":
                moves &= self.piece_bitmap[self.one_convert(-self.state[0])]
            else:
                moves &= (self.piece_bitmap[self.one_convert(-self.state[0])] | 1 << self.pos_convert(self.state[2]))
            moves |= self.pone_move(start)
        if piece == 6:
            temp = moves & attacks
            moves ^= temp
        if check_flag:
            if piece != 6:
                moves &= check
        else:
            if piece == 6:
                if self.state[0] == 1:
                    if "K" in self.state[1] and moves & 1 << 61 != 0:
                        castle = self.check_castle(62, [97], attacks)
                        moves |= castle
                    if "Q" in self.state[1] and moves & 1 << 59 != 0:
                        castle = self.check_castle(58, [93, 92], attacks)
                        moves |= castle
                if self.state[0] == -1:
                    if "k" in self.state[1] and moves & 1 << 5 != 0:
                        castle = self.check_castle(6, [27], attacks)
                        moves |= castle
                    if "q" in self.state[1] and moves & 1 << 3 != 0:
                        castle = self.check_castle(2, [23, 22], attacks)
                        moves |= castle
            pass

        if piece != 6:
            attack =  attacks & (1 << self.pos_convert(start))
            if attack == 0:
                return moves
            king_dif = start - king
            if king_dif % 10 == 0:
                if king_dif > 0:
                    s_dir = "ver_plus"
                else:
                    s_dir = "ver_min"
            elif king_dif // 8 in [0, -1]:
                if king_dif > 0:
                    s_dir = "hor_plus"
                else:
                    s_dir = "hor_min"
            elif king_dif % 11 == 0:
                if king_dif > 0:
                    s_dir = "deg_45"
                else:
                    s_dir = "deg_225"
            elif king_dif % 9 == 0:
                if king_dif > 0:
                    s_dir = "deg_135"
                else:
                    s_dir = "deg_315"
            else:
                s_dir = None
            if s_dir is None:
                return moves
            piece_save = self.position[start]
            self.position[start] = 0
            dis_check = self.str_move(king, s_dir)
            attack = dis_check[0] & attack
            if attack != 0 and not dis_check[1] is None:
                attack = dis_check[1]
                if abs(self.position[attack]) in self.piece_checks[s_dir[:3]]:
                    moves &= dis_check[0]
            self.position[start] = piece_save
        return moves

    def check_castle(self, check, moves, attacks):
        check = 1 << check
        if attacks & check != 0:
            return 0
        for move in moves:
            if self.position[move] != 0:
                return 0
        return 1 << self.pos_convert(moves[0])

    def find_moves(self, start, piece):
        out = 0

        if piece == 6:
            for i in king_moves:
                move = start + i
                if self.bound_check(move):
                    continue
                out |= 1 << self.pos_convert(move)
        elif piece == 1:
            start_p = self.pos_convert(start)
            if not self.bound_check(start - 9 * self.state[0]):
                out |= 1 << start_p - 7 * self.state[0]
            if not self.bound_check(start - 11 * self.state[0]):
                out |= 1 << start_p - 9 * self.state[0]
        elif piece == 2:
            out |= self.kn_move(start)
        elif piece in [3, 4, 5]:
            for name in self.piece_moves[piece]:
                out |= self.str_move(start, name)[0]

        return out

    def str_move(self, pos, move):
        move = self.str_moves[move]
        out = 0
        end = None

        while True:
            pos += move
            if self.bound_check(pos):
                break
            elif self.position[pos] != 0:
                out |= 1 << self.pos_convert(pos)
                end = pos
                break
            out |= 1 << self.pos_convert(pos)
        return out, end

    def kn_move(self, pos):
        out = 0

        for move in knight_moves:
            new_pos = move + pos
            if self.bound_check(new_pos):
                continue
            out |= 1 << self.pos_convert(new_pos)

        return out

    def pone_move(self, start):
        out = 0
        one = start - self.state[0] * 10
        if self.position[one] == 0:
            out |= 1 << self.pos_convert(one)
            if start // 10 == 8 or start // 10 == 3:
                two = one - self.state[0] * 10
                if self.position[two] == 0:
                    out |= 1 << self.pos_convert(two)
        return out

game = Game()
start_t = time.perf_counter()
game.update()
print(f"Update: {time.perf_counter() - start_t}")

def update_loads(num, game):
    for _ in range(num):
        game.update()

#cProfile.run('game = Game("r1b1k2r/ppppnppp/2n2q2/2b5/2BNP3/2P1B3/PP3PPP/RN1QK2R b KQkq - 2 7"); update_loads(10 ** 4, game)')
