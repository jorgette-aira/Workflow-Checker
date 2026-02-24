from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase

def run_deepeval_accuracy(user_input, agent_output):
    """Uses LLM-based evaluation for higher accuracy checking."""
    # 1. Define the Metric
    metric = AnswerRelevancyMetric(threshold=0.7)
    
    # 2. Create a Test Case
    test_case = LLMTestCase(
        input=user_input,
        actual_output=agent_output
    )
    
    # 3. Measure
    metric.measure(test_case)
    score = metric.score * 100 # Convert 0.0-1.0 to percentage
    
    passed = metric.is_successful()
    status = "Passed" if passed else "Failed"
    
    return passed, f"    **DeepEval Score:** {score:.2f}% ({status})"
