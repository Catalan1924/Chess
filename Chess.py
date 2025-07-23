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

piece_value = { chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
                chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0 }

def highlight():
    if selected is not None:
        col, row = chess.square_file(selected), 7 - chess.square_rank(selected)
        pygame.draw.rect(screen, SELECT, (col * SQ, row * SQ, SQ, SQ), 4)
  
    if board.is_check():
        king_sq = board.king(board.turn)
        col, row = chess.square_file(king_sq), 7 - chess.square_rank(king_sq)
        pygame.draw.rect(screen, CHECK, (col * SQ, row * SQ, SQ, SQ), 4)

def evaluate(b):
    if b.is_checkmate():
        return -inf if b.turn else inf
    if b.is_stalemate() or b.is_insufficient_material():
        return 0
    score = 0
    for sq in chess.SQUARES:
        p = b.piece_at(sq)
        if p:
            val = piece_value[p.piece_type]
            score += val if p.color == chess.WHITE else -val
    return score

def minimax(b, depth, alpha, beta, maximizing):
    if depth == 0 or b.is_game_over():
        return evaluate(b)
    if maximizing:
        max_eval = -inf
        for move in b.legal_moves:
            b.push(move)
            val = minimax(b, depth-1, alpha, beta, False)
            b.pop()
            max_eval = max(max_eval, val)
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = inf
        for move in b.legal_moves:
            b.push(move)
            val = minimax(b, depth-1, alpha, beta, True)
            b.pop()
            min_eval = min(min_eval, val)
            beta = min(beta, val)
            if beta <= alpha:
                break
        return min_eval

def ai_move():
    best_score, best_move = -inf, None
    for move in board.legal_moves:
        board.push(move)
        score = minimax(board, 3, -inf, inf, board.turn == chess.BLACK)
        board.pop()
        if score > best_score:
            best_score, best_move = score, move
    if best_move:
        board.push(best_move)
def export_pgn():
    game = chess.pgn.Game.from_board(board)
    with open("game.pgn", "w") as f:
        f.write(str(game))
    print("📄 game.pgn saved")

def coord_to_square(x, y):
    file = x // SQ
    rank = 7 - (y // SQ)
    return chess.square(file, rank)

def main():
    global selected, ai_enabled
    while True:
        clock.tick(FPS)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                elif e.key == pygame.K_a:
                    ai_enabled = not ai_enabled
                    print("AI" if ai_enabled else "Human")
                elif e.key == pygame.K_s:
                    export_pgn()
            elif e.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if y >= HEIGHT: continue   # ignore bottom strip
                sq = coord_to_square(x, y)
                if selected is None:
                    if board.piece_at(sq) and board.color_at(sq) == board.turn:
                        selected = sq
                else:
                    move = chess.Move(selected, sq)
                    if move in board.legal_moves:
                        board.push(move)
                        selected = None
                        if ai_enabled and not board.is_game_over():
                            ai_move()
                    else:
                        selected = None

        draw_board()
        highlight()
        draw_pieces()

        pygame.draw.rect(screen, (50, 50, 50), (0, HEIGHT, WIDTH, 40))
        font = pygame.font.SysFont(None, 28)
        msg = f"Turn: {'White' if board.turn else 'Black'}  |  AI: {'ON' if ai_enabled else 'OFF'}"
        if board.is_checkmate():
            msg = "Checkmate!"
        elif board.is_stalemate():
            msg = "Stalemate!"
        screen.blit(font.render(msg, True, (255, 255, 255)), (10, HEIGHT + 10))

        pygame.display.flip()

if __name__ == "__main__":
    os.makedirs("pieces", exist_ok=True) 
    main()      