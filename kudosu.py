#!/usr/bin/env
import pygame
import requests


class SugokuAPI:
    EZ = "easy"
    MED = "medium"
    HARD = "hard"
    RAND = "random"

    @classmethod
    def format_board(cls, board):
        formated_board = []
        for block in board:
            formated_board.append([block[x:x+3]
                                  for x in range(0, len(block), 3)])
        return formated_board

    @classmethod
    def get_board(cls, difficulty=EZ):
        res = requests.get(
            f"https://sugoku.herokuapp.com/board?difficulty={difficulty}")
        board = res.json().get("board")
        solved = cls.get_solved(board)
        return cls.format_board(board), cls.format_board(solved)

    @classmethod
    def get_solved(cls, board):
        data = {"board": repr(board)}
        res = requests.post("https://sugoku.herokuapp.com/solve", data=data,
                            headers={"Content-Type": "application/x-www-form-urlencoded"})

        solution = res.json().get("solution")
        return solution


window_width, window_height = 864, 864
GRID = window_height//9


class COLORS:
    BLACK = (0, 0, 0)
    SOME_GREY = (236, 236, 236)
    DARKER_GREY = (169, 169, 169)
    EVEN_DARKER_GREY = (52, 52, 52)
    RED = (255, 0, 0)


pygame.init()
font = pygame.font.SysFont(None, 96)
bigger_font = pygame.font.SysFont(None, 96*2)
screen = pygame.display.set_mode((window_width, window_height))
clock = pygame.time.Clock()


class Cell(pygame.Surface):
    def __init__(self, pos: tuple, val, locked: bool = False):
        super().__init__(size=(GRID, GRID))
        self.pos = pos
        self.val = val
        self.locked = locked
        self.render_stuff()

    def set_val(self, val):
        if not self.locked:
            self.val = val
            self.render_stuff()

    def render_stuff(self):
        color = COLORS.EVEN_DARKER_GREY if self.locked else COLORS.BLACK
        self.fill(color)
        if self.val:
            text = font.render(str(self.val), True, COLORS.SOME_GREY)
        else:
            text = font.render("", True, COLORS.SOME_GREY)
        self.blit(text, (GRID//3, GRID//5))
        pygame.draw.rect(self, COLORS.SOME_GREY, self.get_rect(), 1)


class Block(pygame.Surface):
    def __init__(self, pos: tuple, values: list[list]):
        super().__init__(size=(GRID*3, GRID*3))
        self.pos = pos

        self.cells = self.generate_cells(values)
        self.render_cells()

    def generate_cells(self, values: list[list]):
        cells = []

        for y, row in enumerate(values):
            r = []
            for x, val in enumerate(row):
                r.append(Cell((x*GRID, y*GRID), val, bool(val)))
            cells.append(r)

        return cells

    def render_cells(self):
        cell: Cell
        for row in self.cells:
            for cell in row:
                self.blit(cell, cell.pos)

        pygame.draw.rect(self, COLORS.SOME_GREY, self.get_rect(), 5)


class Kudosu:
    def __init__(self, board, solution):
        self.solution = solution
        self.blocks = self.generate_blocks(board)
        self.selected = None
        self.selected_pos = None

    def validate(self):
        board = []
        block: Block
        for block in self.blocks:
            bl = []
            for row in block.cells:
                cell: Cell
                rl = []
                for cell in row:
                    rl.append(cell.val)
                bl.append(rl)

            board.append(bl)

        return board == self.solution

    def generate_blocks(self, board):
        blocks = []
        x = 0
        y = 0

        for block in board:
            blocks.append(Block((x*GRID*3, y*GRID*3), block))
            x += 1
            if x > 2:
                x = 0
                y += 1

        return blocks

    def set_selected_val(self, val):
        if self.selected is not None:
            b, r, c = self.selected
            self.blocks[b].cells[r][c].set_val(val)
            self.refresh_blocks()

    def set_selected(self, click):
        mx, my = click
        for b, block in enumerate(self.blocks):
            block: Block
            for r, row in enumerate(block.cells):
                row: list[Cell]
                for c, cell in enumerate(row):
                    if cell.get_rect().collidepoint(mx-c*GRID-(b % 3)*GRID*3, my-r*GRID-(b // 3)*GRID*3):
                        # print(f"block: {b} cell: {c},{r}")
                        self.selected, self.selected_pos = (
                            b, r, c), (c*GRID+(b % 3)*GRID*3, r*GRID+(b // 3)*GRID*3)
                        return
        self.selected = None
        self.selected_pos = None

    def refresh_blocks(self):
        block: Block
        for block in self.blocks:
            block.render_cells()

    def draw(self):
        for block in self.blocks:
            screen.blit(block, block.pos)

        if self.selected is not None:
            pygame.draw.rect(screen, COLORS.RED, pygame.Rect(
                self.selected_pos[0], self.selected_pos[1], GRID, GRID), 3)

# test = font.render("1", True, (123, 123, 123))
# cell = Cell(pos=(0, 0), 0)


board, solution = SugokuAPI.get_board()

# print(board)
# print("==================")
# print(solution)

wintext = bigger_font.render("woooo", True, COLORS.SOME_GREY)

game = Kudosu(board, solution)
win = False
run = True
while run:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))

            elif pygame.K_KP_1 <= event.key <= pygame.K_KP_0:
                game.set_selected_val((event.key - pygame.K_KP_1+1) % 10)
                win = game.validate()
            elif pygame.K_0 <= event.key <= pygame.K_9:
                game.set_selected_val(event.key - pygame.K_0)
                win = game.validate()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            game.set_selected(pos)

    if win:
        run = False
        screen.fill(COLORS.BLACK)
        screen.blit(wintext, (240, window_height//2-64))

        pygame.display.flip()
        pygame.event.clear()
        while event := pygame.event.wait():
            if event.type in (pygame.QUIT, pygame.KEYDOWN):
                break

    screen.fill(COLORS.BLACK)

    game.draw()

    pygame.display.update()
    clock.tick(60)

pygame.quit()
