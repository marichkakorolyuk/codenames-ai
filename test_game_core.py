import unittest
from game_core import CardType, Card, GameState, GameEngine

class TestCardType(unittest.TestCase):
    def test_card_types(self):
        self.assertEqual(CardType.RED.value, "red")
        self.assertEqual(CardType.BLUE.value, "blue")
        self.assertEqual(CardType.NEUTRAL.value, "neutral")
        self.assertEqual(CardType.ASSASSIN.value, "assassin")

class TestCard(unittest.TestCase):
    def test_card_initialization(self):
        card = Card(word="test", type=CardType.RED)
        self.assertEqual(card.word, "test")
        self.assertEqual(card.type, CardType.RED)
        self.assertFalse(card.revealed)
        
        card = Card(word="test2", type=CardType.BLUE, revealed=True)
        self.assertEqual(card.word, "test2")
        self.assertEqual(card.type, CardType.BLUE)
        self.assertTrue(card.revealed)

class TestGameState(unittest.TestCase):
    def setUp(self):
        self.cards = [
            Card("red1", CardType.RED),
            Card("red2", CardType.RED),
            Card("blue1", CardType.BLUE),
            Card("blue2", CardType.BLUE),
            Card("neutral", CardType.NEUTRAL),
            Card("assassin", CardType.ASSASSIN)
        ]
        self.game_state = GameState(
            game_id="test_game",
            board=self.cards,
            red_remaining=2,
            blue_remaining=2,
            current_team=CardType.RED
        )
    
    def test_game_state_initialization(self):
        self.assertEqual(self.game_state.game_id, "test_game")
        self.assertEqual(len(self.game_state.board), 6)
        self.assertEqual(self.game_state.red_remaining, 2)
        self.assertEqual(self.game_state.blue_remaining, 2)
        self.assertEqual(self.game_state.current_team, CardType.RED)
        self.assertIsNone(self.game_state.winner)
        self.assertEqual(self.game_state.turn_count, 0)
        self.assertEqual(self.game_state.clue_history, [])
        self.assertEqual(self.game_state.guess_history, [])
    
    def test_get_visible_state(self):
        # Initially, no cards are revealed
        visible_state = self.game_state.get_visible_state(CardType.RED)
        self.assertEqual(visible_state["game_id"], "test_game")
        self.assertEqual(len(visible_state["board"]), 6)
        for card in visible_state["board"]:
            self.assertIsNone(card["type"])
            self.assertFalse(card["revealed"])
        
        # Reveal a card
        self.cards[0].revealed = True
        visible_state = self.game_state.get_visible_state(CardType.RED)
        self.assertEqual(visible_state["board"][0]["type"], "red")
        self.assertTrue(visible_state["board"][0]["revealed"])
    
    def test_get_spymaster_state(self):
        # Spymaster can see all card types
        spymaster_state = self.game_state.get_spymaster_state(CardType.RED)
        self.assertEqual(spymaster_state["game_id"], "test_game")
        self.assertEqual(len(spymaster_state["board"]), 6)
        self.assertEqual(spymaster_state["board"][0]["type"], "red")
        self.assertEqual(spymaster_state["board"][2]["type"], "blue")
        self.assertEqual(spymaster_state["board"][4]["type"], "neutral")
        self.assertEqual(spymaster_state["board"][5]["type"], "assassin")

