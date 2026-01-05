import tkinter as tk
from tkinter import ttk

from game import Game, fen_translate

class Play:

    def __init__(self, game=None):
        if game is None:
            self.game = Game()
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

        self.undo = tk.Button(
            frm, text="Undo",
            command=lambda: self.undo_move(),
            height=3, width=6
        )
        self.undo.grid(column=8, row=3)

        input()

    def move(self, i, j):
        if self.selected is None:
            if self.check_pos((i, j)):
                self.selected = (i, j)
                self.buttons[i][j].config(bg="#008000")
        else:
            flag = self.game.move(self.convert(*self.selected), self.convert(i, j))
            if flag:
                self.game.update()
                x, y = self.selected
                self.buttons[i][j].config(text=self.get_text((i, j)))
                self.buttons[x][y].config(text="")
                self.selected = None
            else:
                self.selected = None
        self.update()

    def update(self):
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
                    if (self.convert(i, j) in
                                self.game.possible_moves[
                                    self.convert(*self.selected)]):
                        col = "#0BDA51"
                self.buttons[i][j].config(bg=col)

        check = self.game.check_check()
        for ch in check:
            i = ch[-1] // 10 - 2
            j = ch[-1] % 10 - 1
            self.buttons[i][j].config(bg="#CD1C18")

        if not self.selected is None:
            i, j = self.selected
            col = "#008000"
            self.buttons[i][j].config(bg=col)

    def check_pos(self, pos):
        pos = self.convert(*pos)
        if pos in self.game.possible_moves:
            if len(self.game.possible_moves[pos]) != 0:
                return True
        return False

    def convert(self, i, j):
        return (i + 2) * 10 + 1 + j

    def get_text(self, pos):
        pos = self.convert(*pos)
        i = self.game.position[pos]
        text = fen_translate[abs(i)]
        if i > 0:
            text = text.upper()
        return text

    def undo_move(self):
        self.game.undo_move()
        self.game.update()
        self.update()

if __name__ == "__main__":
    Play()
    #play_bot()
