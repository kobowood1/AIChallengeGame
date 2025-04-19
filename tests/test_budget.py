"""
Unit tests for the game_data module's budget validation logic.
"""
import sys
import os
import pytest

# Add parent directory to path so we can import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_data import validate_package, MAX_BUDGET, POLICIES

def test_valid_selections():
    """Test valid policy selections within budget that have diverse options."""
    # Mix of level 1 and 2 options, within budget
    selections = {
        "Healthcare": 2,
        "Housing": 1,
        "Education": 2,
        "Environment": 1,
        "Defense": 2,
        "Infrastructure": 1,
        "Social Security": 2
    }
    is_valid, total_cost, error = validate_package(selections)
    assert is_valid is True
    assert total_cost == 11  # 3*2 + 4*1 = 6 + 5 = 11
    assert error == ""

def test_max_budget_selections():
    """Test valid selections exactly at the budget limit."""
    # Mix of level 1, 2, and 3 options, at max budget
    selections = {
        "Healthcare": 3,
        "Housing": 2,
        "Education": 3,
        "Environment": 1,
        "Defense": 2,
        "Infrastructure": 1,
        "Social Security": 2
    }
    is_valid, total_cost, error = validate_package(selections)
    assert is_valid is True
    assert total_cost == 14  # 2*3 + 3*2 + 2*1 = 6 + 6 + 2 = 14
    assert error == ""

def test_over_budget():
    """Test selections that exceed the maximum budget."""
    # Too many high-level options, exceeding budget
    selections = {
        "Healthcare": 3,
        "Housing": 3,
        "Education": 3,
        "Environment": 2,
        "Defense": 1,
        "Infrastructure": 2,
        "Social Security": 2
    }
    is_valid, total_cost, error = validate_package(selections)
    assert is_valid is False
    assert total_cost == 16  # 3*3 + 3*2 + 1*1 = 9 + 6 + 1 = 16
    assert "exceeds maximum budget" in error

def test_uniform_options():
    """Test selections where all policies have the same option level."""
    # All level 1 options
    all_level_1 = {
        "Healthcare": 1,
        "Housing": 1,
        "Education": 1,
        "Environment": 1,
        "Defense": 1,
        "Infrastructure": 1,
        "Social Security": 1
    }
    is_valid, total_cost, error = validate_package(all_level_1)
    assert is_valid is False
    assert total_cost == 7  # 7*1 = 7
    assert "same level" in error

    # All level 2 options
    all_level_2 = {
        "Healthcare": 2,
        "Housing": 2,
        "Education": 2,
        "Environment": 2,
        "Defense": 2,
        "Infrastructure": 2,
        "Social Security": 2
    }
    is_valid, total_cost, error = validate_package(all_level_2)
    assert is_valid is False
    assert total_cost == 14  # 7*2 = 14
    assert "same level" in error

def test_missing_policy():
    """Test selections with a missing policy."""
    incomplete_selections = {
        "Healthcare": 1,
        "Housing": 1,
        "Education": 1,
        # Missing Environment
        "Defense": 1,
        "Infrastructure": 1,
        "Social Security": 1
    }
    is_valid, total_cost, error = validate_package(incomplete_selections)
    assert is_valid is False
    assert "Missing selection" in error

def test_invalid_option_level():
    """Test selections with an invalid option level."""
    invalid_level = {
        "Healthcare": 1,
        "Housing": 1,
        "Education": 4,  # Invalid level
        "Environment": 1,
        "Defense": 1,
        "Infrastructure": 1,
        "Social Security": 1
    }
    is_valid, total_cost, error = validate_package(invalid_level)
    assert is_valid is False
    assert "Invalid option level" in error