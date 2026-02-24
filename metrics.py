from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase

def run_deepeval_check(user_input, agent_output, context):
    """Evaluates the agent using DeepEval's Relevancy metric."""
    metric = AnswerRelevancyMetric(threshold=0.7)
    
    # Ensure all arguments are separated by commas
    test_case = LLMTestCase(
        input=user_input,
        actual_output=agent_output,
        retrieval_context=context # 'context' must be a list of strings
    )
    
    metric.measure(test_case)
    
    passed = metric.is_successful()
    score = metric.score * 100
    
    return passed, f"    **DeepEval Score:** {score:.2f}% ({'Passed' if passed else 'Failed'})"
