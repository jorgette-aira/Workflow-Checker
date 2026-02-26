from deepeval.metrics import AnswerRelevancyMetric, GEval, HallucinationMetric
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval.models import GPTModel

def run_deepeval_metrics(workflow_data, agent_response, user_input):
    """
    Pure DeepEval implementation using GEval for Tone and 
    AnswerRelevancy for Accuracy.
    """
    
    # 1. Answer Relevancy Metric (Semantic Accuracy)
    relevancy_metric = AnswerRelevancyMetric(threshold=0.7)
    
    # 2. Tone Metric (using G-Eval to judge Professionalism)
    # This replaces StyleMetric to avoid the ImportError.
    tone_metric = GEval(
        name="Tone",
        criteria="Professional and Helpful language.",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.7
    )

    hallucination_metric = HallucinationMetric(threshold=0.5)
    # 3. Create the Test Case
    test_case = LLMTestCase(
        input=user_input,
        actual_output=agent_response,
        context=context_list
    )
    
    # 4. Measure
    relevancy_metric.measure(test_case)
    tone_metric.measure(test_case)
    hallucination_metric.measure(test_case)
    
    # Calculate scores
    rel_score = relevancy_metric.score * 100
    tone_score = tone_metric.score * 100
    
    # Overall Pass/Fail logic
    passed = relevancy_metric.is_successful() and tone_metric.is_successful() and hallucination_metric.is_successful())
    
    # Formatting for your Discord Notification
    details = (
        f"    **Accuracy :** {rel_score:.2f}% ({'Passed' if relevancy_metric.is_successful() else 'Failed'})\n"
        f"    **Tone :** {tone_score:.2f}% ({'Passed' if tone_metric.is_successful() else 'Failed'})\n"
        f"    **Factual Consistency:** {hallucination_metric.score * 100:.1f}%\n"
        f"    **DeepEval Reason:** {hallucination_metric.reason}"
    )
    
    return passed, details

def run_all_metrics(workflow_data, agent_response, expected_qa):
    # Map the expected_qa to user_input for the DeepEval check
    return run_deepeval_metrics(workflow_data, agent_response, expected_qa)
