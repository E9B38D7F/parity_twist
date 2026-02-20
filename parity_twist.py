import polars as pl
from itertools import product
import pygame as p
from pygame_utils import Box, InputBox, OptionBox, print_text

WIDTH = 800
HEIGHT = 500
# p.display.set_icon(p.image.load("data/thinker.png"))
# p.display.set_caption("Calibrator")


class Game:
    def __init__(self, players):
        self.game_state = [-1] * 10
        self.players = players # This is a list of two Player objects
        self.free_numbers = list(range(1, 11)) # Numbers yet to be played
        self.move_num = 0
        self.winner = None

    def do_move(self):
        player_to_move = self.players[self.move_num % 2]
        while True:
            index, number = player_to_move.get_move(self.game_state)
            if self.game_state[index] == -1 and number in self.free_numbers:
                break
            else:
                print("Invalid move, try again")
        self.game_state[index] = number
        self.free_numbers.remove(number)
        self.move_num += 1

    def evaluate(self):
        assert self.move_num == 10, "Game not over! Cannot evaluate."
        gs = self.game_state
        print(f"Final game state: {gs}")
        p1_row_wins = 0
        for i in range(3):
            row_parity_normal = (gs[9] % 2) == (gs[6 + i] % 2)
            p1_lower = gs[i] < gs[3 + i]
            if p1_lower == row_parity_normal:
                print(f"p1 wins row {i}")
                p1_row_wins += 1
            else:
                print(f"p2 wins row {i}")
        p1_wins = p1_row_wins > 1.5
        winner = self.players[0] if p1_wins else self.players[1]
        print(f"{winner.name} wins!")
        self.winner = winner

    def play(self):
        while self.move_num < 10:
            self.do_move()
        self.evaluate()


class Player:
    # Shell class for other versions of player objects
    def __init__(self, name):
        self.name = name

    def get_move(self, game_state):
        pass


class HumanPlayer(Player):
    def __init__(self, name):
        super().__init__(name)

    def get_move(self, game_state, screen):
        # print(game_state)
        # free_numbers = [i for i in range(10) if i not in game_state]
        # print(f"Possible numbers: {free_numbers}")
        # index = int(input("Move index: "))
        # number = int(input("Number: "))
        # return index, number
        pass


class BlockheadPlayer(Player):
    def __init__(self, name):
        super().__init__(name)
        self.lookup_table = None

    def load_lookup_table(self, game_state):
        columns = pl.read_parquet("_data/ffffffffff.parquet").columns
        lazy = pl.concat([
            (
                pl.scan_parquet(f"_data/{''.join(sequence)}.parquet")
                .select(columns)
            )
            for sequence in product("ft", repeat=10)
        ])
        filt = [
            pl.col(f"slot_{i}") == game_state[i]
            for i in range(10)
            if game_state[i] != -1
        ]
        self.lookup_table = lazy.filter(*filt).collect()

    def get_move(self, game_state):
        if self.lookup_table is None:
            self.load_lookup_table(game_state)
        filtered = self.lookup_table.filter(*[
            pl.col(f"slot_{i}") == game_state[i] for i in range(10)
        ])
        return filtered["target_square"][0], filtered["number_input"][0]


def initialise_game(screen):
    print_text("New game", 40, "#FFEEFF", 400, 100, screen)
    print_text("Player 1", 32, "#FFEEFF", 150, 200, screen)
    print_text("Player 2", 32, "#FFEEFF", 150, 300, screen)
    p1_human = OptionBox(300, 175, 150, 50, screen, text="human")
    p1_computer = OptionBox(500, 175, 150, 50, screen, text="computer")
    p1_human.others = [p1_computer]; p1_computer.others = [p1_human]
    p2_human = OptionBox(300, 275, 150, 50, screen, text="human")
    p2_computer = OptionBox(500, 275, 150, 50, screen, text="computer")
    p2_human.others = [p2_computer]; p2_computer.others = [p2_human]
    start_button = Box(300, 400, 200, 50, screen, text="Start game")
    p.display.flip()
    starting = False
    while not starting:
        e = p.event.wait()
        if e.type == p.MOUSEBUTTONDOWN:
            for box in [p1_human, p1_computer, p2_human, p2_computer]:
                box.handle_event(e, screen)
            starting = (
                start_button.rect.collidepoint(e.pos)
                and (p1_human.active or p1_computer.active)
                and (p2_human.active or p2_computer.active)
            )
            p.display.flip()
    return Game([
        HumanPlayer("p1") if p1_human.active else BlockheadPlayer("p1"),
        HumanPlayer("p2") if p2_human.active else BlockheadPlayer("p2")
    ])


def play_game(game, screen):
    coords = {0: (200, 100), 3: (350, 100), 6: (500, 100),
              1: (200, 200), 4: (350, 200), 7: (500, 200),
              2: (200, 300), 5: (350, 300), 8: (500, 300),
                                            9: (500, 400)}

    while game.move_num <= 10:
        player = game.players[game.move_num % 2]
        screen.fill(p.Color("black"))
        header_text = (
            f"{player.name}'s Turn ({type(player).__name__})"
            if game.move_num < 10 else "Game over!"
        )
        print_text(header_text, 30, "#FFEEFF", 400, 30, screen)

        # Draw current board state
        inputs = {}
        for i in range(10):
            x, y = coords[i]
            val = str(game.game_state[i]) if game.game_state[i] != -1 else ""
            inputs[i] = InputBox(x, y, 100, 60, screen, text=val)
        p.display.flip()
        if game.move_num == 10:
            break

        if isinstance(player, BlockheadPlayer):
            # Computer logic
            p.time.wait(1000) # ⏳ Wait 1s so the human can see what's happening
            idx, num = player.get_move(game.game_state)
            game.game_state[idx] = num
            game.free_numbers.remove(num)
            game.move_num += 1
            continue

        else:
            # Human logic
            submit_btn = Box(250, 400, 150, 60, screen, text="Submit")
            waiting_for_move = True
            while waiting_for_move:
                e = p.event.wait()
                for i, box in inputs.items():
                    if game.game_state[i] == -1: box.handle_event(e, screen)
                if e.type == p.MOUSEBUTTONDOWN:
                    if submit_btn.rect.collidepoint(e.pos):
                        try:
                            for i, box in inputs.items():
                                if (
                                    game.game_state[i] == -1
                                    and box.text != ""
                                ):
                                    idx, num = i, int(box.text)
                                    assert num in game.free_numbers
                                    game.game_state[idx] = num
                                    game.free_numbers.remove(num)
                                    game.move_num += 1
                                    waiting_for_move = False
                                    break
                        except:
                            print_text(
                                "INVALID!",
                                40,
                                "Red",
                                400,
                                450,
                                screen
                            )
                            p.display.flip()
                            p.time.wait(800)
                            waiting_for_move = False
                p.display.flip()


def print_end_state(game, screen):
    game.evaluate()
    print_text(f"{game.winner.name} wins!", 40, "Green", 400, 180, screen)
    print_text("Click to quit", 24, "Orange", 400, 280, screen)
    p.display.flip()
    while True:
        e = p.event.wait()
        if e.type == p.MOUSEBUTTONDOWN:
            p.quit()
            return


def run_games(screen):
    game = initialise_game(screen)
    play_game(game, screen)
    print_end_state(game, screen)

def main():
    p.init()
    screen = p.display.set_mode((WIDTH, HEIGHT))
    screen.fill(p.Color("black"))
    p.display.flip()
    run_games(screen)


if __name__ == "__main__":
    main()
