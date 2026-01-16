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

        self.ai = tk.Button(
            frm, text="Bot Move",
            command=lambda: self.eng_move(),
            height=3, width=6
        )
        self.ai.grid(column=8, row=1)
        self.ai_ev= tk.Button(
            frm, text="-",
            command=lambda: self.eng_evl(),
            height=3, width=6
        )
        self.ai_ev.grid(column=8, row=2)
        self.undo = tk.Button(
            frm, text="Undo",
            command=lambda: self.undo_move(),
            height=3, width=6
        )
        self.undo.grid(column=8, row=3)
        self.white = tk.Button(
            frm, text="White",
            command=lambda: self.view_bitmap(self.game.piece_bitmap[0]),
            height=3, width=6
        )
        self.white.grid(column=8, row=4)
        self.black = tk.Button(
            frm, text="Black",
            command=lambda: self.view_bitmap(self.game.piece_bitmap[1]),
            height=3, width=6
        )
        self.black.grid(column=9, row=4)
        self.white_rays= tk.Button(
            frm, text="W-rays",
            command=lambda: self.view_bitmap(self.game.make_attacks(self.game.state[0])),
            height=3, width=6
        )
        self.white_rays.grid(column=8, row=5)
        self.black_rays = tk.Button(
            frm, text="B-rays",
            command=lambda: self.view_bitmap(self.game.make_attacks(-self.game.state[0])),
            height=3, width=6
        )
        self.black_rays.grid(column=9, row=5)
        self.ray = tk.Button(
            frm, text="Ray",
            command=lambda: self.view_ray(),
            height=3, width=6
        )
        self.ray.grid(column=8, row=6)

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
        move = self.game.moves_made[-1]
        self.game.undo_move()
        self.game.update()
        self.update()

        i, j = self.revert(move.sqr1)
        self.buttons[i][j].config(bg="#B5C7EB")
        i, j = self.revert(move.sqr2)
        self.buttons[i][j].config(bg="#4682B4")

    def view_ray(self):
        if self.selected is None:
            return None
        self.view_bitmap(self.game.bitboards[self.convert(*self.selected)])

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
        move = make_move(self.game, 0)[0]
        self.ai_ev.config(
            text=str(round(move[1] * self.game.state[0] / 10 ** 3, 2)))
        print(self.revert(move[2]), self.revert(move[3][0]))
        self.game.update()
        i, j = self.revert(move[2])
        self.buttons[i][j].config(bg="#B5C7EB")
        i, j = self.revert(move[3][0])
        self.buttons[i][j].config(bg="#4682B4")

    def eng_move(self):
        start_t = time.perf_counter()
        move = make_move(self.game, 0)[0]
        print(f"Move time: {time.perf_counter() - start_t}")
        self.ai_ev.config(
            text=str(round(move[1] * self.game.state[0] / 10 ** 3, 2)))
        self.game.update()
        _ = self.game.move(move[2], move[3])
        self.game.update()
        self.update()
        i, j = self.revert(move[2])
        self.buttons[i][j].config(bg="#B5C7EB")
        i, j = self.revert(move[3][0])
        self.buttons[i][j].config(bg="#4682B4")

if __name__ == "__main__":
    from engine import make_move
    if len(sys.argv) == 1:
        Play()
    else:
        fen = sys.argv[1]
        print(fen)
        Play(fen=fen)
