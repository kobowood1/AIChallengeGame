"""
Conversation Orchestrator for Policy Deliberation

This module manages agent interactions, turn-taking, and ideological tension
in the policy simulation to create engaging deliberative experiences.
"""
import random
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from ai_agents import agent_justify
from policy_utils import normalize_policy_name, get_policy_description

class ConversationOrchestrator:
    """
    Orchestrates multi-agent policy deliberation with ideological tension
    """
    
    def __init__(self):
        """Initialize the orchestrator with policy stance definitions"""
        self.conversation_state = {
            'round': 1,
            'phase': 'introduction',
            'last_speaker': None,
            'pending_rebuttals': [],
            'policy_positions': {},
            'engagement_level': 'low'
        }
        
        # Define ideological stances for each policy area and option level  
        self.policy_stances = self._initialize_policy_stances()
        
        # Agent ideology mappings for opposition calculation
        self.ideology_spectrum = {
            'conservative': 1,
            'moderate': 2, 
            'liberal': 3,
            'humanitarian': 4,
            'socialist': 5,
            'neoliberal': 2.5
        }
        
    def _initialize_policy_stances(self) -> Dict[str, Dict[int, Dict[str, int]]]:
        """
        Initialize policy stance matrix for each policy area and option level
        Returns stance scores (-2 to +2) for different ideological dimensions
        """
        return {
            "Language Support": {
                1: {"fiscal": 2, "individualist": 1, "pragmatic": 1},  # Basic, cheap approach
                2: {"fiscal": 0, "individualist": 0, "pragmatic": 2},  # Balanced approach  
                3: {"fiscal": -2, "individualist": -1, "pragmatic": 1}  # Comprehensive, expensive
            },
            "Teacher Training": {
                1: {"fiscal": 2, "quality": -1, "systemic": -1},
                2: {"fiscal": 0, "quality": 1, "systemic": 0},
                3: {"fiscal": -2, "quality": 2, "systemic": 2}
            },
            "School Integration": {
                1: {"assimilation": 2, "diversity": -1, "resources": 1},
                2: {"assimilation": 0, "diversity": 1, "resources": 0},
                3: {"assimilation": -1, "diversity": 2, "resources": -2}
            },
            "Psychosocial Support": {
                1: {"individualist": 2, "medicalized": -1, "fiscal": 2},
                2: {"individualist": 0, "medicalized": 1, "fiscal": 0},
                3: {"individualist": -2, "medicalized": 2, "fiscal": -2}
            },
            "Curriculum Adaptation": {
                1: {"standardization": 2, "cultural": -2, "fiscal": 2},
                2: {"standardization": 0, "cultural": 0, "fiscal": 0},
                3: {"standardization": -2, "cultural": 2, "fiscal": -2}
            },
            "Access to Education": {
                1: {"meritocratic": 2, "systemic": -2, "fiscal": 2},
                2: {"meritocratic": 0, "systemic": 0, "fiscal": 0},
                3: {"meritocratic": -2, "systemic": 2, "fiscal": -2}
            },
            "Financial Support": {
                1: {"fiscal": 2, "individualist": 1, "targeted": 2},
                2: {"fiscal": 0, "individualist": 0, "targeted": 0},
                3: {"fiscal": -2, "individualist": -1, "targeted": -1}
            }
        }
    
    def assign_agent_stances(self, agents: List[Dict]) -> List[Dict]:
        """
        Assign ideological stances to agents based on their ideology and create position preferences
        """
        enhanced_agents = []
        
        for agent in agents:
            enhanced_agent = agent.copy()
            ideology = agent.get('ideology', 'moderate').lower()
            
            # Assign stance preferences based on ideology
            enhanced_agent['stance_preferences'] = self._get_ideology_stances(ideology)
            enhanced_agent['policy_positions'] = {}
            enhanced_agent['speaking_style'] = self._get_speaking_style(ideology)
            enhanced_agent['conflict_tendency'] = self._get_conflict_tendency(ideology)
            
            enhanced_agents.append(enhanced_agent)
        
        return enhanced_agents
    
    def _get_ideology_stances(self, ideology: str) -> Dict[str, int]:
        """Get stance preferences for an ideology (-2 to +2 scale)"""
        stance_profiles = {
            'conservative': {
                'fiscal': 2, 'individualist': 1, 'traditional': 2, 'pragmatic': 1,
                'meritocratic': 2, 'standardization': 1, 'assimilation': 1
            },
            'liberal': {
                'fiscal': -1, 'individualist': -1, 'diversity': 2, 'systemic': 1,
                'cultural': 1, 'quality': 1, 'resources': -1
            },
            'moderate': {
                'fiscal': 0, 'individualist': 0, 'pragmatic': 2, 'quality': 1,
                'systemic': 0, 'standardization': 0
            },
            'humanitarian': {
                'fiscal': -2, 'individualist': -2, 'diversity': 2, 'cultural': 2,
                'systemic': 1, 'quality': 2, 'resources': -2
            },
            'socialist': {
                'fiscal': -2, 'individualist': -2, 'systemic': 2, 'resources': -2,
                'diversity': 1, 'quality': 2, 'standardization': -1
            },
            'neoliberal': {
                'fiscal': 1, 'individualist': 1, 'meritocratic': 1, 'pragmatic': 2,
                'standardization': 1, 'targeted': 1
            }
        }
        
        return stance_profiles.get(ideology, stance_profiles['moderate'])
    
    def _get_speaking_style(self, ideology: str) -> str:
        """Get characteristic speaking style for ideology"""
        styles = {
            'conservative': 'direct_practical',
            'liberal': 'passionate_equity',
            'moderate': 'diplomatic_balanced',
            'humanitarian': 'empathetic_personal',
            'socialist': 'analytical_systemic',
            'neoliberal': 'efficient_market'
        }
        return styles.get(ideology, 'professional_neutral')
    
    def _get_conflict_tendency(self, ideology: str) -> float:
        """Get likelihood of agent to engage in disagreement (0.0-1.0)"""
        tendencies = {
            'conservative': 0.8,  # High tendency to push back
            'liberal': 0.9,      # Very high tendency to challenge
            'moderate': 0.4,     # Lower tendency, prefers compromise
            'humanitarian': 0.6,  # Moderate, passionate about values
            'socialist': 0.9,    # High tendency to challenge systemic issues
            'neoliberal': 0.7    # High tendency to defend efficiency
        }
        return tendencies.get(ideology, 0.5)
    
    def classify_input_substance(self, message: str) -> Dict[str, Any]:
        """
        Classify player input for substance and intent
        
        Returns dict with:
        - is_substantive: bool
        - intent: str (agreement, disagreement, question, vague, irrelevant)
        - needs_clarification: bool
        - detected_stance: Optional[str]
        """
        message_lower = message.lower().strip()
        
        # Check for very short or vague responses
        if len(message_lower) < 10 or message_lower in ['ok', 'sure', 'idk', 'maybe', 'whatever']:
            return {
                'is_substantive': False,
                'intent': 'vague',
                'needs_clarification': True,
                'detected_stance': None,
                'clarification_prompt': 'Could you explain your reasoning in more detail?'
            }
        
        # Check for irrelevant content
        irrelevant_patterns = [
            r'(lol|haha|😂|funny)', 
            r'(weather|sports|food)',
            r'^[!@#$%^&*()]+$',
            r'(test|testing|hello world)'
        ]
        
        if any(re.search(pattern, message_lower) for pattern in irrelevant_patterns):
            return {
                'is_substantive': False,
                'intent': 'irrelevant', 
                'needs_clarification': True,
                'detected_stance': None,
                'clarification_prompt': 'Let\'s focus on the policy discussion. What are your thoughts on this education policy option?'
            }
        
        # Check for agreement/disagreement patterns
        agreement_patterns = [r'(agree|good point|right|yes|support)', r'(like this|makes sense)']
        disagreement_patterns = [r'(disagree|wrong|bad idea|no|against)', r'(don\'t think|not sure about)']
        
        intent = 'neutral'
        if any(re.search(pattern, message_lower) for pattern in agreement_patterns):
            intent = 'agreement'
        elif any(re.search(pattern, message_lower) for pattern in disagreement_patterns):
            intent = 'disagreement'
        elif '?' in message:
            intent = 'question'
        
        # Policy-specific stance detection
        detected_stance = None
        if 'cost' in message_lower or 'budget' in message_lower or 'expensive' in message_lower:
            detected_stance = 'fiscal'
        elif 'equity' in message_lower or 'fair' in message_lower or 'justice' in message_lower:
            detected_stance = 'systemic'
        elif 'culture' in message_lower or 'diversity' in message_lower:
            detected_stance = 'cultural'
        
        return {
            'is_substantive': len(message_lower) > 15,
            'intent': intent,
            'needs_clarification': False,
            'detected_stance': detected_stance,
            'clarification_prompt': None
        }
    
    def calculate_ideological_distance(self, agent1: Dict, agent2: Dict) -> float:
        """Calculate ideological distance between two agents (0.0-1.0)"""
        ideology1 = agent1.get('ideology', 'moderate').lower()
        ideology2 = agent2.get('ideology', 'moderate').lower()
        
        pos1 = self.ideology_spectrum.get(ideology1, 2.5)
        pos2 = self.ideology_spectrum.get(ideology2, 2.5)
        
        # Normalize distance to 0-1 scale
        max_distance = 4.0  # socialist(5) to conservative(1)
        return abs(pos1 - pos2) / max_distance
    
    def select_responding_agents(self, agents: List[Dict], player_input: Dict, 
                               policy_area: str, current_speakers: List[str]) -> List[Dict]:
        """
        Select which agents should respond based on input analysis and ideological positions
        
        Returns list of agents that should respond, ordered by response type (aligned, opposed)
        """
        input_analysis = player_input
        available_agents = [a for a in agents if a['name'] not in current_speakers[-2:]]
        
        if len(available_agents) < 2:
            available_agents = agents  # Reset if we've cycled through everyone
        
        selected_agents = []
        
        if input_analysis['needs_clarification']:
            # Select most diplomatic agent for clarification
            diplomatic_agent = min(available_agents, 
                                 key=lambda a: a.get('conflict_tendency', 0.5))
            selected_agents.append({**diplomatic_agent, 'response_type': 'clarification'})
            
        else:
            # Select one aligned and one opposed agent
            player_stance = input_analysis.get('detected_stance')
            
            if player_stance and input_analysis['intent'] in ['agreement', 'disagreement']:
                # Find agents with different stance preferences
                aligned_agents = []
                opposed_agents = []
                
                for agent in available_agents:
                    agent_stance_pref = agent.get('stance_preferences', {}).get(player_stance, 0)
                    
                    if input_analysis['intent'] == 'agreement':
                        if agent_stance_pref > 0:
                            aligned_agents.append(agent)
                        elif agent_stance_pref < 0:
                            opposed_agents.append(agent)
                    else:  # disagreement
                        if agent_stance_pref < 0:
                            aligned_agents.append(agent)
                        elif agent_stance_pref > 0:
                            opposed_agents.append(agent)
                
                # Select one from each group
                if aligned_agents:
                    selected_agents.append({**random.choice(aligned_agents), 'response_type': 'agreement'})
                if opposed_agents and random.random() < 0.8:  # 80% chance of opposition
                    selected_agents.append({**random.choice(opposed_agents), 'response_type': 'disagreement'})
            
            # If no specific stance detected or no agents found, select by ideological distance
            if len(selected_agents) < 2:
                remaining_agents = [a for a in available_agents 
                                  if not any(a['name'] == s['name'] for s in selected_agents)]
                
                if len(remaining_agents) >= 2:
                    # Sort by conflict tendency and ideological diversity
                    conflict_agents = sorted(remaining_agents, 
                                           key=lambda a: a.get('conflict_tendency', 0.5), reverse=True)
                    
                    # Add high-conflict agent
                    if conflict_agents and len(selected_agents) < 2:
                        selected_agents.append({**conflict_agents[0], 'response_type': 'challenge'})
                    
                    # Add ideologically distant agent for debate
                    if len(conflict_agents) > 1 and len(selected_agents) < 2:
                        distant_agent = max(conflict_agents[1:], 
                                          key=lambda a: self.calculate_ideological_distance(conflict_agents[0], a))
                        selected_agents.append({**distant_agent, 'response_type': 'counter'})
        
        return selected_agents[:2]  # Limit to 2 responses per turn
    
    def generate_orchestrated_responses(self, selected_agents: List[Dict], policy_area: str, 
                                      option_chosen: int, player_message: str, 
                                      recent_messages: List[Dict]) -> List[Dict]:
        """
        Generate agent responses with enhanced prompts for interaction and conflict
        """
        responses = []
        
        for i, agent_config in enumerate(selected_agents):
            agent = {k: v for k, v in agent_config.items() if k != 'response_type'}
            response_type = agent_config.get('response_type', 'neutral')
            
            # Check if this agent is responding to the previous agent
            responding_to_agent = None
            if i > 0:
                responding_to_agent = {k: v for k, v in selected_agents[i-1].items() if k != 'response_type'}
            
            # Generate enhanced response
            response = self._generate_enhanced_agent_response(
                agent, policy_area, option_chosen, player_message,
                recent_messages, response_type, responding_to_agent
            )
            
            responses.append({
                'agent': agent,
                'message': response,
                'response_type': response_type,
                'responding_to': responding_to_agent['name'] if responding_to_agent else None
            })
        
        return responses
    
    def _generate_enhanced_agent_response(self, agent: Dict, policy_area: str, 
                                        option_chosen: int, player_message: str,
                                        recent_messages: List[Dict], response_type: str,
                                        responding_to_agent: Optional[Dict]) -> str:
        """Generate agent response with enhanced interactive prompts"""
        
        # Enhanced prompts based on response type
        interaction_prompts = {
            'clarification': f"""
The player gave a vague response: "{player_message}"

You need to ask a specific follow-up question to understand their position better. 
Be diplomatic but direct. Ask about their reasoning or what specific aspect they're considering.
End your response with a clear question that helps the discussion move forward.
""",
            'agreement': f"""
The player said: "{player_message}"

You generally agree with this perspective. Build on their point and add your own supporting reasoning.
Start with something like "I agree with that because..." or "That's a good point, and I'd add..."
Then ask a follow-up question to deepen the discussion.
""",
            'disagreement': f"""
The player said: "{player_message}"

You disagree with this perspective based on your background and ideology.
Start with respectful disagreement like "I see it differently because..." or "I have to respectfully disagree..."
Explain your reasoning and end with a question that challenges their assumption.
""",
            'challenge': f"""
The player said: "{player_message}"

Push back on their reasoning and challenge them to think more deeply.
Use phrases like "Have you considered..." or "But what about..." 
Be assertive but professional. End with a probing question.
""",
            'counter': f"""
{responding_to_agent['name'] if responding_to_agent else 'Another participant'} just made a point, and the player said: "{player_message}"

You have a different perspective from both. Address both the previous response and the player's message.
Use the other participant's name and directly engage with their argument.
Create some ideological tension by explaining your different viewpoint.
"""
        }
        
        # Use the enhanced prompt or fall back to original system
        enhanced_prompt = interaction_prompts.get(response_type, "")
        
        try:
            # Call the enhanced agent_justify function with interaction context
            return agent_justify(
                policy_domain=policy_area,
                option_chosen=option_chosen,
                agent=agent,
                user_message=f"{enhanced_prompt}\n\nPlayer message: {player_message}",
                recent_messages=recent_messages,
                responding_to_agent=responding_to_agent
            )
        except Exception as e:
            logging.error(f"Error generating enhanced response: {e}")
            # Fallback to rule-based response
            return self._generate_fallback_response(agent, response_type, player_message)
    
    def _generate_fallback_response(self, agent: Dict, response_type: str, player_message: str) -> str:
        """Generate rule-based fallback responses when AI is unavailable"""
        
        name = agent.get('name', 'Participant')
        ideology = agent.get('ideology', 'moderate')
        
        fallback_responses = {
            'clarification': [
                f"Could you elaborate on that? I want to make sure I understand your perspective.",
                f"What specific aspect are you most concerned about?",
                f"Can you help me understand your reasoning behind that?"
            ],
            'agreement': [
                f"I agree with your point. From my {ideology} perspective, this makes sense because we need practical solutions.",
                f"That's exactly right. My experience as a {agent.get('occupation', 'community member')} supports that view.",
                f"You've raised an important point that aligns with my values."
            ],
            'disagreement': [
                f"I respectfully disagree. As someone with {ideology} views, I think we need to consider the broader implications.",
                f"I see it differently. My background as a {agent.get('occupation', 'community member')} has shown me that approach has limitations.",
                f"That's an interesting perspective, but I'm concerned about the unintended consequences."
            ],
            'challenge': [
                f"Have you considered how this would affect the most vulnerable students?",
                f"But what about the long-term sustainability of that approach?",
                f"That sounds good in theory, but how would it work in practice?"
            ],
            'counter': [
                f"I see both perspectives, but I think we're missing a key factor here.",
                f"While I understand the previous points, my {ideology} viewpoint suggests a different approach.",
                f"This is exactly the kind of disagreement that makes these discussions valuable. Here's my take..."
            ]
        }
        
        responses = fallback_responses.get(response_type, fallback_responses['clarification'])
        return random.choice(responses)
    
    def should_facilitate_summary(self, conversation_length: int) -> bool:
        """Determine if a facilitator summary is needed"""
        return conversation_length > 0 and conversation_length % 6 == 0
    
    def generate_facilitator_summary(self, recent_messages: List[Dict], policy_area: str) -> str:
        """Generate a facilitator summary and next question"""
        
        # Count different perspectives mentioned
        participants = set()
        key_themes = []
        
        for msg in recent_messages[-6:]:
            sender = msg.get('sender', '')
            message = msg.get('message', '').lower()
            participants.add(sender)
            
            # Extract key themes
            if 'cost' in message or 'budget' in message:
                key_themes.append('funding concerns')
            if 'equity' in message or 'fair' in message:
                key_themes.append('equity issues')
            if 'practical' in message or 'implementation' in message:
                key_themes.append('implementation challenges')
        
        unique_themes = list(set(key_themes))
        
        summary = f"""
Let me summarize our discussion on {policy_area}:

We've heard from {len(participants)} participants with different perspectives on this policy.
Key themes that have emerged include: {', '.join(unique_themes) if unique_themes else 'various concerns about implementation and effectiveness'}.

The discussion shows the complexity of this issue and the different values we each bring to policy-making.

Now I'd like to focus our next discussion: Given what we've heard, what do you think would be the biggest challenge in implementing any of these approaches, and how might we address it?
"""
        
        return summary.strip()