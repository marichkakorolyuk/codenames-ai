"""
Unit tests for Codenames AI agents.
Tests the functionality of AI agent implementations.
"""

import unittest
from unittest.mock import patch, MagicMock
import json

from codenames.game import CardType, Card, GameState
from codenames.agents.spymaster import SpymasterAgent
from codenames.agents.operative import OperativeAgent
from codenames.agents.debates import DebateManager


class TestSpymasterAgent(unittest.TestCase):
    """Tests for the SpymasterAgent class"""
    
    def setUp(self):
        """Set up test cases"""
        # Create a sample agent
        self.agent = SpymasterAgent(name="TestSpymaster", team=CardType.RED)
        
        # Create a sample game state for testing
        board = [
            Card(word="apple", type=CardType.RED, revealed=False),
            Card(word="banana", type=CardType.RED, revealed=False),
            Card(word="cherry", type=CardType.BLUE, revealed=False),
            Card(word="date", type=CardType.BLUE, revealed=False),
            Card(word="elderberry", type=CardType.NEUTRAL, revealed=False),
            Card(word="fig", type=CardType.NEUTRAL, revealed=False),
            Card(word="grape", type=CardType.ASSASSIN, revealed=False),
        ]
        
        self.game_state = GameState(
            game_id="test_game",
            board=board,
            red_remaining=2,
            blue_remaining=2,
            current_team=CardType.RED
        )
    
    @patch('openai.OpenAI')
    def test_make_api_call(self, mock_openai):
        """Test making an API call"""
        # Set up mock
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_completion = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_choice = MagicMock()
        mock_choice.message.content = "Test response"
        mock_completion.choices = [mock_choice]
        
        # Make the API call
        response = self.agent.make_api_call("System message", "User message")
        
        # Check that the API was called with the correct parameters
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args[1]
        self.assertEqual(call_args["model"], "gpt-4o")
        self.assertEqual(call_args["messages"][0]["role"], "system")
        self.assertEqual(call_args["messages"][0]["content"], "System message")
        self.assertEqual(call_args["messages"][1]["role"], "user")
        self.assertEqual(call_args["messages"][1]["content"], "User message")
        
        # Check that the response was processed correctly
        self.assertEqual(response, "Test response")
    
    @patch.object(SpymasterAgent, 'make_api_call')
    def test_generate_clue(self, mock_make_api_call):
        """Test generating a clue"""
        # Set up mock to return a formatted clue
        mock_make_api_call.return_value = """
CLUE: fruit
NUMBER: 2
TARGETS: apple, banana
"""
        
        # Generate a clue
        clue_word, clue_number, target_words = self.agent.generate_clue(self.game_state)
        
        # Check that the API was called
        mock_make_api_call.assert_called_once()
        
        # Check that the clue was parsed correctly
        self.assertEqual(clue_word, "fruit")
        self.assertEqual(clue_number, 2)
        self.assertEqual(target_words, ["apple", "banana"])
        
        # Check that the decision was logged
        self.assertEqual(len(self.agent.decisions), 1)
        self.assertEqual(self.agent.decisions[0]["type"], "clue")
        self.assertEqual(self.agent.decisions[0]["parsed"]["word"], "fruit")
        self.assertEqual(self.agent.decisions[0]["parsed"]["number"], 2)
        self.assertEqual(self.agent.decisions[0]["parsed"]["targets"], ["apple", "banana"])
    
    def test_word_similarity(self):
        """Test the word similarity function"""
        # Same words
        self.assertEqual(self.agent._simple_word_similarity("apple", "apple"), 1.0)
        
        # Substring
        self.assertAlmostEqual(self.agent._simple_word_similarity("app", "apple"), 0.8)
        
        # Different words with common letters
        sim = self.agent._simple_word_similarity("apple", "plane")
        self.assertTrue(0 < sim < 1)
        
        # Completely different words
        self.assertAlmostEqual(self.agent._simple_word_similarity("xyz", "abc"), 0.0)


