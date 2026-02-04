import random
import itertools
import pickle

from gamenew import print_bits, rev_list

random.seed(42)
big_num = (1 << 64) - 1

rook_dirs = [
    (-8, lambda x, _: x >= 0),
    (8, lambda x, _: x < 64),
    (-1, lambda x, old: old // 8 == x // 8),
    (1, lambda x, old: old // 8 == x // 8),
]

bishop_dirs = [
    (-9, lambda x, old: old % 8 > x % 8 and x >= 0),
    (9, lambda x, old: old % 8 < x % 8 and x < 64),
    (-7, lambda x, old: old % 8 < x % 8 and x >= 0),
    (7, lambda x, old: old % 8 > x % 8 and x < 64),
]

def rook(x, y, mn=1, mx=7):
    out = []
    for i in range(mn, mx):
        if i != x:
            out.append(i * 8 + y)
        if i != y:
            out.append(x * 8 + i)
    return out

def bish_sub(x, y, dx, dy, mn, mx):
    out = []
    x += dx
    y += dy
    while mn <= x < mx and mn <= y < mx:
        out.append(8 * x + y)
        x += dx
        y += dy
    return out

def bish(x, y, mn=1, mx=7):
    out = []
    for delta in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        out += bish_sub(x, y, *delta, mn, mx)
    return out

def gen_blocks(pos_list):
    out = []
    for ln in range(len(pos_list) + 1):
        for sub in itertools.combinations(pos_list, ln):
            pos = 0
            for i in sub:
                pos |= 1 << i
            out.append(pos)
    return out

def gen_all(mn=1, mx=7):
    rooks = []
    bishs = []
    for x in range(8):
        for y in range(8):
            rooks.append(gen_blocks(rook(x, y, mn, mx)))
            bishs.append(gen_blocks(bish(x, y, mn, mx)))
    return rooks, bishs

def gen_attacks(board, dirs):
    attacks = []
    for pos, blocks in enumerate(board):
        at = attacks_pos(blocks, pos, dirs)
        attacks.append(at)
    return attacks

def attacks_pos(block_list, pos, dirs, flag=True):
    out = []
    for block in block_list:
        part = 0
        for dr, cond in dirs:
            part |= attacks_sub(dr, cond, block, pos, flag)
        out.append(part)
    return out

def attacks_sub(dr, condition, block, pos, flag=True):
    out = 0
    new_pos = pos + dr
    while condition(new_pos, pos):
        cur = 1 << new_pos
        if flag:
            out |= cur
        if cur & block != 0:
            out |= cur
            break
        new_pos += dr
    return out

def find_all_magic(board, attacks, piece):
    magics = []
    tables = []
    shifts = []
    full = []
    for i in range(64):
        #print(f"Square: {i}")
        magic, table, shift = find_magic(board[i], attacks[i])
        magics.append(magic)
        tables.append(table)
        shifts.append(shift)
        fl_parts = piece(i // 8, i % 8)
        fl = 0
        for f in fl_parts:
            fl |= 1 << f
        full.append(fl)
    return magics, tables, shifts, full

def find_magic(blocks, attacks):
    shift = 64 - max(blocks).bit_count()
    takes = 0
    while True:
        takes += 1
        table = [None] * len(blocks)
        magic = random_dense()
        for pos, block in enumerate(blocks):
            idx = ((block * magic) & big_num)
            idx = idx >> shift
            if table[idx] is None:
                table[idx] = attacks[pos]
            elif table[idx] == attacks[pos]:
                pass
            else:
                break
        else:
            #print(f"Found on take: {takes}")
            break
    return magic, table, shift

def random_dense():
    magic_bits = random.choices(["0", "1"], weights=[5, 1], k=63)
    magic = ""
    magic = magic.join(magic_bits)
    magic = int(magic, 2)
    if magic < 2 ** 60:
        return random_dense()
    return magic

def test_magic(board, attacks, tables, magics, shifts):
    for pos, blocks in enumerate(board):
        shift = shifts[pos]
        magic = magics[pos]
        table = tables[pos]
        attack = attacks[pos]
        for pos2, block in enumerate(blocks):
            idx = ((block * magic) & big_num) >> shift
            if attack[pos2] != table[idx]:
                print(pos, pos2, idx)
                print("Error")
                return False
    return True

def make_magic(name):
    #bishop_magic, rook_magic = None, None
    rook_board, bishop_board = gen_all()
    bishop_attacks = gen_attacks(bishop_board, bishop_dirs)
    bishop_magic = find_all_magic(bishop_board, bishop_attacks, bish)
    rook_attacks = gen_attacks(rook_board, rook_dirs)
    rook_magic = find_all_magic(rook_board, rook_attacks, rook)
    #cols = find_all_blocks()
    with open(name, "wb") as fil:
        pickle.dump((bishop_magic, rook_magic), fil)
    print("Save Completed")

def find_all_blocks():
    blocks = []
    boards = gen_all(0, 8)
    for pos in range(64):
        blocks.append(find_blocks(pos, boards[0][pos], boards[1][pos]))
    return blocks

def find_blocks(pos, b1, b2):
    blocks = []
    b1 = attacks_pos(b1, pos, rook_dirs, False)
    b2 = attacks_pos(b2, pos, bishop_dirs, False)
    for i in set(b1):
        for j in set(b2):
            blocks.append(i | j)
    blockss = list(set(blocks))
    out = {}
    for i in blocks:
        out[i] = find_indecies(i)
    return out

def find_indecies(num):
    out = []
    while num:
        lsb = num & -num
        pos = lsb.bit_length() - 1
        out.append(rev_list[pos])
        num ^= lsb
    return out
