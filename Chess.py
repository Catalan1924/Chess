import pygame, chess, sys, time, json, os
from math import inf

# ---------- CONFIG ----------
SQ = 60
WIDTH = HEIGHT = SQ * 8
BAR = 60
TOTAL_W = WIDTH + BAR
FPS = 30
START_TIME = 3 * 60

pygame.init()
screen = pygame.display.set_mode((TOTAL_W, HEIGHT))
pygame.display.set_caption("Chess – Timer + Leaderboard")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 42)
small_font = pygame.font.SysFont(None, 28)
WHITE_S = (235, 235, 210)
BLACK_S = (119, 154, 88)
SELECT = (186, 202, 68)
CHECK = (207, 95, 95)
BG_BAR = (50, 50, 50)
TEXT = (255, 255, 255)

# ---------- BOARD ----------
board = chess.Board()
selected = None
ai_enabled = False
game_over = None
winner_side = None  # 'white' / 'black'

# ---------- TIMER ----------
time_left = {chess.WHITE: START_TIME, chess.BLACK: START_TIME}
last_tick = time.time()

# ---------- LEADERBOARD ----------
LB_FILE = "leaderboard.json"
leaderboard = {}

def load_lb():
    global leaderboard
    if os.path.exists(LB_FILE):
        with open(LB_FILE) as f:
            leaderboard = json.load(f)

def save_lb():
    with open(LB_FILE, "w") as f:
        json.dump(leaderboard, f, indent=2)

def add_win(name):
    leaderboard[name] = leaderboard.get(name, 0) + 1
    save_lb()

def show_leaderboard_popup():
    """Simple blocking popup until user presses ESC or ENTER."""
    load_lb()
    sorted_lb = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)[:10]
    popup = True
    while popup:
        screen.fill((30, 30, 30))
        title = small_font.render("Leaderboard (ESC to close)", True, TEXT)
        screen.blit(title, (20, 20))
        for idx, (name, pts) in enumerate(sorted_lb, 1):
            line = small_font.render(f"{idx}. {name}  –  {pts}", True, TEXT)
            screen.blit(line, (20, 60 + idx * 30))
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_RETURN)):
                popup = False

