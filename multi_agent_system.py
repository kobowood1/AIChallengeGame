"""
Multi-agent refugee education policy simulation system for the Republic of Bean.
Implements turn-based discussion with OpenAI and Google Gemini models.
"""
import os
import time
from typing import Dict, List, Optional, Tuple
from openai import OpenAI

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Initialize API clients
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

if GEMINI_AVAILABLE and os.environ.get("GOOGLE_API_KEY"):
    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

class Agent:
    """Represents an AI agent in the policy simulation"""
    
    def __init__(self, name: str, model_type: str, background: str, ideology: str):
        self.name = name
        self.model_type = model_type  # 'openai' or 'gemini'
        self.background = background
        self.ideology = ideology
        
        if model_type == 'gemini' and GEMINI_AVAILABLE:
            try:
                self.model = genai.GenerativeModel('gemini-1.5-flash')
            except Exception:
                self.model = None
                self.model_type = 'openai'  # Fallback to OpenAI
        else:
            self.model = None  # Will use OpenAI client directly

class MultiAgentSimulation:
    """Orchestrates the multi-agent policy simulation"""
    
    def __init__(self):
        self.agents = {
            'Amir': Agent(
                name='Amir',
                model_type='openai',
                background='Former teacher and refugee advocate with 15 years experience in education',
                ideology='Progressive - believes in comprehensive support and integration'
            ),
            'Salma': Agent(
                name='Salma',
                model_type='openai', 
                background='Education policy researcher and mother of three school-age children',
                ideology='Pragmatic - focuses on practical implementation and measurable outcomes'
            ),
            'Lila': Agent(
                name='Lila',
                model_type='gemini',
                background='School principal with experience managing diverse student populations',
                ideology='Collaborative - emphasizes community engagement and shared responsibility'
            ),
            'Leila': Agent(
                name='Leila',
                model_type='gemini',
                background='Social worker specializing in refugee family services and trauma-informed care',
                ideology='Humanitarian - prioritizes individual student needs and wellbeing'
            )
        }
        
        self.conversation_history = []
        self.current_policy_area = None
        self.policy_options = {}
        self.user_vote = None
        
    def set_policy_context(self, policy_area: str, options: Dict[str, Dict], user_vote: str):
        """Set the current policy discussion context"""
        self.current_policy_area = policy_area
        self.policy_options = options
        self.user_vote = user_vote
        
    def generate_openai_response(self, agent: Agent, context: str, conversation_history: List[str]) -> str:
        """Generate response using OpenAI"""
        system_prompt = f"""You are {agent.name}, participating in a refugee education policy simulation for the Republic of Bean.
        
Background: {agent.background}
Perspective: {agent.ideology}

Policy Area: {self.current_policy_area}
Available Options: {self.policy_options}
User's Previous Vote: {self.user_vote}

You must:
1. Share your perspective in exactly 1-2 sentences
2. Ask the user ONE direct question about their choice
3. Stop and wait for their response

Be conversational, authentic, and draw on your background. Focus on the policy implications."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context}
        ]
        
        # Add conversation history
        for msg in conversation_history[-6:]:  # Last 6 messages for context
            if "Agent:" in msg:
                messages.append({"role": "assistant", "content": msg})
            elif "User:" in msg:
                messages.append({"role": "user", "content": msg})
            
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=150,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    def generate_gemini_response(self, agent: Agent, context: str, conversation_history: List[str]) -> str:
        """Generate response using Google Gemini"""
        prompt = f"""You are {agent.name}, participating in a refugee education policy simulation for the Republic of Bean.

Background: {agent.background}
Perspective: {agent.ideology}

Policy Area: {self.current_policy_area}
Available Options: {self.policy_options}
User's Previous Vote: {self.user_vote}

Conversation so far:
{chr(10).join(conversation_history[-4:])}

Current context: {context}

You must:
1. Share your perspective in exactly 1-2 sentences
2. Ask the user ONE direct question about their choice
3. Stop and wait for their response

Be conversational, authentic, and draw on your background. Focus on the policy implications."""

        try:
            if agent.model:
                response = agent.model.generate_content(prompt)
                return response.text.strip()
            else:
                # Fallback to OpenAI if Gemini model not available
                return self.generate_openai_response(agent, context, conversation_history)
        except Exception as e:
            # Fallback to OpenAI if Gemini fails
            print(f"Gemini error for {agent.name}: {e}")
            return self.generate_openai_response(agent, context, conversation_history)
    
    def generate_agent_response(self, agent_name: str, context: str) -> str:
        """Generate response from specified agent"""
        agent = self.agents[agent_name]
        
        if agent.model_type == 'openai':
            response = self.generate_openai_response(agent, context, self.conversation_history)
        else:
            response = self.generate_gemini_response(agent, context, self.conversation_history)
        
        # Store in conversation history
        self.conversation_history.append(f"Agent {agent_name}: {response}")
        return response
    
    def generate_moderator_intro(self) -> str:
        """Generate moderator introduction using OpenAI"""
        system_prompt = """You are the Moderator for the Republic of Bean policy simulation. 
        
Generate a welcoming introduction for Phase 2: Group Discussion about Access to Education policy.
Mention that Amir will start the discussion by sharing his thoughts and asking a question.

Keep it professional but engaging, around 2-3 sentences."""

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Start Phase 2 discussion on {self.current_policy_area}. User voted: {self.user_vote}"}
            ],
            max_tokens=100,
            temperature=0.6
        )
        
        intro = response.choices[0].message.content.strip()
        self.conversation_history.append(f"Moderator: {intro}")
        return intro
    
    def generate_moderator_summary(self, user_responses: List[str]) -> str:
        """Generate final moderator summary and decision request"""
        system_prompt = """You are the Moderator. Summarize the key viewpoints from the discussion and ask for the final group recommendation.

