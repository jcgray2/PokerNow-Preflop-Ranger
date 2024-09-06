import traceback
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from pokernow_client import PokerClient
import time

class RangeDisplay:
    def __init__(self, game_url):
        options = Options()
        options.add_argument("-headless")  # Run Firefox in headless mode (optional)
        self.driver = webdriver.Firefox(options=options)
        self.client = PokerClient(self.driver)
        self.game_url = game_url

    def start(self):
        try:
            self.client.navigate(self.game_url)
            print("Navigated to the game URL. Waiting for the page to load...")
           
            try:
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".table-player"))
                )
                print("Game elements detected. Proceeding to capture game state.")
            except TimeoutException:
                print("Timed out waiting for game elements to load.")
                return

            start_time = time.time()
            while time.time() - start_time < 60:  # Run for a maximum of 60 seconds
                try:
                    print("\nAttempting to get game state...")
                    players_info = self.client.game_state_manager.get_players_info()
                    self.display_players_info(players_info)
                except Exception as e:
                    print(f"Error getting game state: {e}")
                    traceback.print_exc()
               
                print("\nPress Ctrl+C to stop the script...")
                time.sleep(5)  # Check for updates every 5 seconds
           
            print("Script ran for 60 seconds and will now exit.")
        except KeyboardInterrupt:
            print("Script interrupted by user.")
        except Exception as e:
            print(f"An error occurred in the main loop: {e}")
            traceback.print_exc()
        finally:
            self.driver.quit()

    def display_players_info(self, players_info):
        print("\nCurrent Players Information:")
        print(f"Number of active players: {len(players_info)}")
        active_players = [p for p in players_info if p.status != 'Folded']
        folded_players = [p for p in players_info if p.status == 'Folded']
        max_bet = max(float(p.bet_value) for p in players_info)

        print("Active Players:")
        for player in active_players:
            bet_value = float(player.bet_value)
            to_call = max_bet - bet_value
            status = "** Current **" if player.status == 'Current' else player.status
            print(f"Name: {player.name} ({status}) - Position: {player.position_name}")
            print(f"  Stack: {player.stack}")
            print(f"  Bet: {player.bet_value}")
            if to_call > 0:
                print(f"  To Call: {to_call:.2f}")
            print("  ---")

        print("\nFolded Players:")
        for player in folded_players:
            print(f"Name: {player.name} - Position: {player.position_name}")
            print(f"  Stack: {player.stack}")
            print("  ---")

if __name__ == "__main__":
    try:
        game_url = input("Enter the PokerNow game URL: ")
        range_display = RangeDisplay(game_url)
        range_display.start()
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Traceback:")
        traceback.print_exc()
    finally:
        input("Press Enter to exit...")