def prompt_name():
    """Simple input box for winner name."""
    name = ""
    prompt = True
    while prompt:
        screen.fill((30, 30, 30))
        txt1 = small_font.render("Enter winner name:", True, TEXT)
        txt2 = small_font.render(name + "|", True, TEXT)
        screen.blit(txt1, (50, HEIGHT // 2 - 30))
        screen.blit(txt2, (50, HEIGHT // 2 + 10))
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN and name.strip():
                    add_win(name.strip())
                    prompt = False
                elif e.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                elif e.unicode.isalnum() or e.unicode == " ":
                    name += e.unicode

# ---------- AI ----------
piece_values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
                chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}

def evaluate_board(b):
    if b.is_checkmate():
        return float('-inf') if b.turn else float('inf')
    score = 0
    for pt in piece_values:
        score += len(b.pieces(pt, chess.WHITE)) * piece_values[pt]
        score -= len(b.pieces(pt, chess.BLACK)) * piece_values[pt]
    return score

def minimax(b, depth, maximizing):
    if depth == 0 or b.is_game_over():
        return evaluate_board(b), None
    best_move = None
    if maximizing:
        max_eval = float('-inf')
        for move in b.legal_moves:
            b.push(move)
            val, _ = minimax(b, depth - 1, False)
            b.pop()
            if val > max_eval:
                max_eval, best_move = val, move
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in b.legal_moves:
            b.push(move)
            val, _ = minimax(b, depth - 1, True)
            b.pop()
            if val < min_eval:
                min_eval, best_move = val, move
        return min_eval, best_move

def ai_move():
    _, move = minimax(board, 3, board.turn == chess.WHITE)
    if move:
        board.push(move)

# ---------- GRAPHICS ----------
def draw_board():
    for r in range(8):
        for c in range(8):
            color = WHITE_S if (r + c) % 2 == 0 else BLACK_S
            pygame.draw.rect(screen, color, (c * SQ, r * SQ, SQ, SQ))

def draw_pieces():
    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece:
            label = piece.symbol().upper() if piece.color else piece.symbol()
            color = (0, 0, 0) if piece.color else (255, 255, 255)
            img = font.render(label, True, color)
            x, y = chess.square_file(sq) * SQ + 10, (7 - chess.square_rank(sq)) * SQ + 10
            screen.blit(img, (x, y))

def highlight():
    if selected is not None:
        col, row = chess.square_file(selected), 7 - chess.square_rank(selected)
        pygame.draw.rect(screen, SELECT, (col * SQ, row * SQ, SQ, SQ), 4)
    if not game_over and board.is_check():
        king_sq = board.king(board.turn)
        col, row = chess.square_file(king_sq), 7 - chess.square_rank(king_sq)
        pygame.draw.rect(screen, CHECK, (col * SQ, row * SQ, SQ, SQ), 4)

def draw_bar():
    pygame.draw.rect(screen, BG_BAR, (WIDTH, 0, BAR, HEIGHT))
    mini = small_font
    def fmt(sec):
        m, s = divmod(int(max(sec, 0)), 60)
        return f"{m:02}:{s:02}"
    wt = mini.render(fmt(time_left[chess.WHITE]), True, TEXT)
    bt = mini.render(fmt(time_left[chess.BLACK]), True, TEXT)
    screen.blit(wt, (WIDTH + 5, 20))
    screen.blit(bt, (WIDTH + 5, HEIGHT - 40))
    msg = mini.render("W" if board.turn == chess.WHITE else "B", True, TEXT)
    screen.blit(msg, (WIDTH + 5, HEIGHT // 2 - 10))
    if game_over:
        gm = mini.render(game_over, True, (255, 100, 100))
        screen.blit(gm, (WIDTH + 5, HEIGHT // 2 + 10))

def update_timer():
    global last_tick, game_over, winner_side
    if game_over:
        return
    now = time.time()
    elapsed = now - last_tick
    last_tick = now
    if board.turn in time_left:
        time_left[board.turn] -= elapsed
        if time_left[board.turn] <= 0:
            winner_side = "black" if board.turn == chess.WHITE else "white"
            game_over = f"{winner_side.capitalize()} wins on time!"

def coord_to_square(x, y):
    return chess.square(x // SQ, 7 - (y // SQ))

def main():
    global selected, ai_enabled, game_over, winner_side
    load_lb()
    while True:
        clock.tick(30)
        update_timer()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                elif e.key == pygame.K_a and not game_over:
                    ai_enabled = not ai_enabled
                elif e.key == pygame.K_s and not game_over:
                    with open("game.pgn", "w") as f:
                        f.write(str(chess.pgn.Game.from_board(board)))
                elif e.key == pygame.K_l:
                    show_leaderboard_popup()
            elif e.type == pygame.MOUSEBUTTONDOWN and not game_over:
                x, y = pygame.mouse.get_pos()
                if x >= WIDTH:
                    continue
                sq = coord_to_square(x, y)
                if selected is None:
                    if board.piece_at(sq) and board.color_at(sq) == board.turn:
                        selected = sq
                else:
                    move = chess.Move(selected, sq)
                    if move in board.legal_moves:
                        board.push(move)
                        selected = None
                        if ai_enabled and not board.is_game_over() and not game_over:
                            ai_move()
                    else:
                        selected = None

        # After move, check game end
        if not game_over and board.is_game_over():
            if board.is_checkmate():
                winner_side = "black" if board.turn == chess.WHITE else "white"
                game_over = f"{winner_side.capitalize()} wins by checkmate!"
            elif board.is_stalemate() or board.is_insufficient_material():
                game_over = "Draw!"
            if winner_side:
                prompt_name()

        draw_board()
        highlight()
        draw_pieces()
        draw_bar()
        pygame.display.flip()

if __name__ == "__main__":
    main()