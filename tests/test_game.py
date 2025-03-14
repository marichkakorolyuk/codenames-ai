"""
Unit tests for Codenames core game logic.
Tests the functionality of game entities and the game engine.
"""

import unittest
from unittest.mock import patch, MagicMock
import random

from codenames.game import CardType, Card, Player, GameState, GameEngine
from codenames.words import WORD_LIST


class TestCardType(unittest.TestCase):
    """Tests for the CardType enum"""
    
    def test_card_type_values(self):
        """Test that CardType has the expected values"""
        self.assertEqual(CardType.RED.value, "red")
        self.assertEqual(CardType.BLUE.value, "blue")
        self.assertEqual(CardType.NEUTRAL.value, "neutral")
        self.assertEqual(CardType.ASSASSIN.value, "assassin")


class TestCard(unittest.TestCase):
    """Tests for the Card class"""
    
    def test_card_creation(self):
        """Test creating a card"""
        card = Card(word="test", type=CardType.RED)
        self.assertEqual(card.word, "test")
        self.assertEqual(card.type, CardType.RED)
        self.assertFalse(card.revealed)
    
    def test_card_reveal(self):
        """Test revealing a card"""
        card = Card(word="test", type=CardType.RED)
        self.assertFalse(card.revealed)
        card.revealed = True
        self.assertTrue(card.revealed)


class TestPlayer(unittest.TestCase):
    """Tests for the Player class"""
    
    def test_player_creation(self):
        """Test creating a player"""
        player = Player(id="1", name="Test Player", team=CardType.RED, role="spymaster")
        self.assertEqual(player.id, "1")
        self.assertEqual(player.name, "Test Player")
        self.assertEqual(player.team, CardType.RED)
        self.assertEqual(player.role, "spymaster")
        self.assertFalse(player.is_ai)
    
    def test_ai_player_creation(self):
        """Test creating an AI player"""
        player = Player(id="2", name="AI Player", team=CardType.BLUE, role="operative", is_ai=True)
        self.assertEqual(player.id, "2")
        self.assertEqual(player.name, "AI Player")
        self.assertEqual(player.team, CardType.BLUE)
        self.assertEqual(player.role, "operative")
        self.assertTrue(player.is_ai)


class TestGameState(unittest.TestCase):
    """Tests for the GameState class"""
    
    def setUp(self):
        """Set up test cases"""
        # Create a sample board
        self.board = [
            Card(word="apple", type=CardType.RED),
            Card(word="banana", type=CardType.BLUE),
            Card(word="cherry", type=CardType.NEUTRAL),
            Card(word="date", type=CardType.ASSASSIN),
            Card(word="elderberry", type=CardType.RED)
        ]
        
        # Create a game state
        self.game_state = GameState(
            game_id="test_game",
            board=self.board,
            red_remaining=2,
            blue_remaining=1,
            current_team=CardType.RED
        )
    
    def test_game_state_creation(self):
        """Test creating a game state"""
        self.assertEqual(self.game_state.game_id, "test_game")
        self.assertEqual(len(self.game_state.board), 5)
        self.assertEqual(self.game_state.red_remaining, 2)
        self.assertEqual(self.game_state.blue_remaining, 1)
        self.assertEqual(self.game_state.current_team, CardType.RED)
        self.assertIsNone(self.game_state.winner)
        self.assertEqual(self.game_state.turn_count, 0)
        self.assertEqual(self.game_state.clue_history, [])
        self.assertEqual(self.game_state.guess_history, [])
    
    def test_get_visible_state(self):
        """Test getting the visible state for operatives"""
        # Reveal one card
        self.game_state.board[0].revealed = True
        
        # Get visible state for red team
        visible_state = self.game_state.get_visible_state(CardType.RED)
        
        # Check that the visible state has the correct structure
        self.assertEqual(visible_state["game_id"], "test_game")
        self.assertEqual(visible_state["red_remaining"], 2)
        self.assertEqual(visible_state["blue_remaining"], 1)
        self.assertEqual(visible_state["current_team"], "red")
        self.assertIsNone(visible_state["winner"])
        
        # Check that the revealed card shows its type
        self.assertEqual(visible_state["board"][0]["word"], "apple")
        self.assertEqual(visible_state["board"][0]["type"], "red")
        self.assertTrue(visible_state["board"][0]["revealed"])
        
        # Check that unrevealed cards don't show their type
        self.assertEqual(visible_state["board"][1]["word"], "banana")
        self.assertIsNone(visible_state["board"][1]["type"])
        self.assertFalse(visible_state["board"][1]["revealed"])
    
    def test_get_spymaster_state(self):
        """Test getting the game state for spymasters"""
        # Reveal one card
        self.game_state.board[0].revealed = True
        
        # Get spymaster state for red team
        spymaster_state = self.game_state.get_spymaster_state(CardType.RED)
        
        # Check that the state has the correct structure
        self.assertEqual(spymaster_state["game_id"], "test_game")
        self.assertEqual(spymaster_state["red_remaining"], 2)
        self.assertEqual(spymaster_state["blue_remaining"], 1)
        self.assertEqual(spymaster_state["current_team"], "red")
        
        # Check that all cards show their type to the spymaster
        self.assertEqual(spymaster_state["board"][0]["word"], "apple")
        self.assertEqual(spymaster_state["board"][0]["type"], "red")
        self.assertTrue(spymaster_state["board"][0]["revealed"])
        
        self.assertEqual(spymaster_state["board"][1]["word"], "banana")
        self.assertEqual(spymaster_state["board"][1]["type"], "blue")
        self.assertFalse(spymaster_state["board"][1]["revealed"])
        
        self.assertEqual(spymaster_state["board"][3]["word"], "date")
        self.assertEqual(spymaster_state["board"][3]["type"], "assassin")
    
    def test_is_game_over(self):
        """Test the is_game_over method"""
        # Initially, game is not over
        self.assertFalse(self.game_state.is_game_over())
        
        # Set a winner
        self.game_state.winner = CardType.RED
        self.assertTrue(self.game_state.is_game_over())
    
    def test_get_winner(self):
        """Test the get_winner method"""
        # Initially, no winner
        self.assertIsNone(self.game_state.get_winner())
        
        # Set a winner
        self.game_state.winner = CardType.BLUE
        self.assertEqual(self.game_state.get_winner(), "blue")


