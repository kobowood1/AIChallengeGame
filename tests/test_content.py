"""
Unit tests for the challenge_content module.
"""

import unittest
from challenge_content import POLICY_AREAS, MAX_BUDGET


class TestChallengeContent(unittest.TestCase):
    """Test cases for the challenge_content module."""

    def test_policy_areas_count(self):
        """Test that there are exactly 7 policy areas defined."""
        self.assertEqual(len(POLICY_AREAS), 7)

    def test_max_budget(self):
        """Test that the maximum budget is set to 14 units."""
        self.assertEqual(MAX_BUDGET, 14)

    def test_policy_options(self):
        """Test that each policy area has exactly 3 options."""
        for policy_area in POLICY_AREAS:
            self.assertEqual(len(policy_area.options), 3)

    def test_option_costs(self):
        """Test that option costs are between 1 and 3."""
        for policy_area in POLICY_AREAS:
            for option in policy_area.options:
                self.assertGreaterEqual(option.cost, 1)
                self.assertLessEqual(option.cost, 3)


if __name__ == "__main__":
    unittest.main()