class TestOperativeAgent(unittest.TestCase):
    """Tests for the OperativeAgent class"""
    
    def setUp(self):
        """Set up test cases"""
        # Create a sample agent
        self.agent = OperativeAgent(name="TestOperative", team=CardType.RED)
        
        # Create a sample game state for testing
        board = [
            Card(word="apple", type=CardType.RED, revealed=False),
            Card(word="banana", type=CardType.RED, revealed=False),
            Card(word="cherry", type=CardType.BLUE, revealed=False),
            Card(word="date", type=CardType.BLUE, revealed=False),
            Card(word="elderberry", type=CardType.NEUTRAL, revealed=False),
            Card(word="fig", type=CardType.NEUTRAL, revealed=False),
            Card(word="grape", type=CardType.ASSASSIN, revealed=False),
        ]
        
        self.game_state = GameState(
            game_id="test_game",
            board=board,
            red_remaining=2,
            blue_remaining=2,
            current_team=CardType.RED
        )
    
    @patch.object(OperativeAgent, 'make_api_call')
    def test_generate_guess(self, mock_make_api_call):
        """Test generating a guess"""
        # Set up mock to return a formatted guess
        mock_make_api_call.return_value = """
DECISION: apple
REASONING: This word seems most related to the clue 'fruit'.
"""
        
        # Generate a guess
        guess_word, reasoning = self.agent.generate_guess(
            self.game_state, "fruit", 2, 0, []
        )
        
        # Check that the API was called
        mock_make_api_call.assert_called_once()
        
        # Check that the guess was parsed correctly
        self.assertEqual(guess_word, "apple")
        self.assertEqual(reasoning, "This word seems most related to the clue 'fruit'.")
        
        # Check that the decision was logged
        self.assertEqual(len(self.agent.decisions), 1)
        self.assertEqual(self.agent.decisions[0]["type"], "guess")
        self.assertEqual(self.agent.decisions[0]["parsed"]["guess"], "apple")
    
    @patch.object(OperativeAgent, 'make_api_call')
    def test_debate_response(self, mock_make_api_call):
        """Test generating a debate response"""
        # Set up mock
        mock_make_api_call.return_value = "I think apple is the best guess because it's clearly a fruit."
        
        # Create a sample debate log
        debate_log = [
            {
                "round": 1,
                "agent": "Agent1",
                "message": "I suggest we guess 'banana'.",
                "guess": "banana"
            }
        ]
        
        # Generate a debate response
        response = self.agent.debate_response(debate_log, self.game_state, "fruit", 2)
        
        # Check that the API was called
        mock_make_api_call.assert_called_once()
        
        # Check the response
        self.assertEqual(response, "I think apple is the best guess because it's clearly a fruit.")
    
    @patch.object(OperativeAgent, 'make_api_call')
    def test_final_vote(self, mock_make_api_call):
        """Test casting a final vote"""
        # Set up mock
        mock_make_api_call.return_value = "apple"
        
        # Create a sample debate log
        debate_log = [
            {
                "round": 1,
                "agent": "Agent1",
                "message": "I suggest we guess 'banana'.",
                "guess": "banana"
            },
            {
                "round": 2,
                "agent": "TestOperative",
                "message": "I think apple is better.",
                "guess": "apple"
            }
        ]
        
        # Set voting options
        options = ["apple", "banana", "end"]
        
        # Cast a final vote
        vote = self.agent.final_vote(debate_log, options, self.game_state, "fruit", 2)
        
        # Check that the API was called
        mock_make_api_call.assert_called_once()
        
        # Check the vote
        self.assertEqual(vote, "apple")


class TestDebateManager(unittest.TestCase):
    """Tests for the DebateManager class"""
    
    def setUp(self):
        """Set up test cases"""
        # Create a debate manager
        self.debate_manager = DebateManager(max_rounds=2)
        
        # Create a sample game state for testing
        board = [
            Card(word="apple", type=CardType.RED, revealed=False),
            Card(word="banana", type=CardType.RED, revealed=False),
            Card(word="cherry", type=CardType.BLUE, revealed=False),
            Card(word="date", type=CardType.BLUE, revealed=False),
            Card(word="elderberry", type=CardType.NEUTRAL, revealed=False),
            Card(word="fig", type=CardType.NEUTRAL, revealed=False),
            Card(word="grape", type=CardType.ASSASSIN, revealed=False),
        ]
        
        self.game_state = GameState(
            game_id="test_game",
            board=board,
            red_remaining=2,
            blue_remaining=2,
            current_team=CardType.RED
        )
    
    @patch.object(OperativeAgent, 'generate_guess')
    @patch.object(OperativeAgent, 'debate_response')
    @patch.object(OperativeAgent, 'final_vote')
    def test_run_debate(self, mock_final_vote, mock_debate_response, mock_generate_guess):
        """Test running a debate"""
        # Create mock agents
        agent1 = OperativeAgent(name="Agent1", team=CardType.RED)
        agent2 = OperativeAgent(name="Agent2", team=CardType.RED)
        
        # Set up mocks
        mock_generate_guess.side_effect = [
            ("apple", "Apple is a fruit"),
            ("banana", "Banana is also a fruit")
        ]
        mock_debate_response.side_effect = [
            "I still think apple is best",
            "I now agree apple is better than banana"
        ]
        mock_final_vote.side_effect = ["apple", "apple"]
        
        # Run the debate
        result = self.debate_manager.run_debate(
            [agent1, agent2],
            self.game_state,
            "fruit",
            2,
            0,
            []
        )
        
        # Check that the agents were called correctly
        self.assertEqual(mock_generate_guess.call_count, 2)
        self.assertEqual(mock_debate_response.call_count, 2)
        self.assertEqual(mock_final_vote.call_count, 2)
        
        # Check the result
        self.assertEqual(result["final_decision"], "apple")
        self.assertEqual(result["vote_counts"], {"apple": 2})
        self.assertEqual(len(result["debate_log"]), 4)  # 2 initial proposals + 2 debate responses
    
    def test_extract_preference(self):
        """Test extracting a preference from a message"""
        # Test explicit end turn mention
        message = "I think we should end the turn."
        preference = self.debate_manager._extract_preference(message, self.game_state)
        self.assertEqual(preference, "end")
        
        # Test quoted word
        message = "I think 'apple' is the best choice."
        preference = self.debate_manager._extract_preference(message, self.game_state)
        self.assertEqual(preference, "apple")
        
        # Test direct mention
        message = "Let's choose banana because it's yellow."
        preference = self.debate_manager._extract_preference(message, self.game_state)
        self.assertEqual(preference, "banana")
        
        # Test no clear preference
        message = "I'm not sure what to choose."
        preference = self.debate_manager._extract_preference(message, self.game_state)
        self.assertIsNone(preference)


if __name__ == "__main__":
    unittest.main()
