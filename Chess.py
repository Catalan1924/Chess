import pygame, chess, sys, time, json, os
from math import inf

SQ = 60
WIDTH = HEIGHT = SQ * 8
BAR = 80
TOTAL_W = WIDTH + BAR
FPS = 30
START_TIME = 5 * 60  
PIECE_VAL = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
             chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}

pygame.init()
screen = pygame.display.set_mode((TOTAL_W, HEIGHT))
pygame.display.set_caption("Live-Score Chess – Maroon White")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 42)
small = pygame.font.SysFont(None, 28)

WHITE_SQ = (180, 149, 96)
BLACK_SQ = (119, 154, 88)
SELECT   = (186, 202, 68)
CHECK    = (207, 95, 95)
TEXT     = (255, 255, 255)
BG_BAR   = (50, 50, 50)
WHITE_PIECE_COLOR   = (255, 255, 255)   

LB_FILE = "leaderboard.json"


def load_lb():
    return json.load(open(LB_FILE)) if os.path.exists(LB_FILE) else {}
def save_lb(data):
    json.dump(data, open(LB_FILE, "w"), indent=2)


def main_menu():
    while True:
        screen.fill((30, 30, 30))
        title = font.render("Choose Mode", True, TEXT)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

        btn_human = pygame.Rect(200, 200, 200, 50)
        btn_ai    = pygame.Rect(200, 270, 200, 50)
        btn_quit  = pygame.Rect(200, 340, 200, 50)

        for btn, txt, col in [(btn_human,"Human vs Human",(70,180,70)),
                              (btn_ai,  "Human vs AI",   (70,70,180)),
                              (btn_quit,"Quit",          (180,70,70))]:
            pygame.draw.rect(screen, col, btn)
            screen.blit(small.render(txt, True, TEXT), (btn.x+20, btn.y+15))

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
        screen.blit(small.render("Really quit?  Y / N", True, TEXT), (box.x+40, box.y+40))
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_y:
                    pygame.quit(); sys.exit()
                elif e.key == pygame.K_n:
                    return


class Game:
    def __init__(self, vs_ai):
        self.board = chess.Board()
        self.vs_ai = vs_ai
        self.time_left = {chess.WHITE: START_TIME, chess.BLACK: START_TIME}
        self.last_tick = time.time()
        self.selected = None
        self.game_over = None
        self.lb = load_lb()
        self.captured = {chess.WHITE: 0, chess.BLACK: 0}
        self.last_fen = self.board.fen()

    def update_captured(self):
        """Add points whenever a piece disappears."""
        curr = {pt: len(self.board.pieces(pt, c)) for pt in PIECE_VAL for c in (chess.WHITE, chess.BLACK)}
        old = {pt: len(chess.Board(self.last_fen).pieces(pt, c)) for pt in PIECE_VAL for c in (chess.WHITE, chess.BLACK)}
        for pt in PIECE_VAL:
            if curr[pt] < old[pt]:

                captor = chess.BLACK if self.board.turn == chess.WHITE else chess.WHITE
                self.captured[captor] += PIECE_VAL[pt] * (old[pt] - curr[pt])
        self.last_fen = self.board.fen()

    def update_timer(self):
        if self.game_over:
            return
        now = time.time()
        elapsed = now - self.last_tick
        self.last_tick = now
        side = self.board.turn
        self.time_left[side] -= elapsed
        if self.time_left[side] <= 0:
            self.game_over = f"{'Black' if side == chess.WHITE else 'White'} wins on time!"

    def minimax(self, b, d, maximizing):
        if d == 0 or b.is_game_over():
            return 0, None
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

    def ai_move(self):
        _, move = self.minimax(self.board, 3, self.board.turn == chess.WHITE)
        if move:
            self.board.push(move)

    def run(self):
        while True:
            self.update_timer()
            self.update_captured()
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


            if not self.game_over and self.board.is_game_over():
                if self.board.is_checkmate():
                    winner = "Black" if self.board.turn == chess.WHITE else "White"
                    self.game_over = f"{winner} wins by checkmate!"
                elif self.board.is_stalemate() or self.board.is_insufficient_material():
                    self.game_over = "Draw!"
                if self.game_over:
                    winner_name = f"Player_{'Black' if self.captured[chess.WHITE] < self.captured[chess.BLACK] else 'White'}"
                    self.lb[winner_name] = self.lb.get(winner_name, 0) + max(self.captured.values())
                    save_lb(self.lb)

            self.draw()

    def draw(self):
        screen.fill((30, 30, 30))
        self.draw_board()
        self.draw_pieces()
        self.draw_bar()
        pygame.display.flip()

    def draw_board(self):
        for r in range(8):
            for c in range(8):
                color = WHITE_SQ if (r + c) % 2 == 0 else BLACK_SQ
                pygame.draw.rect(screen, color, (c * SQ, r * SQ, SQ, SQ))
        if self.selected is not None:
            col, row = chess.square_file(self.selected), 7 - chess.square_rank(self.selected)
            pygame.draw.rect(screen, SELECT, (col * SQ, row * SQ, SQ, SQ), 4)
        if not self.game_over and self.board.is_check():
            king_sq = self.board.king(self.board.turn)
            col, row = chess.square_file(king_sq), 7 - chess.square_rank(king_sq)
            pygame.draw.rect(screen, CHECK, (col * SQ, row * SQ, SQ, SQ), 4)

    def draw_pieces(self):
        fnt = pygame.font.SysFont(None, 48)
        for sq in chess.SQUARES:
            pc = self.board.piece_at(sq)
            if pc:
                lbl = pc.symbol().upper() if pc.color else pc.symbol()
                color = WHITE_PIECE_COLOR if pc.color else (0, 0, 0)
                img = fnt.render(lbl, True, color)
                x, y = chess.square_file(sq) * SQ + 10, (7 - chess.square_rank(sq)) * SQ + 10
                screen.blit(img, (x, y))

    def draw_bar(self):
        pygame.draw.rect(screen, BG_BAR, (WIDTH, 0, BAR, HEIGHT))
        def fmt(sec):
            m, s = divmod(int(max(sec, 0)), 60)
            return f"{m:02}:{s:02}"
        wt = small.render(fmt(self.time_left[chess.WHITE]), True, TEXT)
        bt = small.render(fmt(self.time_left[chess.BLACK]), True, TEXT)
        pw = small.render(f"W:{self.captured[chess.WHITE]}", True, TEXT)
        pb = small.render(f"B:{self.captured[chess.BLACK]}", True, TEXT)
        screen.blit(wt, (WIDTH + 5, 20))
        screen.blit(bt, (WIDTH + 5, HEIGHT - 60))
        screen.blit(pw, (WIDTH + 5, HEIGHT // 2 - 40))
        screen.blit(pb, (WIDTH + 5, HEIGHT // 2 - 10))
        if self.game_over:
            gm = small.render(self.game_over, True, (255, 100, 100))
            screen.blit(gm, (WIDTH + 5, HEIGHT // 2 + 20))

# ---------- ENTRY ----------
if __name__ == "__main__":
    vs_ai = main_menu()
    Game(vs_ai).run()