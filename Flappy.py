import random
import tkinter as tk

W, H = 420, 640
GROUND_H = 80

BIRD_X = 120
BIRD_SIZE = 22
GRAVITY = 0.55
FLAP_VELOCITY = -9.5
MAX_FALL_SPEED = 12

PIPE_W = 56
GAP_MIN = 130
GAP_MAX = 190
PIPE_SPEED = 3.6
SPAWN_EVERY_PIXELS = 260  # distance between pipe pairs

COLOR_BG = "#87CEEB"      # sky
COLOR_GROUND = "#8B5A2B"  # ground
COLOR_PIPE = "#2ecc71"
COLOR_BIRD = "#ffcc00"
COLOR_TEXT = "#1b1b1b"

class Flappy:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Flappy — Python/tkinter demo")
        root.resizable(False, False)

        self.canvas = tk.Canvas(
            root, width=W, height=H, bg=COLOR_BG, highlightthickness=0
        )
        self.canvas.pack()

        self.hud = tk.Label(
            root, text="Score: 0   [Space] flap   [P] pause   [R] restart",
            font=("Segoe UI", 12), fg=COLOR_TEXT, bg=COLOR_BG
        )
        self.hud.place(x=8, y=8)

        root.bind("<space>", self.flap)
        root.bind("<Key-p>", self.toggle_pause)
        root.bind("<Key-r>", self.restart)

        self.reset_game()
        self.loop()


    def reset_game(self):
        self.canvas.delete("all")
        self.paused = False
        self.game_over = False
        self.scroll_px = 0
        self.score = 0
        self.scored_pipes = set()

        # ground
        self.ground_y = H - GROUND_H
        self._draw_ground()

        # bird state
        self.bird_y = H // 2
        self.bird_vy = 0.0

        # pipes: list of dicts with x, gap_y, gap_h, ids
        self.pipes = []
        self.next_spawn_at = W + 120  # first pipe off-screen   to the right

        self._redraw_bird()
        self._update_hud()

    def restart(self, _=None):
        self.reset_game()

    def flap(self, _=None):
        if self.game_over:
            return
        self.bird_vy = FLAP_VELOCITY

    def toggle_pause(self, _=None):
        if self.game_over:
            return
        self.paused = not self.paused
        self._update_hud()
        if self.paused:
            self._overlay("PAUSED")
        else:
            self.canvas.delete("overlay")

    def loop(self):
        self.step()
        self.root.after(16, self.loop)  # ~60 FPS

    def step(self):
        if self.game_over or self.paused:
            return

        # physics
        self.bird_vy = min(MAX_FALL_SPEED, self.bird_vy + GRAVITY)
        self.bird_y += self.bird_vy

        # spawn pipes when needed
        if self.next_spawn_at <= W:
            self._spawn_pipe_pair()
            self.next_spawn_at += SPAWN_EVERY_PIXELS
        self.next_spawn_at -= PIPE_SPEED

        # move pipes
        for p in self.pipes:
            p["x"] -= PIPE_SPEED

        # remove offscreen pipes
        self.pipes = [p for p in self.pipes if p["x"] + PIPE_W > -10]

        # collisions
        if self._collides_ground() or self._collides_pipes():
            self._end_game()
            return

        # scoring: pass center of a pipe pair
        for p in self.pipes:
            if p["id"] not in self.scored_pipes and p["x"] + PIPE_W < BIRD_X:
                self.score += 1
                self.scored_pipes.add(p["id"])

        self._redraw()

    def _draw_ground(self):
        self.canvas.delete("ground")
        self.canvas.create_rectangle(
            0, self.ground_y, W, H, fill=COLOR_GROUND, outline="", tags="ground"
        )

    def _redraw_bird(self):
        self.canvas.delete("bird")
        x1 = BIRD_X - BIRD_SIZE // 2
        y1 = self.bird_y - BIRD_SIZE // 2
        x2 = BIRD_X + BIRD_SIZE // 2
        y2 = self.bird_y + BIRD_SIZE // 2
        # simple body
        self.canvas.create_oval(x1, y1, x2, y2, fill=COLOR_BIRD, outline="", tags="bird")
        # tiny eye for charm
        self.canvas.create_oval(x2 - 10, y1 + 6, x2 - 4, y1 + 12,
                                fill="#000", outline="", tags="bird")

    def _draw_pipes(self):
        self.canvas.delete("pipe")
        for p in self.pipes:
            x1 = int(p["x"])
            x2 = int(p["x"] + PIPE_W)
            gap_y = p["gap_y"]
            gap_h = p["gap_h"]
            # top pipe
            self.canvas.create_rectangle(
                x1, 0, x2, gap_y - gap_h // 2, fill=COLOR_PIPE, outline="", tags="pipe"
            )
            # bottom pipe
            self.canvas.create_rectangle(
                x1, gap_y + gap_h // 2, x2, self.ground_y, fill=COLOR_PIPE, outline="", tags="pipe"
            )

    def _redraw(self):
        self._draw_pipes()
        self._redraw_bird()
        self._update_hud()

    def _overlay(self, text: str):
        self.canvas.delete("overlay")
        self.canvas.create_rectangle(0, 0, W, H, fill="#000", stipple="gray50",
                                     outline="", tags="overlay")
        self.canvas.create_text(
            W // 2, H // 2 - 12, text=text, fill="#ffffff",
            font=("Segoe UI", 28, "bold"), tags="overlay"
        )
        if text == "GAME OVER":
            self.canvas.create_text(
                W // 2, H // 2 + 22, text="Press R to restart",
                fill="#eeeeee", font=("Segoe UI", 13), tags="overlay"
            )

    def _update_hud(self):
        status = ""
        if self.paused:
            status = "Paused"
        if self.game_over:
            status = "Game Over — press [R] to restart"
        self.hud.config(text=f"Score: {self.score}   {status}")

    def _spawn_pipe_pair(self):
        gap_h = random.randint(GAP_MIN, GAP_MAX)

        margin = 40
        min_center = margin + gap_h // 2
        max_center = self.ground_y - margin - gap_h // 2
        gap_y = random.randint(min_center, max_center)

        pipe = {
            "id": id(object()),
            "x": W + 20,
            "gap_y": gap_y,
            "gap_h": gap_h,
        }
        self.pipes.append(pipe)

    def _collides_ground(self) -> bool:
        top = self.bird_y - BIRD_SIZE // 2
        bottom = self.bird_y + BIRD_SIZE // 2
        return bottom >= self.ground_y or top <= 0

    def _collides_pipes(self) -> bool:
        bx1 = BIRD_X - BIRD_SIZE // 2
        bx2 = BIRD_X + BIRD_SIZE // 2
        by1 = self.bird_y - BIRD_SIZE // 2
        by2 = self.bird_y + BIRD_SIZE // 2
        for p in self.pipes:
            px1 = int(p["x"])
            px2 = int(p["x"] + PIPE_W)
            gap_y = p["gap_y"]
            gap_h = p["gap_h"]
            if not (bx2 < px1 or bx1 > px2):
                if by1 < (gap_y - gap_h // 2):
                    return True

                if by2 > (gap_y + gap_h // 2):
                    return True
        return False

    def _end_game(self):
        self.game_over = True
        self._update_hud()
        self._overlay("GAME OVER")


def main():
    root = tk.Tk()
    Flappy(root)
    root.mainloop()

if __name__ == "__main__":
    main()