Summarize what each agent contributed and then ask: "Which option do you choose as our final group recommendation?"

Keep it concise but comprehensive."""

        context = f"""
Policy Area: {self.current_policy_area}
Options: {self.policy_options}
User's initial vote: {self.user_vote}
User responses during discussion: {'; '.join(user_responses)}
Agent contributions: {'; '.join([msg for msg in self.conversation_history if 'Agent' in msg])}
"""

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context}
            ],
            max_tokens=200,
            temperature=0.6
        )
        
        summary = response.choices[0].message.content.strip()
        self.conversation_history.append(f"Moderator: {summary}")
        return summary
    
    def get_agent_response(self, agent_name: str, user_selections: Dict, conversation_history: List, policy_focus: str) -> str:
        """Get a response from a specific agent"""
        if agent_name not in self.agents:
            return f"Agent {agent_name} not found."
        
        agent = self.agents[agent_name]
        
        # Get the user's selection for the policy focus
        user_option = user_selections.get(policy_focus, 2)
        
        # Build context from conversation history
        context = ""
        if conversation_history:
            recent_messages = conversation_history[-3:]  # Last 3 messages
            context = "\n".join([f"{msg['sender']}: {msg['message']}" for msg in recent_messages])
        
        return self._get_agent_justification(agent, policy_focus, user_option, context)
    
    def _get_agent_justification(self, agent: Agent, policy_focus: str, user_option: int, context: str = "") -> str:
        """Generate agent justification for a policy choice"""
        prompt = f"""
As {agent.name}, respond to the user's policy choice.

Background: {agent.background}
Ideology: {agent.ideology}

Policy Area: {policy_focus}
User's Choice: Option {user_option}

Context from recent conversation:
{context}

Respond in character as {agent.name}. Be conversational, authentic, and reference the user's choice. Keep response to 2-3 sentences maximum.
"""
        
        try:
            if agent.model_type == 'openai':
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": f"You are {agent.name}. {agent.background}. {agent.ideology}"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=150,
                    temperature=0.7
                )
                return response.choices[0].message.content.strip()
            else:
                # Gemini
                if agent.model:
                    response = agent.model.generate_content(prompt)
                    return response.text.strip()
                else:
                    # Fallback to OpenAI
                    response = openai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": f"You are {agent.name}. {agent.background}. {agent.ideology}"},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=150,
                        temperature=0.7
                    )
                    return response.choices[0].message.content.strip()
        except Exception as e:
            return f"As {agent.name}, I appreciate your choice on {policy_focus}. This is an important decision that requires careful consideration of all stakeholders."
    
    def get_moderator_summary(self, conversation_history: List, user_selections: Dict) -> str:
        """Generate a moderator summary of the discussion"""
        try:
            # Build summary of discussion
            discussion_points = []
            for msg in conversation_history[-8:]:  # Last 8 messages
                if msg['sender'] in ['Amir', 'Salma', 'Lila', 'Leila']:
                    discussion_points.append(f"**Agent {msg['sender']}** {msg['message'][:150]}...")
            
            summary_text = "During the discussion, each agent provided valuable insights:\n\n" + "\n\n".join(discussion_points)
            summary_text += f"\n\nBased on this discussion, the group recommends proceeding with the proposed policy package."
            
            return summary_text
            
        except Exception as e:
            return "The agents have shared their perspectives on your policy choices. Based on the discussion, we recommend proceeding with a balanced approach that addresses the key concerns raised."

def create_policy_simulation_data():
    """Create sample policy data for testing"""
    return {
        "policy_area": "Access to Education",
        "options": {
            "1": {
                "name": "Immersion Approach",
                "cost": 1,
                "description": "Direct integration into mainstream classes with minimal additional support"
            },
            "2": {
                "name": "Transitional Bilingual Education", 
                "cost": 2,
                "description": "Temporary native language instruction while learning the host language"
            },
            "3": {
                "name": "Comprehensive Multilingual Program",
                "cost": 3,
                "description": "Full support in multiple languages with specialized curricula"
            },
            "4": {
                "name": "Integration with Quotas",
                "cost": 2, 
                "description": "Structured integration with enrollment quotas to ensure balance"
            }
        },
        "user_vote": "Integration with Quotas because it balances resource costs and inclusivity"
    }

# Example usage and testing
if __name__ == "__main__":
    # Test the simulation
    simulation = MultiAgentSimulation()
    
    # Set up policy context
    data = create_policy_simulation_data()
    simulation.set_policy_context(
        data["policy_area"],
        data["options"], 
        data["user_vote"]
    )
    
    print("=== Multi-Agent Policy Simulation Test ===")
    print(f"Policy Area: {data['policy_area']}")
    print(f"User Vote: {data['user_vote']}")
    print()
    
    # Test moderator intro
    intro = simulation.generate_moderator_intro()
    print(f"🟡 Moderator: {intro}")
    print()
    
    # Test agent responses
    agents_order = ['Amir', 'Salma', 'Lila', 'Leila']
    user_responses = []
    
    for agent_name in agents_order:
        agent_response = simulation.generate_agent_response(
            agent_name, 
            f"The user voted for {data['user_vote']}. Share your perspective and ask a question."
        )
        print(f"🟢 {agent_name}: {agent_response}")
        print(">> _(Please answer the question above to continue…)_")
        print()
        
        # Simulate user response
        mock_user_response = f"I appreciate {agent_name}'s perspective. Let me consider that viewpoint."
        user_responses.append(mock_user_response)
        simulation.conversation_history.append(f"User: {mock_user_response}")
    
    # Test moderator summary
    summary = simulation.generate_moderator_summary(user_responses)
    print(f"🟡 Moderator: {summary}")