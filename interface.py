import sys
import time
import tkinter as tk
from tkinter import ttk

#from game import Game, fen_translate
from gamenew import Game, fen_translate

class Play:

    def __init__(self, game=None, fen=None):
        if game is None:
            if fen is None:
                self.game = Game()
            else:
                self.game = Game(fen)
        else:
            self.game = game
        self.game.update()

        try:
            self.engine = Engine()
        except:
            pass

        root = tk.Tk()
        frm = tk.ttk.Frame(root, padding=10)
        frm.grid()
        flag = True

        self.selected = None

        self.buttons = []

        for i in range(8):
            row = []
            for j in range(8):
                if (i + j) % 2 == 0:
                    col = "#704214"
                else:
                    col = "#EDE8D0"

                row.append(tk.Button(
                    frm, text=self.get_text((i, j)),
                    command=lambda i=i, j=j: self.move(i, j),
                    bg=col,
                    height=3, width=3
                ))
                row[j].grid(column=j, row=i)
            self.buttons.append(row)

        self.update()
        self.evl = None

        self.hsh = tk.Button(
            frm, text="Hash",
            command=lambda: print(self.game.hsh),
            height=3, width=6
        )
        self.hsh.grid(column=8, row=0)
        self.fen = tk.Button(
            frm, text="Fen",
            command=lambda: print(self.game.fen()),
            height=3, width=6
        )
        self.fen.grid(column=9, row=0)
        self.undo = tk.Button(
            frm, text="Undo",
            command=lambda: self.undo_move(),
            height=3, width=6
        )
        self.undo.grid(column=10, row=0)

        self.ai = tk.Button(
            frm, text="Bot Move",
            command=lambda: self.eng_move(),
            height=3, width=6
        )
        self.ai.grid(column=8, row=1)
        self.ai_ev = tk.Button(
            frm, text="-",
            command=lambda: self.eng_evl_dis(),
            height=3, width=6
        )
        self.ai_ev.grid(column=9, row=1)

        self.ai_all = tk.Button(
            frm, text="B-Eval",
            command=lambda: self.eng_evl_all(),
            height=3, width=6
        )
        self.ai_all.grid(column=8, row=2)
        self.ai_worst = tk.Button(
            frm, text="W-Eval",
            command=lambda: self.eng_evl_all(False),
            height=3, width=6
        )
        self.ai_worst.grid(column=9, row=2)
        self.ai_piece = tk.Button(
            frm, text="P-Eval",
            command=lambda: self.eng_evl_piece(),
            height=3, width=6
        )
        self.ai_piece.grid(column=10, row=2)

        self.pones = tk.Button(
            frm, text="Pones",
            command=lambda: self.view_bitmap(self.game.piece_bitmap[3]),
            height=3, width=6
        )
        self.pones.grid(column=8, row=3)
        self.knights = tk.Button(
            frm, text="Knights",
            command=lambda: self.view_bitmap(self.game.piece_bitmap[4]),
            height=3, width=6
        )
        self.knights.grid(column=9, row=3)

        self.diag = tk.Button(
            frm, text="Diag",
            command=lambda: self.view_bitmap(self.game.piece_bitmap[5]),
            height=3, width=6
        )
        self.diag.grid(column=8, row=4)
        self.strg = tk.Button(
            frm, text="Straight",
            command=lambda: self.view_bitmap(self.game.piece_bitmap[6]),
            height=3, width=6
        )
        self.strg.grid(column=9, row=4)

        self.white = tk.Button(
            frm, text="White",
            command=lambda: self.view_bitmap(self.game.piece_bitmap[0]),
            height=3, width=6
        )
        self.white.grid(column=8, row=5)
        self.black = tk.Button(
            frm, text="Black",
            command=lambda: self.view_bitmap(self.game.piece_bitmap[1]),
            height=3, width=6
        )
        self.black.grid(column=9, row=5)

        self.white_rays= tk.Button(
            frm, text="W-rays",
            command=lambda: self.view_bitmap(self.game.make_attacks(self.game.state[0])),
            height=3, width=6
        )
        self.white_rays.grid(column=8, row=6)
        self.black_rays = tk.Button(
            frm, text="B-rays",
            command=lambda: self.view_bitmap(self.game.make_attacks(-self.game.state[0])),
            height=3, width=6
        )
        self.black_rays.grid(column=9, row=6)

        self.ray = tk.Button(
            frm, text="Ray",
            command=lambda: self.view_piece_bitmap(self.game.bitboards),
            height=3, width=6
        )
        self.ray.grid(column=8, row=7)

        self.caps = tk.Button(
            frm, text="Caps",
            command=lambda: self.view_piece_bitmap(self.game.capboards),
            height=3, width=6
        )
        self.caps.grid(column=9, row=7)

        input()

    def move(self, i, j):
        if self.selected is None:
            if self.check_pos((i, j)):
                self.selected = (i, j)
                self.buttons[i][j].config(bg="#008000")
        else:
            flag = self.game.move(self.convert(*self.selected), (self.convert(i, j), True))
            flag = flag or self.game.move(self.convert(*self.selected), (self.convert(i, j), False))
            if flag:
                self.evl = None
                self.game.update()
                x, y = self.selected
                self.buttons[i][j].config(text=self.get_text((i, j)))
                self.buttons[x][y].config(text="")
                self.selected = None
            else:
                print(f"Illegal move: {self.convert(*self.selected), self.convert(i, j)}")
                self.selected = None
        self.update()

    def update(self):
        self.possible_moves = self.game.possible_moves_out()
        for i, row in enumerate(self.buttons):
            for j, but in enumerate(row):
                self.buttons[i][j].config(text=self.get_text((i, j)))
                if (i + j) % 2 == 0:
                    col = "#EDE8D0"
                else:
                    col = "#704214"
                if self.check_pos((i, j)) and self.selected is None:
                    if (i + j) % 2 == 0:
                        col = "#00CEC8"
                    else:
                        col = "#005451"
                elif not self.selected is None:
                    if ((self.convert(i, j), True) in
                                self.possible_moves[
                                    self.convert(*self.selected)]):
                        col = "#0BDA51"
                    elif ((self.convert(i, j), False) in
                                self.possible_moves[
                                    self.convert(*self.selected)]):
                        col = "#E40078"
                self.buttons[i][j].config(bg=col)

        check = self.game.return_check()
        for ch in check:
            i = ch // 10 - 2
            j = ch % 10 - 1
            self.buttons[i][j].config(bg="#CD1C18")

        if not self.selected is None:
            i, j = self.selected
            col = "#008000"
            self.buttons[i][j].config(bg=col)

    def check_pos(self, pos):
        pos = self.convert(*pos)
        if pos in self.possible_moves:
            if len(self.possible_moves[pos]) != 0:
                return True
        return False

    def convert(self, i, j):
        return (i + 2) * 10 + 1 + j

    def revert(self, pos):
        return pos // 10 - 2, pos % 10 - 1

    def get_text(self, pos):
        pos = self.convert(*pos)
        i = self.game.position[pos]
        text = fen_translate[abs(i)]
        if i > 0:
            text = text.upper()
        return text

    def undo_move(self):
        self.evl = None
        move = self.game.moves_made[-1]
        self.game.undo_move()
        self.game.update()
        self.update()

        i, j = self.revert(move.sqr1)
        self.buttons[i][j].config(bg="#B5C7EB")
        i, j = self.revert(move.sqr2)
        self.buttons[i][j].config(bg="#4682B4")

    def view_piece_bitmap(self, bmap):
        if self.selected is None:
            return None
        self.view_bitmap(bmap[self.convert(*self.selected)])

    def view_bitmap(self, bmap):
        row = []
        for i, row in enumerate(self.buttons):
            for j, but in enumerate(row):
                val = f"{bmap:64b}"[(8 - i) * 8 - j - 1]
                if val == "1":
                    col = "#7363B7"
                else:
                    col = "#704214"
                self.buttons[i][j].config(bg=col)

    def eng_evl(self):
        self.update()
        if self.evl is None:
            start_t = time.perf_counter()
            moves = self.engine.make_move(self.game, 1)
            print(f"Move time: {time.perf_counter() - start_t}")
            self.evl = moves
        else:
            moves = self.evl
        self.ai_ev.config(
            text=str(round(moves[0][1] * self.game.state[0], 2)))
        self.game.update()
        return moves

    def eng_evl_all(self, best=True):
        moves = self.eng_evl()
        used = []
        for move in moves:
            i, j = self.revert(move[2])
            if (i, j) in used:
                continue
            if best:
                used.append((i, j))
            self.buttons[i][j].config(
                text=self.get_text((i, j)) + "\n" + str(round(move[1] * self.game.state[0], 2)))

    def eng_evl_piece(self):
        if self.selected is None:
            return None
        moves = self.eng_evl()
        for move in moves:
            i, j = self.revert(move[2])
            if (i, j) == self.selected:
                i, j = self.revert(move[3][0])
                self.buttons[i][j].config(bg="#50C878")
                self.buttons[i][j].config(
                    text=str(round(move[1] * self.game.state[0], 2)))

    def eng_evl_dis(self):
        move = self.eng_evl()[0]
        print(self.revert(move[2]), self.revert(move[3][0]))
        i, j = self.revert(move[2])
        self.buttons[i][j].config(bg="#B5C7EB")
        i, j = self.revert(move[3][0])
        self.buttons[i][j].config(bg="#4682B4")

    def eng_move(self):
        move = self.eng_evl()[0]
        _ = self.game.move(move[2], move[3])
        self.game.update()
        self.update()
        i, j = self.revert(move[2])
        self.buttons[i][j].config(bg="#B5C7EB")
        i, j = self.revert(move[3][0])
        self.buttons[i][j].config(bg="#4682B4")
        self.evl = None

if __name__ == "__main__":
    from engine import Engine
    if len(sys.argv) == 1:
        Play()
    else:
        fen = sys.argv[1]
        print(fen)
        Play(fen=fen)
