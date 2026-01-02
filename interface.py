import numpy as np

from game import Game

def convert(pos):
    row = np.int64(ord(pos[0]) - 97)
    col = 8 - np.int64(pos[1])
    return col, row

def play():
    game = Game()
    game.update()
    flag = True
    while True:
        if flag:
            print(game.position)
        move = input("Play: ").split(" ")
        flag = game.move(convert(move[0]), convert(move[1]))

if __name__ == "__main__":
    play()