class TestGameEngine(unittest.TestCase):
    def setUp(self):
        self.word_list = ["apple", "banana", "cherry", "date", "elderberry",
                         "fig", "grape", "honeydew", "imbe", "jackfruit",
                         "kiwi", "lemon", "mango", "nectarine", "orange",
                         "papaya", "quince", "raspberry", "strawberry", "tangerine",
                         "ugli", "vanilla", "watermelon", "xigua", "yuzu"]
        self.engine = GameEngine(word_list=self.word_list)
    
    def test_create_game(self):
        game_id = self.engine.create_game()
        self.assertIn(game_id, self.engine.games)
        
        game = self.engine.games[game_id]
        self.assertEqual(len(game.board), 25)
        
        # Count card types
        red_cards = sum(1 for card in game.board if card.type == CardType.RED)
        blue_cards = sum(1 for card in game.board if card.type == CardType.BLUE)
        neutral_cards = sum(1 for card in game.board if card.type == CardType.NEUTRAL)
        assassin_cards = sum(1 for card in game.board if card.type == CardType.ASSASSIN)
        
        self.assertEqual(red_cards + blue_cards + neutral_cards + assassin_cards, 25)
        self.assertEqual(neutral_cards, 7)
        self.assertEqual(assassin_cards, 1)
        self.assertTrue((red_cards == 9 and blue_cards == 8) or 
                        (red_cards == 8 and blue_cards == 9))
    
    def test_process_clue(self):
        game_id = self.engine.create_game()
        game = self.engine.games[game_id]
        team = game.current_team
        
        # Valid clue
        result = self.engine.process_clue(game_id, "fruit", 3, team)
        self.assertTrue(result)
        self.assertEqual(len(game.clue_history), 1)
        self.assertEqual(game.clue_history[0], (team, "fruit", 3))
        
        # Invalid team
        wrong_team = CardType.RED if team == CardType.BLUE else CardType.BLUE
        result = self.engine.process_clue(game_id, "invalid", 2, wrong_team)
        self.assertFalse(result)
        self.assertEqual(len(game.clue_history), 1)  # Shouldn't change
    
    def test_process_guess(self):
        game_id = self.engine.create_game()
        game = self.engine.games[game_id]
        team = game.current_team
        
        # First, give a clue
        self.engine.process_clue(game_id, "test", 1, team)
        
        # For testing, we need to know which card belongs to current team
        team_card = None
        for card in game.board:
            if card.type == team:
                team_card = card
                break
        
        # Valid guess for team's card
        result = self.engine.process_guess(game_id, team_card.word, team)
        self.assertTrue(result["success"])
        self.assertEqual(result["card_type"], team.value)
        self.assertFalse(result["end_turn"])  # Should continue turn
        
        # Find a card that's not team's card
        other_team = CardType.RED if team == CardType.BLUE else CardType.BLUE
        other_card = None
        for card in game.board:
            if card.type == other_team and not card.revealed:
                other_card = card
                break
        
        # Guess other team's card, should end turn
        result = self.engine.process_guess(game_id, other_card.word, team)
        self.assertTrue(result["success"])
        self.assertEqual(result["card_type"], other_team.value)
        self.assertTrue(result["end_turn"])
        
        # Verify team changed
        self.assertEqual(game.current_team, other_team)
    
    def test_assassin_guess(self):
        game_id = self.engine.create_game()
        game = self.engine.games[game_id]
        team = game.current_team
        
        # Find the assassin card
        assassin_card = None
        for card in game.board:
            if card.type == CardType.ASSASSIN:
                assassin_card = card
                break
        
        # Guess the assassin card
        result = self.engine.process_guess(game_id, assassin_card.word, team)
        self.assertTrue(result["success"])
        self.assertEqual(result["card_type"], "assassin")
        self.assertTrue(result["end_turn"])
        self.assertTrue(result["game_over"])
        
        # Other team should win
        other_team = CardType.RED if team == CardType.BLUE else CardType.BLUE
        self.assertEqual(result["winner"], other_team.value)
        self.assertEqual(game.winner, other_team)
    
    def test_end_turn(self):
        game_id = self.engine.create_game()
        game = self.engine.games[game_id]
        team = game.current_team
        other_team = CardType.RED if team == CardType.BLUE else CardType.BLUE
        
        # Valid end turn
        result = self.engine.end_turn(game_id, team)
        self.assertTrue(result)
        self.assertEqual(game.current_team, other_team)
        self.assertEqual(game.turn_count, 1)
        
        # Invalid team tries to end turn
        result = self.engine.end_turn(game_id, team)  # Same team, but now it's not their turn
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()
