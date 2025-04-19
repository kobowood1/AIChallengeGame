"""
Data module that contains policy information and budget validation logic.
"""

# Maximum budget available to spend on policy options
MAX_BUDGET = 14

# Policy data with names and options
POLICIES = [
    {
        "name": "Access to Education",
        "options": [
            {"level": 1, "description": "Limited Integration: Separate refugee-only schools with basic resources", "cost": 1},
            {"level": 2, "description": "Partial Integration: Mixed schools with special refugee classes", "cost": 2},
            {"level": 3, "description": "Full Integration: Complete inclusion in mainstream schools with support", "cost": 3}
        ]
    },
    {
        "name": "Language Instruction",
        "options": [
            {"level": 1, "description": "Basic Classes: Minimal language support provided separately", "cost": 1},
            {"level": 2, "description": "Enhanced Program: Regular language classes with trained teachers", "cost": 2},
            {"level": 3, "description": "Comprehensive Approach: Immersive bilingual education with cultural components", "cost": 3}
        ]
    },
    {
        "name": "Teacher Training",
        "options": [
            {"level": 1, "description": "Basic Guidelines: Simple materials on refugee education", "cost": 1},
            {"level": 2, "description": "Training Workshops: Regular professional development sessions", "cost": 2},
            {"level": 3, "description": "Specialized Certification: Comprehensive diversity and trauma-informed preparation", "cost": 3}
        ]
    },
    {
        "name": "Curriculum Adaptation",
        "options": [
            {"level": 1, "description": "Minor Adjustments: Some supplementary refugee-relevant materials", "cost": 1},
            {"level": 2, "description": "Partial Reforms: Modified curriculum with inclusive content", "cost": 2},
            {"level": 3, "description": "Complete Redesign: Fully inclusive, culturally responsive learning materials", "cost": 3}
        ]
    },
    {
        "name": "Psychosocial Support",
        "options": [
            {"level": 1, "description": "Basic Counseling: Limited mental health resources on request", "cost": 1},
            {"level": 2, "description": "Support Program: Regular counseling and group therapy options", "cost": 2},
            {"level": 3, "description": "Comprehensive Care: Trauma-informed schools with on-site specialists", "cost": 3}
        ]
    },
    {
        "name": "Financial Support",
        "options": [
            {"level": 1, "description": "Basic Supplies: Essential educational materials provided", "cost": 1},
            {"level": 2, "description": "Scholarship Program: Tuition assistance and stipends for eligible students", "cost": 2},
            {"level": 3, "description": "Full Support Package: Comprehensive financial aid covering all education costs", "cost": 3}
        ]
    },
    {
        "name": "Certification & Accreditation",
        "options": [
            {"level": 1, "description": "Limited Recognition: Basic skills assessment without formal equivalency", "cost": 1},
            {"level": 2, "description": "Partial Recognition: Standardized testing for placement and limited recognition", "cost": 2},
            {"level": 3, "description": "Comprehensive System: Full recognition of prior learning with bridging programs", "cost": 3}
        ]
    }
]

def validate_package(selection_dict):
    """
    Validate a package of policy selections against budget constraints and option diversity.
    
    Args:
        selection_dict: Dictionary mapping policy names to selected option levels (1, 2, or 3)
        
    Returns:
        Tuple containing (is_valid, total_cost, error_message)
        - is_valid: Boolean indicating if the selection is valid
        - total_cost: Integer representing the total cost of selections
        - error_message: String with error details if invalid, empty string if valid
    """
    # Check if all required policies are selected
    for policy in POLICIES:
        if policy["name"] not in selection_dict:
            return False, 0, f"Missing selection for policy: {policy['name']}"
    
    # Check if all selections are valid option levels
    for policy_name, option_level in selection_dict.items():
        if option_level not in [1, 2, 3]:
            return False, 0, f"Invalid option level ({option_level}) for policy: {policy_name}"
    
    # Calculate total cost
    total_cost = 0
    for policy in POLICIES:
        policy_name = policy["name"]
        option_level = selection_dict[policy_name]
        # Find the cost for this option level
        option_cost = next(option["cost"] for option in policy["options"] if option["level"] == option_level)
        total_cost += option_cost
    
    # Check if within budget
    if total_cost > MAX_BUDGET:
        return False, total_cost, f"Total cost ({total_cost}) exceeds maximum budget ({MAX_BUDGET})"
    
    # Check if all selections are the same level
    unique_levels = set(selection_dict.values())
    if len(unique_levels) == 1:
        level = next(iter(unique_levels))
        return False, total_cost, f"All selections are the same level ({level}). More diversity is required."
    
    # If we got here, everything is valid
    return True, total_cost, ""