class TestGameEngine(unittest.TestCase):
    """Tests for the GameEngine class"""
    
    def setUp(self):
        """Set up test cases"""
        # Create a sample word list
        self.test_words = ["apple", "banana", "cherry", "date", "elderberry",
                          "fig", "grape", "honeydew", "imbe", "jackfruit",
                          "kiwi", "lemon", "mango", "nectarine", "orange",
                          "papaya", "quince", "raspberry", "strawberry", "tangerine",
                          "ugli", "vanilla", "watermelon", "xigua", "yuzu"]
        
        # Create a game engine with the test word list
        self.engine = GameEngine(self.test_words)
    
    @patch('random.sample')
    @patch('random.choice')
    @patch('random.shuffle')
    def test_create_game(self, mock_shuffle, mock_choice, mock_sample):
        """Test creating a new game"""
        # Set up mocks to make the test deterministic
        mock_sample.return_value = self.test_words
        mock_choice.return_value = CardType.RED
        
        # Create a new game
        game_id = self.engine.create_game()
        
        # Check that the game was created
        self.assertIn(game_id, self.engine.games)
        
        # Get the game state
        game = self.engine.get_game(game_id)
        
        # Check that the game state was initialized correctly
        self.assertEqual(game.current_team, CardType.RED)
        self.assertEqual(len(game.board), 25)
        self.assertEqual(game.red_remaining, 9)
        self.assertEqual(game.blue_remaining, 8)
        self.assertIsNone(game.winner)
    
    def test_process_clue(self):
        """Test processing a clue from a spymaster"""
        # Create a game
        game_id = self.engine.create_game()
        game = self.engine.get_game(game_id)
        
        # Process a clue
        result = self.engine.process_clue(game_id, "fruit", 3, game.current_team)
        
        # Check that the clue was processed
        self.assertTrue(result)
        self.assertEqual(len(game.clue_history), 1)
        self.assertEqual(game.clue_history[0][1], "fruit")
        self.assertEqual(game.clue_history[0][2], 3)
        
        # Test invalid cases
        
        # Wrong team
        wrong_team = CardType.BLUE if game.current_team == CardType.RED else CardType.RED
        result = self.engine.process_clue(game_id, "test", 1, wrong_team)
        self.assertFalse(result)
        
        # Invalid game ID
        result = self.engine.process_clue("invalid_id", "test", 1, game.current_team)
        self.assertFalse(result)
    
    def test_process_guess(self):
        """Test processing a guess from an operative"""
        # Create a game
        game_id = self.engine.create_game()
        game = self.engine.get_game(game_id)
        current_team = game.current_team
        
        # Find a card for the current team
        team_card = None
        for card in game.board:
            if card.type == current_team:
                team_card = card
                break
        
        # Process a clue first (requirement for a valid turn)
        self.engine.process_clue(game_id, "fruit", 3, current_team)
        
        # Process a guess for a team card
        result = self.engine.process_guess(game_id, team_card.word, current_team)
        
        # Check that the guess was processed
        self.assertTrue(result["success"])
        self.assertEqual(result["card_type"], current_team.value)
        self.assertFalse(result["end_turn"])
        self.assertTrue(team_card.revealed)
        
        # The team count should have decreased
        if current_team == CardType.RED:
            self.assertEqual(game.red_remaining, 8)
        else:
            self.assertEqual(game.blue_remaining, 7)
        
        # Find an opponent card
        opponent_team = CardType.BLUE if current_team == CardType.RED else CardType.RED
        opponent_card = None
        for card in game.board:
            if card.type == opponent_team and not card.revealed:
                opponent_card = card
                break
        
        # Process a guess for an opponent card
        result = self.engine.process_guess(game_id, opponent_card.word, current_team)
        
        # Check that the guess was processed and turn ended
        self.assertTrue(result["success"])
        self.assertEqual(result["card_type"], opponent_team.value)
        self.assertTrue(result["end_turn"])
        self.assertTrue(opponent_card.revealed)
        
        # The opponent count should have decreased
        if opponent_team == CardType.RED:
            self.assertEqual(game.red_remaining, 8)
        else:
            self.assertEqual(game.blue_remaining, 7)
        
        # The current team should have changed
        self.assertEqual(game.current_team, opponent_team)
    
    def test_assassin_guess(self):
        """Test guessing the assassin card"""
        # Create a game
        game_id = self.engine.create_game()
        game = self.engine.get_game(game_id)
        current_team = game.current_team
        
        # Find the assassin card
        assassin_card = None
        for card in game.board:
            if card.type == CardType.ASSASSIN:
                assassin_card = card
                break
        
        # Process a clue first
        self.engine.process_clue(game_id, "test", 1, current_team)
        
        # Process a guess for the assassin
        result = self.engine.process_guess(game_id, assassin_card.word, current_team)
        
        # Check that the game is over and the current team lost
        self.assertTrue(result["success"])
        self.assertEqual(result["card_type"], "assassin")
        self.assertTrue(result["end_turn"])
        self.assertTrue(result["game_over"])
        
        # The winner should be the other team
        expected_winner = CardType.BLUE if current_team == CardType.RED else CardType.RED
        self.assertEqual(result["winner"], expected_winner.value)
        self.assertEqual(game.winner, expected_winner)
    
    def test_win_by_guessing_all_cards(self):
        """Test winning by guessing all cards"""
        # Create a test game with a controlled setup
        game_id = "test_win"
        
        # Manually create a board with a specific setup
        board = []
        
        # 2 red cards, 1 blue card, 1 neutral, 1 assassin
        board.append(Card(word="apple", type=CardType.RED))
        board.append(Card(word="banana", type=CardType.RED))
        board.append(Card(word="cherry", type=CardType.BLUE))
        board.append(Card(word="date", type=CardType.NEUTRAL))
        board.append(Card(word="elderberry", type=CardType.ASSASSIN))
        
        # Create the game state
        game_state = GameState(
            game_id=game_id,
            board=board,
            red_remaining=2,
            blue_remaining=1,
            current_team=CardType.RED
        )
        
        # Add to the engine
        self.engine.games[game_id] = game_state
        
        # Process a clue
        self.engine.process_clue(game_id, "fruit", 2, CardType.RED)
        
        # Guess the first red card
        result = self.engine.process_guess(game_id, "apple", CardType.RED)
        self.assertTrue(result["success"])
        self.assertEqual(result["card_type"], "red")
        self.assertFalse(result["end_turn"])
        self.assertEqual(game_state.red_remaining, 1)
        
        # Guess the second red card
        result = self.engine.process_guess(game_id, "banana", CardType.RED)
        self.assertTrue(result["success"])
        self.assertEqual(result["card_type"], "red")
        self.assertTrue(result["game_over"])
        self.assertEqual(result["winner"], "red")
        self.assertEqual(game_state.red_remaining, 0)
        self.assertEqual(game_state.winner, CardType.RED)
    
    def test_end_turn(self):
        """Test ending a turn"""
        # Create a game
        game_id = self.engine.create_game()
        game = self.engine.get_game(game_id)
        current_team = game.current_team
        next_team = CardType.BLUE if current_team == CardType.RED else CardType.RED
        
        # End the turn
        result = self.engine.end_turn(game_id, current_team)
        
        # Check that the turn was ended
        self.assertTrue(result)
        self.assertEqual(game.current_team, next_team)
        self.assertEqual(game.turn_count, 1)
        
        # Test invalid cases
        
        # Wrong team
        result = self.engine.end_turn(game_id, current_team)  # Old current_team
        self.assertFalse(result)
        
        # Invalid game ID
        result = self.engine.end_turn("invalid_id", next_team)
        self.assertFalse(result)
    
    def test_get_game(self):
        """Test getting a game by ID"""
        # Create a game
        game_id = self.engine.create_game()
        
        # Get the game
        game = self.engine.get_game(game_id)
        
        # Check that the game was retrieved
        self.assertIsNotNone(game)
        self.assertEqual(game.game_id, game_id)
        
        # Test invalid ID
        game = self.engine.get_game("invalid_id")
        self.assertIsNone(game)


if __name__ == "__main__":
    unittest.main()
