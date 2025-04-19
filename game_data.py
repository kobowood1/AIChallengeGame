"""
Data module that contains policy information and budget validation logic.
"""

# Maximum budget available to spend on policy options
MAX_BUDGET = 14

# Policy data with names and options
POLICIES = [
    {
        "name": "Healthcare",
        "options": [
            {"level": 1, "description": "Basic Government Insurance", "cost": 1},
            {"level": 2, "description": "Universal Healthcare", "cost": 2},
            {"level": 3, "description": "Premium Healthcare For All", "cost": 3}
        ]
    },
    {
        "name": "Housing",
        "options": [
            {"level": 1, "description": "Basic Social Housing", "cost": 1},
            {"level": 2, "description": "Affordable Housing Program", "cost": 2},
            {"level": 3, "description": "Universal Housing Guarantee", "cost": 3}
        ]
    },
    {
        "name": "Education",
        "options": [
            {"level": 1, "description": "Basic Public Schools", "cost": 1},
            {"level": 2, "description": "Enhanced Education Access", "cost": 2},
            {"level": 3, "description": "Premier Education For All", "cost": 3}
        ]
    },
    {
        "name": "Environment",
        "options": [
            {"level": 1, "description": "Basic Environmental Regulations", "cost": 1},
            {"level": 2, "description": "Green Energy Incentives", "cost": 2},
            {"level": 3, "description": "Carbon Neutrality Initiative", "cost": 3}
        ]
    },
    {
        "name": "Defense",
        "options": [
            {"level": 1, "description": "Basic National Defense", "cost": 1},
            {"level": 2, "description": "Regional Military Presence", "cost": 2},
            {"level": 3, "description": "Global Military Dominance", "cost": 3}
        ]
    },
    {
        "name": "Infrastructure",
        "options": [
            {"level": 1, "description": "Basic Infrastructure Maintenance", "cost": 1},
            {"level": 2, "description": "Major Infrastructure Investment", "cost": 2},
            {"level": 3, "description": "State-of-the-Art Infrastructure", "cost": 3}
        ]
    },
    {
        "name": "Social Security",
        "options": [
            {"level": 1, "description": "Basic Safety Net", "cost": 1},
            {"level": 2, "description": "Comprehensive Social Security", "cost": 2},
            {"level": 3, "description": "Universal Basic Income", "cost": 3}
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