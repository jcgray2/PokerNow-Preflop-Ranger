import os
import pickle
import traceback
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from models import Card, GameState, PlayerInfo, PlayerState

class CookieManager:
    def __init__(self, driver, cookie_path):
        self.driver = driver
        self.cookie_path = cookie_path

    def load_cookies(self):
        if os.path.exists(self.cookie_path):
            cookies = pickle.load(open(self.cookie_path, 'rb'))
            current_url = self.driver.current_url
            for cookie in cookies:
                if cookie.get('domain', '') in current_url:
                    self.driver.add_cookie(cookie)
        else:
            self.save_cookies()

    def save_cookies(self):
        pickle.dump(self.driver.get_cookies(), open(self.cookie_path, 'wb'))

class GameStateManager:
    def __init__(self, element_helper):
        self.element_helper = element_helper
        self.player_count = 0

    def get_players_info(self):
        player_elements = self.element_helper.get_elements('.table-player')
        dealer_position = self.get_dealer_position()
        print(f"Dealer position: {dealer_position}")

        players = []
        for i, player_element in enumerate(player_elements):
            name = self.element_helper.get_text('.table-player-name a', player_element) or f"Player {i+1}"
            stack = self.element_helper.get_text('.table-player-stack .chips-value', player_element) or "Unknown"
            
            if not name.startswith("Player") and stack != "Unknown":
                is_dealer = str(i + 1) == dealer_position  # +1 because dealer position is 1-indexed
                players.append(PlayerInfo(
                    name=name,
                    stack=stack,
                    bet_value=self.element_helper.get_text('.table-player-bet-value .chips-value', player_element) or "0",
                    status=self.get_player_status(player_element),
                    position=i,
                    position_name="BTN" if is_dealer else ""
                ))
            
            print(f"Player {i + 1}: Name: {name}, Stack: {stack}, Is Dealer: {str(i + 1) == dealer_position}")

        return players

    def get_dealer_position(self):
        dealer_button = self.element_helper.get_element('.dealer-button-ctn')
        if dealer_button:
            position = dealer_button.get_attribute('class').split('-')[-1]
            print(f"Dealer button found. Position: {position}")
            return position
        print("Dealer button not found. Returning 'unknown'.")
        return 'unknown'

    def is_player_sitting_out(self, player_element):
        return 'player-sitting-out' in player_element.get_attribute('class')

    def get_player_status(self, player_element):
        class_list = player_element.get_attribute('class').split()
        if 'decision-current' in class_list:
            return 'Current'
        if 'fold' in class_list:
            return 'Folded'
        if 'offline' in class_list:
            return 'Offline'
        return 'Active'

    def get_position_name(self, position):
        positions = ["SB", "BB", "BTN", "CO"]
        if self.player_count <= len(positions):
            return positions[position % self.player_count]
        else:
            return f"P{position}"

    def get_player_action(self, player_element):
        action_element = self.element_helper.get_element('.player-action', player_element)
        if not action_element:
            action_element = self.element_helper.get_element('.table-player-action-buttons', player_element)
        return action_element.text if action_element else ''

    def get_blinds(self):
        blind_values = self.element_helper.get_elements('.blind-value-ctn .chips-value')
        return [self.parse_stack_value(blind.text) for blind in blind_values]

    def get_current_player(self):
        current_player_element = self.element_helper.get_element('.table-player.decision-current')
        return self.element_helper.get_text('.table-player-name a', current_player_element) if current_player_element else 'unknown'

    def get_your_cards(self):
        card_elements = self.element_helper.get_elements('.table-player.player-hover .table-player-cards .card-container')
        return [Card.parse_card_class(card.get_attribute('class')) for card in card_elements if 'card-hidden' not in card.get_attribute('class')]

    def parse_stack_value(self, stack_value):
        if '+' in stack_value:
            stack_value = stack_value.split('+')[0]
        return stack_value.strip()

class ActionHelper:
    def __init__(self, element_helper):
        self.element_helper = element_helper

    def get_available_actions(self):
        available_actions = {}
        for action_name, selector in {
            'Call': '.game-decisions-ctn .button-1.call',
            'Raise': '.game-decisions-ctn .button-1.raise',
            'Check': '.game-decisions-ctn .button-1.check',
            'Fold': '.game-decisions-ctn .button-1.fold'
        }.items():
            element = self.element_helper.get_element(selector)
            if element and element.is_displayed() and not element.get_attribute('disabled'):
                available_actions[action_name] = element
        return available_actions

    def perform_action(self, action, amount=None):
        available_actions = self.get_available_actions()
        if action == 'Raise' and available_actions.get('Raise'):
            self.handle_raise(amount)
        elif action in available_actions:
            available_actions[action].click()
            if action == 'Fold':
                self.check_and_handle_fold_confirmation()
        else:
            print(f"Action {action} not available.")

    def handle_raise(self, amount):
        raise_button = self.element_helper.get_element('.game-decisions-ctn .button-1.raise')
        if raise_button:
            raise_button.click()
            time.sleep(.25)
            raise_input = self.element_helper.get_element('.raise-controller-form .value-input-ctn .value')
            if raise_input:
                raise_input.clear()
                raise_input.send_keys(str(amount))
            confirm_button = self.element_helper.get_element('.raise-controller-form .bet')
            if confirm_button:
                confirm_button.click()

    def check_and_handle_fold_confirmation(self):
        try:
            confirm_button = self.element_helper.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.alert-1-buttons button.middle-gray')))
            confirm_button.click()
        except Exception as e:
            print(f"Error: {e}")

class ElementHelper:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)

    def wait_for_element(self, selector, timeout=10):
        try:
            return self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        except TimeoutException:
            print(f"Element {selector} not found within {timeout} seconds")
            return None

    def is_element_present(self, selector):
        try:
            self.driver.find_element(By.CSS_SELECTOR, selector)
            return True
        except NoSuchElementException:
            return False

    def get_text(self, selector, context=None):
        try:
            element = context.find_element(By.CSS_SELECTOR, selector) if context else self.driver.find_element(By.CSS_SELECTOR, selector)
            return element.text.strip()
        except NoSuchElementException:
            return ""

    def get_element(self, selector, context=None):
        try:
            return context.find_element(By.CSS_SELECTOR, selector) if context else self.driver.find_element(By.CSS_SELECTOR, selector)
        except NoSuchElementException:
            return None

    def get_elements(self, selector, context=None):
        return context.find_elements(By.CSS_SELECTOR, selector) if context else self.driver.find_elements(By.CSS_SELECTOR, selector)