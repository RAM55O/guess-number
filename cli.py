"""Interactive Terminal CLI for Guess the Number with SQLite Database."""

import sys
import os
import time
from database import Database
from game_logic import GameEngine
from models import Difficulty, DifficultyConfig, Player

# Ensure stdout/stderr handles UTF-8 smoothly across Windows, Linux, and Docker
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


# ANSI Color Codes for terminal UI
class Colors:
    CYAN = "\033[96m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_banner():
    banner = f"""{Colors.CYAN}{Colors.BOLD}
============================================================
       🎲  G U E S S   T H E   N U M B E R   🎲
      Powered by SQLite Database & Smart Hint Engine
============================================================{Colors.RESET}"""
    print(banner)


class CLIApp:
    def __init__(self, db: Database):
        self.db = db
        self.current_player: Player = None

    def start(self):
        clear_screen()
        print_banner()
        self.login_player()
        self.main_menu()

    def login_player(self):
        print(f"\n{Colors.YELLOW}Welcome! Please enter your player name to load or create your profile:{Colors.RESET}")
        while True:
            name = input(f"{Colors.BOLD}Player Name: {Colors.RESET}").strip()
            if name:
                self.current_player = self.db.get_or_create_player(name)
                print(f"\n{Colors.GREEN}✓ Logged in as {Colors.BOLD}{self.current_player.username}{Colors.RESET} (Player ID: {self.current_player.id})")
                time.sleep(1)
                break
            print(f"{Colors.RED}Name cannot be empty. Please enter a valid name.{Colors.RESET}")

    def main_menu(self):
        while True:
            clear_screen()
            print_banner()
            print(f"Logged in as: {Colors.BOLD}{Colors.GREEN}{self.current_player.username}{Colors.RESET}\n")
            print(f"{Colors.BOLD}1.{Colors.RESET} 🎮 Play Game")
            print(f"{Colors.BOLD}2.{Colors.RESET} 🏆 Global Leaderboard")
            print(f"{Colors.BOLD}3.{Colors.RESET} 📊 My Statistics & Match History")
            print(f"{Colors.BOLD}4.{Colors.RESET} 🔄 Switch Player")
            print(f"{Colors.BOLD}5.{Colors.RESET} 📖 How to Play & Game Rules")
            print(f"{Colors.BOLD}6.{Colors.RESET} 🚪 Exit")
            print("=" * 60)

            choice = input(f"{Colors.CYAN}Select an option (1-6): {Colors.RESET}").strip()

            if choice == "1":
                self.play_game_menu()
            elif choice == "2":
                self.show_leaderboard()
            elif choice == "3":
                self.show_player_stats()
            elif choice == "4":
                self.login_player()
            elif choice == "5":
                self.show_rules()
            elif choice == "6":
                print(f"\n{Colors.CYAN}Thanks for playing! Goodbye! 👋{Colors.RESET}\n")
                sys.exit(0)
            else:
                input(f"{Colors.RED}Invalid option! Press Enter to retry...{Colors.RESET}")

    def play_game_menu(self):
        clear_screen()
        print_banner()
        print(f"{Colors.BOLD}Select Difficulty Level:{Colors.RESET}\n")
        print(f"  {Colors.GREEN}1. Easy{Colors.RESET}   - Range: 1 to 50  | 10 Attempts | Base: 100 pts")
        print(f"  {Colors.YELLOW}2. Medium{Colors.RESET} - Range: 1 to 100 |  7 Attempts | Base: 250 pts")
        print(f"  {Colors.RED}3. Hard{Colors.RESET}   - Range: 1 to 500 |  5 Attempts | Base: 500 pts")
        print(f"  {Colors.MAGENTA}4. Custom{Colors.RESET} - Configure your own range & attempts")
        print(f"  {Colors.DIM}5. Back to Main Menu{Colors.RESET}")
        print("=" * 60)

        choice = input(f"{Colors.CYAN}Enter choice (1-5): {Colors.RESET}").strip()

        if choice == "1":
            engine = GameEngine(Difficulty.EASY)
        elif choice == "2":
            engine = GameEngine(Difficulty.MEDIUM)
        elif choice == "3":
            engine = GameEngine(Difficulty.HARD)
        elif choice == "4":
            custom_cfg = self._setup_custom_mode()
            if not custom_cfg:
                return
            engine = GameEngine(Difficulty.CUSTOM, custom_cfg)
        else:
            return

        self.run_game_loop(engine)

    def _setup_custom_mode(self) -> DifficultyConfig:
        clear_screen()
        print_banner()
        print(f"{Colors.MAGENTA}{Colors.BOLD}Custom Game Setup{Colors.RESET}\n")
        try:
            min_val = int(input("Enter Minimum Number (e.g. 1): ").strip() or "1")
            max_val = int(input("Enter Maximum Number (e.g. 200): ").strip() or "200")
            if min_val >= max_val:
                print(f"{Colors.RED}Maximum must be strictly greater than Minimum!{Colors.RESET}")
                input("Press Enter to continue...")
                return None

            max_att = int(input("Enter Max Attempts (e.g. 8): ").strip() or "8")
            if max_att <= 0:
                print(f"{Colors.RED}Attempts must be at least 1!{Colors.RESET}")
                input("Press Enter to continue...")
                return None

            base_points = max(100, int((max_val - min_val) * 1.5))
            return DifficultyConfig(min_val=min_val, max_val=max_val, max_attempts=max_att, base_points=base_points)
        except ValueError:
            print(f"{Colors.RED}Invalid integer entered!{Colors.RESET}")
            input("Press Enter to continue...")
            return None

    def run_game_loop(self, engine: GameEngine):
        clear_screen()
        print_banner()
        print(f"Mode: {Colors.BOLD}{engine.difficulty.value}{Colors.RESET} | Range: [{engine.min_bound} to {engine.max_bound}] | Total Attempts: {engine.max_attempts}")
        print(f"{Colors.DIM}Type 'q' or 'quit' anytime to abandon the game.{Colors.RESET}")
        print("-" * 60)

        while not engine.is_game_over:
            remaining = engine.max_attempts - engine.attempts_used
            attempt_bar = "🟢" * remaining + "🔴" * engine.attempts_used
            print(f"\nAttempts Left [{remaining}/{engine.max_attempts}]: {attempt_bar}")
            print(f"Current Target Bounds: {Colors.CYAN}[{engine.current_low} ... {engine.current_high}]{Colors.RESET}")

            user_input = input(f"{Colors.YELLOW}Enter your guess: {Colors.RESET}").strip()

            if user_input.lower() in ("q", "quit"):
                print(f"\n{Colors.RED}Game abandoned. The number was {engine.target_number}.{Colors.RESET}")
                input("Press Enter to return to menu...")
                return

            try:
                guess = int(user_input)
            except ValueError:
                print(f"{Colors.RED}⚠️ Please enter a valid whole number.{Colors.RESET}")
                continue

            if guess < engine.min_bound or guess > engine.max_bound:
                print(f"{Colors.RED}⚠️ Guess out of bounds! Must be between {engine.min_bound} and {engine.max_bound}.{Colors.RESET}")
                continue

            is_correct, hint_msg, meta = engine.check_guess(guess)

            if is_correct:
                print(f"\n{Colors.GREEN}{Colors.BOLD}{hint_msg}{Colors.RESET}")
                print(f"Score: {Colors.YELLOW}{Colors.BOLD}{meta['score']} pts{Colors.RESET} | Time: {meta['duration']}s")
            else:
                if engine.is_game_over:
                    print(f"\n{Colors.RED}{Colors.BOLD}{hint_msg}{Colors.RESET}")
                else:
                    print(f"\n{Colors.CYAN}👉 {hint_msg}{Colors.RESET}")

        # Save to database
        game_record = engine.to_game_record(self.current_player.id)
        game_id = self.db.save_game(game_record)
        print(f"\n{Colors.GREEN}✓ Game session saved to SQLite database (Game ID: #{game_id})!{Colors.RESET}")
        print("=" * 60)
        input(f"\nPress Enter to return to the Main Menu...")

    def show_leaderboard(self):
        clear_screen()
        print_banner()
        print(f"{Colors.BOLD}🏆 GLOBAL LEADERBOARD (Top 10 High Scores){Colors.RESET}\n")

        rows = self.db.get_leaderboard(limit=10)
        if not rows:
            print(f"{Colors.YELLOW}No winning games recorded yet. Be the first to win!{Colors.RESET}")
        else:
            header = f"{'Rank':<6}{'Player':<16}{'Difficulty':<12}{'Score':<10}{'Attempts':<10}{'Time':<8}{'Date':<18}"
            print(Colors.BOLD + header + Colors.RESET)
            print("-" * len(header))
            for i, r in enumerate(rows, start=1):
                medal = "🥇 " if i == 1 else ("🥈 " if i == 2 else ("🥉 " if i == 3 else f"#{i:<3}"))
                print(f"{medal:<6}{r['username']:<16}{r['difficulty']:<12}{r['score']:<10}{r['attempts_used']}/{r['max_attempts']:<8}{r['duration_seconds']}s   {str(r['played_at'])[:16]}")

        print("=" * 60)
        input("\nPress Enter to return to Main Menu...")

    def show_player_stats(self):
        clear_screen()
        print_banner()
        stats = self.db.get_player_stats(self.current_player.id)
        
        print(f"{Colors.BOLD}📊 Statistics for {Colors.GREEN}{self.current_player.username}{Colors.RESET}:\n")
        if not stats or stats.total_games == 0:
            print(f"{Colors.YELLOW}You haven't played any games yet!{Colors.RESET}")
        else:
            print(f"  • Total Games Played : {Colors.BOLD}{stats.total_games}{Colors.RESET}")
            print(f"  • Total Wins         : {Colors.BOLD}{Colors.GREEN}{stats.games_won}{Colors.RESET}")
            print(f"  • Win Rate           : {Colors.BOLD}{stats.win_rate}%{Colors.RESET}")
            print(f"  • High Score         : {Colors.BOLD}{Colors.YELLOW}{stats.high_score} pts{Colors.RESET}")
            print(f"  • Best Attempts (Win): {Colors.BOLD}{stats.best_attempts or 'N/A'}{Colors.RESET}")
            print(f"  • Cumulative Score   : {Colors.BOLD}{stats.total_score} pts{Colors.RESET}")

        print(f"\n{Colors.BOLD}Recent Games:{Colors.RESET}")
        recent_games = self.db.get_player_games(self.current_player.id, limit=5)
        if recent_games:
            header = f"{'ID':<6}{'Diff':<10}{'Result':<8}{'Attempts':<10}{'Score':<8}{'Date'}"
            print(header)
            print("-" * 55)
            for g in recent_games:
                res_str = f"{Colors.GREEN}WON{Colors.RESET}" if g['is_won'] else f"{Colors.RED}LOST{Colors.RESET}"
                print(f"#{g['id']:<5}{g['difficulty']:<10}{res_str:<17}{g['attempts_used']}/{g['max_attempts']:<8}{g['score']:<8}{str(g['played_at'])[:16]}")
        else:
            print(f"{Colors.DIM}No match history.{Colors.RESET}")

        print("=" * 60)
        input("\nPress Enter to return to Main Menu...")

    def show_rules(self):
        clear_screen()
        print_banner()
        print(f"""{Colors.BOLD}📖 HOW TO PLAY "GUESS THE NUMBER"{Colors.RESET}

1. {Colors.BOLD}Objective:{Colors.RESET}
   The computer randomly generates a secret number within a chosen range.
   Your goal is to guess the exact number within the allotted attempts!

2. {Colors.BOLD}Smart Hint System:{Colors.RESET}
   • {Colors.CYAN}Directional:{Colors.RESET} Tells you if your guess was Too High 📉 or Too Low 📈.
   • {Colors.YELLOW}Dynamic Range:{Colors.RESET} Automatically narrows down the remaining valid range.
   • {Colors.RED}Temperature:{Colors.RESET} Proximity indicators (Freezing ❄️, Warm ☀️, Hot ♨️, On Fire 🔥).
   • {Colors.MAGENTA}Bonus Clues:{Colors.RESET} Unlocks parity (Even/Odd) and divisibility hints on later turns.

3. {Colors.BOLD}Scoring Formula:{Colors.RESET}
   • Base points by difficulty: Easy (100 pts), Medium (250 pts), Hard (500 pts).
   • Multiplier for remaining attempts (efficiency bonus).
   • Speed bonus for solving quickly (under 60s).

4. {Colors.BOLD}Persistence:{Colors.RESET}
   • Every game session and turn-by-turn guess is recorded in {Colors.GREEN}game.db{Colors.RESET} via SQLite.
""")
        print("=" * 60)
        input("\nPress Enter to return to Main Menu...")


if __name__ == "__main__":
    db = Database("game.db")
    app = CLIApp(db)
    app.start()
