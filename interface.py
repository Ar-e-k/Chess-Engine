from copy import deepcopy as dp
import tkinter as tk
from tkinter import ttk
import numpy as np

from game import Game, fen_translate
from engine import make_move

class Play:

    def __init__(self):
        self.game = Game()
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
        input()

    def move(self, i, j):
        if self.selected is None:
            if self.check_pos((i, j)):
                self.selected = (i, j)
                self.buttons[i][j].config(bg="#008000")
        else:
            flag = self.game.move(self.selected, (i, j))
            if flag:
                self.game.update()
                x, y = self.selected
                self.buttons[i][j].config(text=self.get_text((i, j)))
                self.buttons[x][y].config(text="")
                self.selected = None
        self.update()

    def update(self):
        for i, row in enumerate(self.buttons):
            for j, but in enumerate(row):
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
                    if np.any(np.all((i, j) == np.array(
                                self.game.possible_moves[self.selected]), axis=1)):
                        col = "#0BDA51"
                self.buttons[i][j].config(bg=col)

        check = self.game.check_check()
        for ch in check:
            i, j = ch[-1]
            self.buttons[i][j].config(bg="#CD1C18")

        if not self.selected is None:
            i, j = self.selected
            col = "#008000"
            self.buttons[i][j].config(bg=col)

    def check_pos(self, pos):
        if pos in self.game.possible_moves:
            if len(self.game.possible_moves[pos]) != 0:
                return True
        return False

    def get_text(self, pos):
        i = self.game.position[pos]
        text = fen_translate[abs(i)]
        if i > 0:
            text = text.upper()
        return text

def convert(pos):
    row = np.int64(ord(pos[0]) - 97)
    col = 8 - np.int64(pos[1])
    return col, row

def play_old():
    game = Game()
    flag = True
    while True:
        if flag:
            print(game.position)
            game.update()
        move = input("Play: ").split(" ")
        flag = game.move(convert(move[0]), convert(move[1]))

def play_bot():
    game = Game()
    flag = True
    bot = False
    while True:
        if flag:
            game.update()
        if bot:
            move = make_move(game)[0]
            move = (move[2], tuple(move[3]))
            bot = not(bot)
        else:
            print(game.position)
            move = input("Play: ").split(" ")
            move = (convert(move[0]), convert(move[1]))
            bot = not(bot)

        flag = game.move(*move)

if __name__ == "__main__":
    Play()
    #play_bot()
