"""
Content module for the AI CHALLENGE policy simulation game.

This module contains all game content data structures including scenario text,
policy areas with options, budget constraints, and game phase information.
The content is for the Republic of Bean refugee education policy simulation.
"""

from dataclasses import dataclass
from typing import List, Dict, Union, Any


@dataclass
class PolicyOption:
    """
    Represents a single policy option that can be selected for a policy area.

    Attributes:
        label: The display label for the option (e.g., "Option 1")
        summary: A brief description of the option (≤ 20 words)
        cost: The budget cost of implementing this option (integer 1-3)
    """
    label: str
    summary: str
    cost: int


@dataclass
class PolicyArea:
    """
    Represents a policy area with multiple available options.

    Attributes:
        name: The name of the policy area
        description: A one-sentence rationale for this policy area
        options: A list of three PolicyOption instances representing different approaches
    """
    name: str
    description: str
    options: List[PolicyOption]


# The backstory and context for the Republic of Bean policy simulation
SCENARIO_TEXT = """
The Republic of Bean, a small coastal nation, has experienced an unexpected 
influx of 50,000 refugees from neighboring Coffea due to civil unrest. As 
education policy advisors to the Bean Ministry of Education, you must develop 
an inclusive education strategy with limited resources.

Bean is known for its stable but modest economy, with education already 
accounting for 18% of the national budget. The refugees include approximately 
12,000 school-age children who need immediate educational support. Most speak 
a different primary language and have experienced significant trauma and 
disruption to their education.

Your task is to design a comprehensive refugee education policy package that 
balances the needs of the newcomers with those of Bean's citizens. Your 
decisions will affect social cohesion, economic development, and diplomatic 
relations with neighboring countries. The total cost of your policy package 
cannot exceed 14 budget units, and you must select options of different levels 
to create a nuanced approach.

As you deliberate, consider both immediate humanitarian needs and long-term
integration goals. Your recommendations will shape the future of both the 
refugee children and the Republic of Bean for generations to come.
"""

# Maximum budget allowed for the policy package
MAX_BUDGET = 14

# Policy areas with their descriptions and available options
POLICY_AREAS = [
    PolicyArea(
        name="Access to Education",
        description="Defines the integration model for refugee students in Bean's schools.",
        options=[
            PolicyOption(
                label="Option 1",
                summary="Separate refugee-only schools with basic curriculum.",
                cost=1
            ),
            PolicyOption(
                label="Option 2",
                summary="Partial integration with transitional classes before mainstreaming.",
                cost=2
            ),
            PolicyOption(
                label="Option 3",
                summary="Full integration into existing schools with supplementary support.",
                cost=3
            )
        ]
    ),
    PolicyArea(
        name="Language Instruction",
        description="Outlines strategies for addressing language barriers in refugee education.",
        options=[
            PolicyOption(
                label="Option 1",
                summary="Basic language survival courses primarily in native language.",
                cost=1
            ),
            PolicyOption(
                label="Option 2",
                summary="Intensive language immersion with bilingual teaching assistants.",
                cost=2
            ),
            PolicyOption(
                label="Option 3",
                summary="Comprehensive bilingual education with qualified staff.",
                cost=3
            )
        ]
    ),
    PolicyArea(
        name="Teacher Training",
        description="Prepares educators to effectively teach and support refugee students.",
        options=[
            PolicyOption(
                label="Option 1",
                summary="Basic orientation workshop for teachers on refugee backgrounds.",
                cost=1
            ),
            PolicyOption(
                label="Option 2",
                summary="Ongoing professional development on trauma-informed teaching.",
                cost=2
            ),
            PolicyOption(
                label="Option 3",
                summary="Comprehensive certification with mentoring and specialized staff.",
                cost=3
            )
        ]
    ),
    PolicyArea(
        name="Curriculum Adaptation",
        description="Adjusts educational content to meet refugee students' needs.",
        options=[
            PolicyOption(
                label="Option 1",
                summary="Minimal curriculum adjustments with supplementary materials.",
                cost=1
            ),
            PolicyOption(
                label="Option 2",
                summary="Modified curriculum with flexible assessment and cultural elements.",
                cost=2
            ),
            PolicyOption(
                label="Option 3",
                summary="Comprehensive curriculum redesign with student-centered approaches.",
                cost=3
            )
        ]
    ),
    PolicyArea(
        name="Psychosocial Support",
        description="Supports mental health and social-emotional needs of refugee students.",
        options=[
            PolicyOption(
                label="Option 1",
                summary="Basic teacher training on trauma recognition and referral.",
                cost=1
            ),
            PolicyOption(
                label="Option 2",
                summary="School counselors and regular group support sessions.",
                cost=2
            ),
            PolicyOption(
                label="Option 3",
                summary="Comprehensive mental health services with family support.",
                cost=3
            )
        ]
    ),
    PolicyArea(
        name="Financial Support",
        description="Provides material resources to refugee students and families.",
        options=[
            PolicyOption(
                label="Option 1",
                summary="Basic school supplies and textbook loan program.",
                cost=1
            ),
            PolicyOption(
                label="Option 2",
                summary="School materials plus transportation and meal subsidies.",
                cost=2
            ),
            PolicyOption(
                label="Option 3",
                summary="Full support including technology, uniforms, and family stipends.",
                cost=3
            )
        ]
    ),
    PolicyArea(
        name="Certification / Accreditation of Previous Education",
        description="Recognizes refugee students' prior learning and qualifications.",
        options=[
            PolicyOption(
                label="Option 1",
                summary="Basic skills assessment with minimal recognition of prior learning.",
                cost=1
            ),
            PolicyOption(
                label="Option 2",
                summary="Standardized equivalency exams with bridging courses for gaps.",
                cost=2
            ),
            PolicyOption(
                label="Option 3",
                summary="Comprehensive assessment with flexible pathways and plans.",
                cost=3
            )
        ]
    )
]


