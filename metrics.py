from deepeval.metrics import AnswerRelevancyMetric, GEval, HallucinationMetric
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

# FIX: Added 'context' to the arguments (making it 4 total)
def run_deepeval_metrics(workflow_data, agent_response, user_input, context):
    """
    Pure DeepEval implementation using GEval for Tone, 
    AnswerRelevancy for Accuracy, and Hallucination for Consistency.
    """
    
    # 1. Initialize Metrics
    relevancy_metric = AnswerRelevancyMetric(threshold=0.7)
    tone_metric = GEval(
        name="Tone",
        criteria="Professional and Helpful language.",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.7
    )
    hallucination_metric = HallucinationMetric(threshold=0.5)

    # 2. Create the Test Case
    test_case = LLMTestCase(
        input=user_input,
        actual_output=agent_response,
        context=context  # Now 'context' is correctly received from the arguments
    )
    
    # 3. Measure
    relevancy_metric.measure(test_case)
    tone_metric.measure(test_case)
    hallucination_metric.measure(test_case)
    
    rel_score = relevancy_metric.score * 100
    tone_score = tone_metric.score * 100
    hall_score = hallucination_metric.score * 100
    
    passed = (relevancy_metric.is_successful() and 
              tone_metric.is_successful() and 
              hallucination_metric.is_successful())
    
    details = (
        f"    **Accuracy:** {rel_score:.2f}% ({'Passed' if relevancy_metric.is_successful() else 'Failed'})\n"
        f"    **Tone:** {tone_score:.2f}% ({'Passed' if tone_metric.is_successful() else 'Failed'})\n"
        f"    **Factual Consistency:** {hall_score:.1f}% ({'Passed' if hallucination_metric.is_successful() else 'Failed'})\n"
        f"    **DeepEval Reason:** {hallucination_metric.reason}"
    )
    
    return passed, details

def run_all_metrics(workflow_data, agent_response, expected_qa):
    # We wrap expected_qa in a list because HallucinationMetric requires a list
    context_as_list = [expected_qa]
    
    # Passing 4 arguments: 1. workflow_data, 2. agent_response, 3. expected_qa, 4. context_as_list
    return run_deepeval_metrics(workflow_data, agent_response, expected_qa, context_as_list)
