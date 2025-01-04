import unittest
from src.utils.helpers import ModelInfo, calculate_api_cost

class TestCostUtilities(unittest.TestCase):
    def test_basic_input_output_costs(self):
        model_info = ModelInfo(
            name="test-model",
            provider="test-provider",
            max_tokens=8192,
            context_window=200_000,
            supports_images=False,
            supports_computer_use=False,
            supports_prompt_cache=False,
            input_price=3.0,
            output_price=15.0
        )
        
        cost = calculate_api_cost(model_info, 1000, 500)
        # Input: (3.0 / 1_000_000) * 1000 = 0.003
        # Output: (15.0 / 1_000_000) * 500 = 0.0075
        # Total: 0.003 + 0.0075 = 0.0105
        self.assertAlmostEqual(cost, 0.0105)

    def test_missing_prices(self):
        model_info = ModelInfo(
            name="test-model",
            provider="test-provider",
            max_tokens=8192,
            context_window=200_000,
            supports_images=False,
            supports_computer_use=False,
            supports_prompt_cache=True,
            input_price=0,
            output_price=0
        )
        
        cost = calculate_api_cost(model_info, 1000, 500)
        self.assertEqual(cost, 0)

    def test_real_model_configuration(self):
        model_info = ModelInfo(
            name="claude-3.5-sonnet",
            provider="anthropic",
            max_tokens=8192,
            context_window=200_000,
            supports_images=True,
            supports_computer_use=True,
            supports_prompt_cache=True,
            input_price=3.0,
            output_price=15.0,
            cache_writes_price=3.75,
            cache_reads_price=0.3
        )
        
        cost = calculate_api_cost(model_info, 2000, 1000, 1500, 500)
        # Cache writes: (3.75 / 1_000_000) * 1500 = 0.005625
        # Cache reads: (0.3 / 1_000_000) * 500 = 0.00015
        # Input: (3.0 / 1_000_000) * 2000 = 0.006
        # Output: (15.0 / 1_000_000) * 1000 = 0.015
        # Total: 0.005625 + 0.00015 + 0.006 + 0.015 = 0.026775
        self.assertAlmostEqual(cost, 0.026775)

    def test_zero_token_counts(self):
        model_info = ModelInfo(
            name="test-model",
            provider="test-provider",
            max_tokens=8192,
            context_window=200_000,
            supports_images=False,
            supports_computer_use=False,
            supports_prompt_cache=True,
            input_price=3.0,
            output_price=15.0,
            cache_writes_price=3.75,
            cache_reads_price=0.3
        )
        
        cost = calculate_api_cost(model_info, 0, 0, 0, 0)
        self.assertEqual(cost, 0)

if __name__ == '__main__':
    unittest.main()
