"""
Policy utilities for canonical naming and mapping
"""

# Canonical policy area names used throughout the application
CANONICAL_POLICY_AREAS = {
    'Language Support': 'Language Support',
    'Language Instruction': 'Language Support',  # Map variant to canonical
    'Teacher Training': 'Teacher Training', 
    'School Integration': 'School Integration',
    'Psychosocial Support': 'Psychosocial Support',
    'Curriculum Adaptation': 'Curriculum Adaptation',
    'Access to Education': 'Access to Education',
    'Certification & Accreditation': 'Certification & Accreditation',
    'Certification / Accreditation of Previous Education': 'Certification & Accreditation',  # Map variant
    'Financial Support': 'Financial Support'
}

def normalize_policy_name(policy_name):
    """
    Normalize policy area names to canonical form
    
    Args:
        policy_name (str): Policy area name from any part of the system
        
    Returns:
        str: Canonical policy area name
    """
    return CANONICAL_POLICY_AREAS.get(policy_name, policy_name)

def get_policy_description(canonical_name):
    """
    Get standardized description for policy area
    
    Args:
        canonical_name (str): Canonical policy area name
        
    Returns:
        str: Policy area description
    """
    descriptions = {
        'Language Support': 'Programs to help refugee students learn the host country language',
        'Teacher Training': 'Preparing teachers to work effectively with refugee students', 
        'School Integration': 'Measures to incorporate refugee students into mainstream schools',
        'Psychosocial Support': 'Mental health services for refugee students dealing with trauma',
        'Curriculum Adaptation': 'Modifying educational content to be accessible and relevant to refugee students',
        'Access to Education': 'Ensuring refugee students can physically attend and enroll in schools',
        'Certification & Accreditation': 'Recognizing refugees\' prior education and helping them gain credentials',
        'Financial Support': 'Providing monetary assistance for refugee students\' educational needs'
    }
    
    return descriptions.get(canonical_name, f"Policy area: {canonical_name}")