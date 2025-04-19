"""
Game logic for the AI challenge game
"""
import random

class AIChallenge:
    """
    Represents an AI challenge game session
    """
    
    CHALLENGES = [
        {
            "prompt": "Write a function that counts occurrences of each character in a string",
            "test_cases": [
                {"input": "hello", "expected": {"h": 1, "e": 1, "l": 2, "o": 1}},
                {"input": "banana", "expected": {"b": 1, "a": 3, "n": 2}}
            ],
            "time_limit": 120,  # seconds
            "difficulty": "easy"
        },
        {
            "prompt": "Write a function that finds the largest palindrome in a string",
            "test_cases": [
                {"input": "babad", "expected": "bab"},
                {"input": "cbbd", "expected": "bb"}
            ],
            "time_limit": 180,
            "difficulty": "medium"
        },
        {
            "prompt": "Implement a function to find the shortest path in a grid with obstacles",
            "test_cases": [
                {
                    "input": {
                        "grid": [[0, 0, 0], [1, 1, 0], [0, 0, 0]], 
                        "start": [0, 0], 
                        "end": [2, 2]
                    }, 
                    "expected": 4
                }
            ],
            "time_limit": 240,
            "difficulty": "hard"
        }
    ]
    
    def __init__(self, room_id):
        """
        Initialize a new game session
        
        Args:
            room_id: Unique identifier for the game room
        """
        self.room_id = room_id
        self.players = {}
        self.current_challenge = None
        self.state = "waiting"  # waiting, active, finished
        self.start_time = None
        self.end_time = None
        self.winners = []
    
    def add_player(self, player_id, username):
        """
        Add a player to the game
        
        Args:
            player_id: Unique identifier for the player
            username: Display name for the player
        """
        self.players[player_id] = {
            "username": username,
            "score": 0,
            "submission": None,
            "submission_time": None,
            "status": "waiting"  # waiting, coding, submitted, verified
        }
        return self.players[player_id]
    
    def remove_player(self, player_id):
        """
        Remove a player from the game
        
        Args:
            player_id: Unique identifier for the player to remove
        """
        if player_id in self.players:
            del self.players[player_id]
    
    def start_game(self):
        """
        Start the game with a random challenge
        """
        if self.state == "waiting" and len(self.players) > 0:
            self.current_challenge = random.choice(self.CHALLENGES)
            self.state = "active"
            import time
            self.start_time = time.time()
            self.end_time = self.start_time + self.current_challenge["time_limit"]
            
            # Reset player statuses
            for player_id in self.players:
                self.players[player_id]["status"] = "coding"
                self.players[player_id]["submission"] = None
                self.players[player_id]["submission_time"] = None
            
            return self.current_challenge
        return None
    
    def submit_solution(self, player_id, solution):
        """
        Submit a solution for a player
        
        Args:
            player_id: ID of the player submitting
            solution: The code solution submitted
            
        Returns:
            Dictionary with submission status
        """
        import time
        current_time = time.time()
        
        if self.state != "active" or player_id not in self.players:
            return {"success": False, "message": "Invalid submission"}
        
        if current_time > self.end_time:
            return {"success": False, "message": "Time expired"}
        
        player = self.players[player_id]
        player["submission"] = solution
        player["submission_time"] = current_time
        player["status"] = "submitted"
        
        # For a realistic implementation, we would validate the solution here
        # For this demo, we'll simulate a successful submission
        submission_time = current_time - self.start_time
        score = max(0, self.current_challenge["time_limit"] - submission_time)
        player["score"] += int(score)
        
        # Check if all players have submitted
        all_submitted = all(p["status"] == "submitted" for p in self.players.values())
        if all_submitted:
            self.finish_game()
        
        return {
            "success": True, 
            "message": "Solution submitted", 
            "score": player["score"],
            "time_taken": submission_time
        }
    
    def finish_game(self):
        """
        End the current game and determine winners
        """
        if self.state == "active":
            self.state = "finished"
            
            # Determine winners (players with highest score)
            max_score = max([p["score"] for p in self.players.values()], default=0)
            self.winners = [
                player_id for player_id, player in self.players.items() 
                if player["score"] == max_score
            ]
            
            return {
                "winners": self.winners,
                "players": self.players
            }
        return None
    
    def get_game_state(self):
        """
        Get the current state of the game
        
        Returns:
            Dictionary with the current game state
        """
        import time
        current_time = time.time()
        
        return {
            "room_id": self.room_id,
            "state": self.state,
            "players": self.players,
            "current_challenge": self.current_challenge,
            "time_remaining": max(0, self.end_time - current_time) if self.state == "active" else 0,
            "winners": self.winners
        }

# Game room management
class GameManager:
    """
    Manages all active game rooms
    """
    def __init__(self):
        self.games = {}
        
    def create_game(self, room_id):
        """
        Create a new game room
        
        Args:
            room_id: Unique identifier for the room
            
        Returns:
            The created game instance
        """
        game = AIChallenge(room_id)
        self.games[room_id] = game
        return game
    
    def get_game(self, room_id):
        """
        Get a game by room ID
        
        Args:
            room_id: ID of the game room
            
        Returns:
            Game instance or None if not found
        """
        return self.games.get(room_id)
    
    def delete_game(self, room_id):
        """
        Delete a game room
        
        Args:
            room_id: ID of the game room to delete
        """
        if room_id in self.games:
            del self.games[room_id]

# Create a singleton instance of the game manager
game_manager = GameManager()
