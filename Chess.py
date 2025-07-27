import pygame, chess, sys, time, json, os
from math import inf

# ---------- CONFIG ----------
SQ = 60
WIDTH = HEIGHT = SQ * 8
BAR = 80
TOTAL_W = WIDTH + BAR
FPS = 30
START_TIME = 3 * 60

pygame.init()
screen = pygame.display.set_mode((TOTAL_W, HEIGHT))
pygame.display.set_caption("Live-Score Chess")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 42)
small = pygame.font.SysFont(None, 28)

WHITE_S = (235, 235, 210)
BLACK_S = (119, 154, 88)
SELECT = (186, 202, 68)
CHECK = (207, 95, 95)
TEXT = (255, 255, 255)
BG_BAR = (50, 50, 50)

LB_FILE = "leaderboard.json"

# ---------- UTIL ----------
def load_lb():
    return json.load(open(LB_FILE)) if os.path.exists(LB_FILE) else {}

def save_lb(data):
    json.dump(data, open(LB_FILE, "w"), indent=2)

# ---------- MAIN MENU ----------
def main_menu():
    while True:
        screen.fill((30, 30, 30))
        title = font.render("Choose Mode", True, TEXT)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

        btn_human = pygame.Rect(200, 200, 200, 50)
        btn_ai    = pygame.Rect(200, 270, 200, 50)
        btn_quit  = pygame.Rect(200, 340, 200, 50)

        pygame.draw.rect(screen, (70, 180, 70), btn_human)
        pygame.draw.rect(screen, (70, 70, 180), btn_ai)
        pygame.draw.rect(screen, (180, 70, 70), btn_quit)

        screen.blit(small.render("Human vs Human", True, TEXT), (btn_human.x+20, btn_human.y+15))
        screen.blit(small.render("Human vs AI", True, TEXT),    (btn_ai.x+35, btn_ai.y+15))
        screen.blit(small.render("Quit", True, TEXT),           (btn_quit.x+70, btn_quit.y+15))

        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif e.type == pygame.MOUSEBUTTONDOWN:
                mx, my = e.pos
                if btn_human.collidepoint(mx, my):
                    return False
                elif btn_ai.collidepoint(mx, my):
                    return True
                elif btn_quit.collidepoint(mx, my):
                    confirm_quit()

