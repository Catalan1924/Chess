import pygame, chess, sys, os
from math import inf


SQ = 60                  
WIDTH = HEIGHT = SQ * 8
FPS = 30
WHITE = (235, 235, 210)
BLACK = (119, 154, 88)
SELECT = (186, 202, 68)
CHECK = (207,  95,  95)
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT + 40))  
pygame.display.set_caption("Mini Chess – ESC to quit")
clock = pygame.time.Clock()

board = chess.Board()
selected = None         
ai_enabled = True     
dragging = None



def draw_board():
        for r in range(8):
            for c in range(8):
                color = WHITE if (r + c) % 2 == 0 else BLACK
                pygame.draw.rect(screen, color, (c * SQ, r * SQ, SQ, SQ))

def draw_pieces():
    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece:
            file = os.path.join("pieces", f"{piece.symbol()}.png")
            if not os.path.exists(file):

                font = pygame.font.SysFont(None, 48)
                label = piece.symbol().upper() if piece.color else piece.symbol()
                color = (0, 0, 0) if piece.color else (255, 255, 255)
                img = font.render(label, True, color)
            else:
                img = pygame.image.load(file)
                img = pygame.transform.scale(img, (SQ, SQ))
            x, y = chess.square_file(sq) * SQ, (7 - chess.square_rank(sq)) * SQ
            screen.blit(img, (x, y))

def highlight():
    if selected is not None:
        col, row = chess.square_file(selected), 7 - chess.square_rank(selected)
        pygame.draw.rect(screen, SELECT, (col * SQ, row * SQ, SQ, SQ), 4)
  
    if board.is_check():
        king_sq = board.king(board.turn)
        col, row = chess.square_file(king_sq), 7 - chess.square_rank(king_sq)
        pygame.draw.rect(screen, CHECK, (col * SQ, row * SQ, SQ, SQ), 4)