"""
Game logic for the policy-making deliberation game
"""
import random

class AIChallenge:
    """
    Represents a policy deliberation session with AI agent participants
    """
    
    CHALLENGES = [
        {
            "prompt": "Develop a comprehensive refugee education policy for the Republic of Bean",
            "description": "As policy advisors for the Republic of Bean, you must develop an education policy that addresses the influx of refugees. Your policy should balance budget constraints while ensuring both refugee and citizen students receive quality education.",
            "time_limit": 1800,  # 30 minutes for discussion
            "policy_domains": [
                "Language Support", 
                "Teacher Training", 
                "School Integration", 
                "Psychosocial Support", 
                "Curriculum Adaptation"
            ],
            "difficulty": "policy"
        }
    ]
    
    def __init__(self, room_id):
        """
        Initialize a new policy deliberation session
        
        Args:
            room_id: Unique identifier for the policy deliberation room
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
        Add a policy advisor to the deliberation session
        
        Args:
            player_id: Unique identifier for the policy advisor
            username: Display name for the policy advisor
        """
        self.players[player_id] = {
            "username": username,
            "score": 0,
            "submission": None,
            "submission_time": None,
            "status": "waiting"  # waiting, deliberating, submitted, verified
        }
        return self.players[player_id]
    
    def remove_player(self, player_id):
        """
        Remove a policy advisor from the deliberation session
        
        Args:
            player_id: Unique identifier for the policy advisor to remove
        """
        if player_id in self.players:
            del self.players[player_id]
    
    def start_game(self):
        """
        Start the policy deliberation session with a challenge
        """
        if self.state == "waiting" and len(self.players) > 0:
            self.current_challenge = random.choice(self.CHALLENGES)
            self.state = "active"
            import time
            self.start_time = time.time()
            self.end_time = self.start_time + self.current_challenge["time_limit"]
            
            # Reset player statuses
            for player_id in self.players:
                self.players[player_id]["status"] = "deliberating"
                self.players[player_id]["submission"] = None
                self.players[player_id]["submission_time"] = None
            
            return self.current_challenge
        return None
    
    def submit_solution(self, player_id, solution):
        """
        Submit a policy proposal from a policy advisor
        
        Args:
            player_id: ID of the policy advisor submitting
            solution: The policy proposal text submitted
            
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
        
        # For a realistic implementation, we would validate the policy proposal here
        # For this demo, we'll simulate a successful policy proposal submission
        submission_time = current_time - self.start_time
        score = max(0, self.current_challenge["time_limit"] - submission_time)
        player["score"] += int(score)
        
        # Check if all policy advisors have submitted their proposals
        all_submitted = all(p["status"] == "submitted" for p in self.players.values())
        if all_submitted:
            self.finish_game()
        
        return {
            "success": True, 
            "message": "Policy proposal submitted", 
            "score": player["score"],
            "time_taken": submission_time
        }
    
    def finish_game(self):
        """
        End the current policy deliberation session and determine winners
        """
        if self.state == "active":
            self.state = "finished"
            
            # Determine leading policy advisors (those with highest evaluation scores)
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
        Get the current state of the policy deliberation session
        
        Returns:
            Dictionary with the current deliberation state
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

# Policy session management
class GameManager:
    """
    Manages all active policy deliberation sessions
    """
    def __init__(self):
        self.games = {}
        
    def create_game(self, room_id):
        """
        Create a new policy deliberation session
        
        Args:
            room_id: Unique identifier for the session room
            
        Returns:
            The created policy deliberation instance
        """
        game = AIChallenge(room_id)
        self.games[room_id] = game
        return game
    
    def get_game(self, room_id):
        """
        Get a policy deliberation session by room ID
        
        Args:
            room_id: ID of the policy deliberation room
            
        Returns:
            Policy deliberation instance or None if not found
        """
        return self.games.get(room_id)
    
    def delete_game(self, room_id):
        """
        Delete a policy deliberation session
        
        Args:
            room_id: ID of the policy deliberation room to delete
        """
        if room_id in self.games:
            del self.games[room_id]

# Create a singleton instance of the policy deliberation manager
game_manager = GameManager()