def confirm_quit():
    box = pygame.Rect(WIDTH//2-150, HEIGHT//2-50, 300, 100)
    while True:
        screen.fill((30, 30, 30))
        pygame.draw.rect(screen, (100, 0, 0), box)
        t1 = small.render("Really quit?  Y / N", True, TEXT)
        screen.blit(t1, (box.x+40, box.y+40))
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_y:
                    pygame.quit(); sys.exit()
                elif e.key == pygame.K_n:
                    return

# ---------- GAME ----------
class Game:
    def __init__(self, vs_ai):
        self.board = chess.Board()
        self.vs_ai = vs_ai
        self.time_left = {chess.WHITE: START_TIME, chess.BLACK: START_TIME}
        self.last_tick = time.time()
        self.selected = None
        self.game_over = None
        self.winner_side = None
        self.lb = load_lb()
        self.initial_material = self.material_value()

    def material_value(self):
        v = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}
        return sum(len(self.board.pieces(pt, c)) * v[pt]
                   for pt in v for c in (chess.WHITE, chess.BLACK))

    def update_timer(self):
        if self.game_over:
            return
        now = time.time()
        elapsed = now - self.last_tick
        self.last_tick = now
        side = self.board.turn
        self.time_left[side] -= elapsed
        if self.time_left[side] <= 0:
            self.winner_side = "black" if side == chess.WHITE else "white"
            self.game_over = f"{self.winner_side.capitalize()} wins on time!"

    def live_points(self, color):
        """Real-time material difference vs start."""
        curr = self.material_value()
        diff = self.initial_material - curr
        return diff if color == chess.WHITE else -diff

    def minimax(self, b, d, maximizing):
        if d == 0 or b.is_game_over():
            return self.evaluate_board(b), None
        best = None
        if maximizing:
            max_eval = float('-inf')
            for m in b.legal_moves:
                b.push(m)
                val, _ = self.minimax(b, d-1, False)
                b.pop()
                if val > max_eval:
                    max_eval, best = val, m
            return max_eval, best
        else:
            min_eval = float('inf')
            for m in b.legal_moves:
                b.push(m)
                val, _ = self.minimax(b, d-1, True)
                b.pop()
                if val < min_eval:
                    min_eval, best = val, m
            return min_eval, best

    def evaluate_board(self, b):
        if b.is_checkmate():
            return float('-inf') if b.turn else float('inf')
        v = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}
        score = 0
        for pt in v:
            score += len(b.pieces(pt, chess.WHITE)) * v[pt]
            score -= len(b.pieces(pt, chess.BLACK)) * v[pt]
        return score

    def ai_move(self):
        _, move = self.minimax(self.board, 3, self.board.turn == chess.WHITE)
        if move:
            self.board.push(move)

    def run(self):
        clock = pygame.time.Clock()
        while True:
            clock.tick(30)
            self.update_timer()

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        return
                    elif e.key == pygame.K_s:
                        with open("game.pgn", "w") as f:
                            f.write(str(chess.pgn.Game.from_board(self.board)))
                elif e.type == pygame.MOUSEBUTTONDOWN and not self.game_over:
                    x, y = e.pos
                    if x >= WIDTH:
                        continue
                    sq = chess.square(x // SQ, 7 - (y // SQ))
                    if self.selected is None:
                        if self.board.piece_at(sq) and self.board.color_at(sq) == self.board.turn:
                            self.selected = sq
                    else:
                        move = chess.Move(self.selected, sq)
                        if move in self.board.legal_moves:
                            self.board.push(move)
                            self.selected = None
                            if self.vs_ai and not self.board.is_game_over() and not self.game_over:
                                self.ai_move()

            # Check game end
            if not self.game_over and self.board.is_game_over():
                if self.board.is_checkmate():
                    self.winner_side = "black" if self.board.turn == chess.WHITE else "white"
                    self.game_over = f"{self.winner_side.capitalize()} wins by checkmate!"
                elif self.board.is_stalemate() or self.board.is_insufficient_material():
                    self.game_over = "Draw!"
                if self.winner_side:
                    name = f"Player_{self.winner_side}"
                    self.lb[name] = self.lb.get(name, 0) + 1
                    save_lb(self.lb)

            self.draw()

    def draw(self):
        screen.fill((30, 30, 30))
        draw_board(self.board, self.selected, self.game_over)
        draw_pieces(self.board)
        draw_bar(self.time_left, self.game_over, self.live_points)
        pygame.display.flip()

# ---------- DRAW HELPERS ----------
def draw_board(brd, sel, over):
    for r in range(8):
        for c in range(8):
            color = WHITE_S if (r + c) % 2 == 0 else BLACK_S
            pygame.draw.rect(screen, color, (c * SQ, r * SQ, SQ, SQ))
    if sel is not None:
        col, row = chess.square_file(sel), 7 - chess.square_rank(sel)
        pygame.draw.rect(screen, SELECT, (col * SQ, row * SQ, SQ, SQ), 4)
    if not over and brd.is_check():
        king_sq = brd.king(brd.turn)
        col, row = chess.square_file(king_sq), 7 - chess.square_rank(king_sq)
        pygame.draw.rect(screen, CHECK, (col * SQ, row * SQ), 4)

def draw_pieces(brd):
    fnt = pygame.font.SysFont(None, 48)
    for sq in chess.SQUARES:
        pc = brd.piece_at(sq)
        if pc:
            lbl = pc.symbol().upper() if pc.color else pc.symbol()
            color = (0, 0, 0) if pc.color else (255, 255, 255)
            img = fnt.render(lbl, True, color)
            x, y = chess.square_file(sq) * SQ + 10, (7 - chess.square_rank(sq)) * SQ + 10
            screen.blit(img, (x, y))

def draw_bar(times, over, live_fn):
    pygame.draw.rect(screen, BG_BAR, (WIDTH, 0, BAR, HEIGHT))
    mini = small
    def fmt(sec):
        m, s = divmod(int(max(sec, 0)), 60)
        return f"{m:02}:{s:02}"
    wt = mini.render(fmt(times[chess.WHITE]), True, TEXT)
    bt = mini.render(fmt(times[chess.BLACK]), True, TEXT)
    pt_w = mini.render(f"W:{live_fn(chess.WHITE)}", True, TEXT)
    pt_b = mini.render(f"B:{live_fn(chess.BLACK)}", True, TEXT)
    screen.blit(wt, (WIDTH + 5, 20))
    screen.blit(bt, (WIDTH + 5, HEIGHT - 60))
    screen.blit(pt_w, (WIDTH + 5, HEIGHT // 2 - 40))
    screen.blit(pt_b, (WIDTH + 5, HEIGHT // 2 - 10))
    if over:
        gm = mini.render(over, True, (255, 100, 100))
        screen.blit(gm, (WIDTH + 5, HEIGHT // 2 + 20))

# ---------- ENTRY ----------
if __name__ == "__main__":
    vs_ai = main_menu()
    Game(vs_ai).run()