"""
Budget Rule:
The policy package must not exceed MAX_BUDGET (14 units).
Each policy area requires selecting exactly one option.
A balanced approach is required - players must select options of different levels
(cannot choose all Option 1s, all Option 2s, or all Option 3s) to create a more
nuanced and realistic policy package that addresses different aspects with 
varying levels of investment.
"""


# Game phases information
GAME_PHASES = {
    "phase1": {
        "title": "Individual Policy Selection",
        "duration_minutes": 20,
        "objective": "Select policy options within budget constraints for your package.",
        "actions": [
            "Review the Republic of Bean scenario and understand the constraints.",
            "Examine all seven policy areas and their available options.",
            "Select exactly one option for each policy area.",
            "Ensure your total budget does not exceed 14 units.",
            "Ensure you have a mix of different option levels (not all 1s, 2s, or 3s).",
            "Submit your individual policy package."
        ]
    },
    "phase2": {
        "title": "AI-Moderated Deliberation and Voting",
        "duration_minutes": 30,
        "objective": "Discuss options with AI citizens and reach consensus through voting.",
        "actions": [
            "Present your policy package to the group including AI representatives.",
            "Listen to feedback from AI citizens with diverse perspectives.",
            "Engage in discussion about trade-offs and priorities.",
            "Propose modifications based on deliberation.",
            "Participate in majority vote on the final policy package.",
            "In case of ties, a random tie-breaker will determine the outcome.",
            "Confirm that the agreed package maintains the budget limit of 14 units."
        ]
    },
    "phase3": {
        "title": "Reflection and Analysis",
        "duration_minutes": "participant-paced",
        "objective": "Reflect on decisions made and lessons learned from the process.",
        "actions": [
            "Review the final adopted policy package.",
            "Consider the strengths and weaknesses of the adopted approach.",
            "Reflect on the deliberation process and different perspectives presented.",
            "Answer guided reflection questions about your experience.",
            "Identify key insights about education policy and democratic deliberation.",
            "Submit your reflection responses."
        ]
    }
}

"""
Reflection Questions:

1. How did your initial policy package differ from the final adopted package? What 
   factors influenced these changes?

2. Which policy area generated the most debate during deliberation, and why do you 
   think this was the case?

3. How did you balance immediate humanitarian needs with long-term integration 
   goals in your policy decisions?

4. What perspectives did the AI representatives bring that you might not have 
   considered otherwise?

5. How did budget constraints affect your decision-making process? What trade-offs 
   were most difficult?

6. Which policy option do you believe will have the greatest positive impact, and 
   what evidence supports this?

7. How might the policy package be received differently by refugee families versus 
   long-term Bean residents?

8. What additional information would have helped you make more informed policy 
   decisions?

9. How did this exercise change your understanding of education policy challenges 
   in refugee contexts?

10. If you were to implement this policy package in reality, what additional 
    considerations or modifications would you suggest?
"""
