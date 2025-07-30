"""
Content moderation system for refugee education policy deliberation.
Detects harmful or exclusionary content and provides appropriate responses.
"""
import os
import logging
from openai import OpenAI

openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

class ContentModerator:
    """Handles content moderation for policy deliberation"""
    
    def __init__(self):
        self.moderation_keywords = [
            # Anti-migration terms
            'deport', 'go back', 'don\'t belong', 'invasion', 'flood', 'burden',
            'drain', 'threat', 'dangerous', 'criminal', 'illegal', 'unwanted',
            'take over', 'replace', 'invade', 'destroy', 'ruin', 'steal jobs',
            
            # Exclusionary language
            'separate schools', 'keep apart', 'not our problem', 'their fault',
            'can\'t integrate', 'cultural threat', 'language barrier excuse',
            'lower standards', 'waste resources', 'special treatment',
            
            # Discriminatory terms
            'inferior', 'primitive', 'backwards', 'uncivilized', 'savage',
            'terrorist', 'extremist', 'radicalize'
        ]
        
        self.constructive_responses = [
            "Let's focus on evidence-based solutions that work for all students in our education system.",
            "Research shows that inclusive policies benefit both refugee and local students. What specific concerns do you have about implementation?",
            "Our goal is to design policies that support successful integration while maintaining educational quality for everyone.",
            "Data from similar programs suggests that well-designed support systems improve outcomes for all students. How can we build on that?",
            "Let's consider the long-term benefits of education investment for our entire community.",
            "What specific educational outcomes are you hoping to achieve with your approach?"
        ]
    
    def analyze_content(self, message: str) -> dict:
        """
        Analyze user message for harmful content using AI moderation
        Returns: dict with 'is_harmful', 'severity', 'category', 'response'
        """
        try:
            # Use OpenAI's moderation endpoint for initial screening
            moderation_result = openai_client.moderations.create(input=message)
            flagged = moderation_result.results[0].flagged
            categories = moderation_result.results[0].categories
            
            # Check for policy-specific harmful content
            policy_harmful = self._check_policy_harmful_content(message)
            
            # Combine both checks
            is_harmful = flagged or policy_harmful['is_harmful']
            
            if is_harmful:
                # Generate contextual response
                response = self._generate_moderation_response(message, policy_harmful)
                return {
                    'is_harmful': True,
                    'severity': policy_harmful['severity'],
                    'category': policy_harmful['category'],
                    'response': response
                }
            else:
                return {
                    'is_harmful': False,
                    'severity': 'none',
                    'category': 'acceptable',
                    'response': None
                }
                
        except Exception as e:
            logging.error(f"Content moderation error: {e}")
            # If moderation fails, still check for basic harmful content
            policy_check = self._check_policy_harmful_content(message)
            if policy_check['is_harmful']:
                return {
                    'is_harmful': True,
                    'severity': policy_check['severity'],
                    'category': policy_check['category'],
                    'response': self._generate_fallback_response(policy_check['category'])
                }
            return {'is_harmful': False, 'severity': 'none', 'category': 'acceptable', 'response': None}
    
    def _check_policy_harmful_content(self, message: str) -> dict:
        """Check for policy-specific harmful content using keyword matching and AI analysis"""
        message_lower = message.lower()
        
        # Basic keyword check
        for keyword in self.moderation_keywords:
            if keyword in message_lower:
                severity = 'high' if keyword in ['deport', 'invasion', 'terrorist'] else 'medium'
                category = self._categorize_harmful_content(keyword)
                return {
                    'is_harmful': True,
                    'severity': severity,
                    'category': category,
                    'matched_keyword': keyword
                }
        
        # AI-based analysis for more nuanced detection
        try:
            analysis_prompt = f"""Analyze this message from a refugee education policy discussion for harmful, exclusionary, or discriminatory content:

Message: "{message}"

Determine if the message contains:
1. Anti-refugee sentiment
2. Exclusionary language toward refugees
3. Discriminatory attitudes
4. Dehumanizing language
5. Calls for segregation or exclusion

Respond with JSON: {{"is_harmful": boolean, "severity": "low/medium/high", "category": "category_name", "reasoning": "brief explanation"}}"""

            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a content moderator for educational policy discussions. Be precise and fair in your analysis."},
                    {"role": "user", "content": analysis_prompt}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            # Parse AI response (simplified - in production would use proper JSON parsing)
            ai_response = response.choices[0].message.content.lower()
            if '"is_harmful": true' in ai_response:
                if 'high' in ai_response:
                    severity = 'high'
                elif 'medium' in ai_response:
                    severity = 'medium'
                else:
                    severity = 'low'
                
                return {
                    'is_harmful': True,
                    'severity': severity,
                    'category': 'ai_detected',
                    'ai_analysis': ai_response
                }
        except Exception as e:
            logging.error(f"AI content analysis error: {e}")
        
        return {'is_harmful': False, 'severity': 'none', 'category': 'acceptable'}
    
    def _categorize_harmful_content(self, keyword: str) -> str:
        """Categorize harmful content by type"""
        anti_migration = ['deport', 'go back', 'invasion', 'flood', 'threat', 'dangerous']
        exclusionary = ['separate', 'keep apart', 'not our problem', 'can\'t integrate']
        discriminatory = ['inferior', 'primitive', 'backwards', 'terrorist']
        
        if keyword in anti_migration:
            return 'anti_migration'
        elif keyword in exclusionary:
            return 'exclusionary'
        elif keyword in discriminatory:
            return 'discriminatory'
        else:
            return 'harmful_language'
    
    def _generate_moderation_response(self, message: str, analysis: dict) -> str:
        """Generate contextual moderation response"""
        try:
            severity = analysis.get('severity', 'medium')
            category = analysis.get('category', 'harmful_language')
            
            if severity == 'high':
                tone = "firm but respectful"
                focus = "immediately redirect to constructive dialogue"
            else:
                tone = "gentle but clear"
                focus = "guide toward evidence-based discussion"
            
            prompt = f"""Generate a moderator response to address harmful content in a refugee education policy discussion.

Context:
- User message contained {category} content with {severity} severity
- This is an educational simulation about refugee integration policies
- Goal is to redirect to constructive, evidence-based policy discussion
- Tone should be {tone}
- Response should {focus}

Generate a 2-3 sentence response that:
1. Acknowledges the concern behind the message (if valid)
2. Gently redirects to constructive policy discussion
3. Refocuses on evidence-based solutions and shared values
4. Avoids being preachy or confrontational

Focus on the Republic of Bean simulation context and educational goals."""

            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a skilled educational moderator who maintains inclusive, constructive dialogue."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logging.error(f"Error generating moderation response: {e}")
            return self._generate_fallback_response(analysis.get('category', 'harmful_language'))
    
    def _generate_fallback_response(self, category: str) -> str:
        """Generate fallback response when AI generation fails"""
        responses = {
            'anti_migration': "I understand you have concerns. Let's focus on evidence-based education policies that work for everyone in our community. What specific educational outcomes are you hoping to achieve?",
            'exclusionary': "Our goal is to design policies that support all students while maintaining educational quality. What specific implementation challenges are you concerned about?",
            'discriminatory': "In the Republic of Bean, we're committed to evidence-based policies that serve all students effectively. Let's focus on practical solutions that benefit everyone.",
            'harmful_language': "Let's redirect our discussion to constructive policy solutions. What evidence-based approaches do you think would work best for our education system?",
            'ai_detected': "I'd like to refocus our discussion on collaborative policy solutions. What positive outcomes are you hoping to see from our education policies?"
        }
        
        return responses.get(category, responses['harmful_language'])

# Global moderator instance
content_moderator = ContentModerator()