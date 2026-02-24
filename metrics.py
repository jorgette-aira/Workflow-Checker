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

    def run_all_metrics(workflow_data, agent_response, expected_qa):
    # Perform the checks
    struct_res = check_structure(workflow_data)
    acc_res = calculate_accuracy(agent_response, expected_qa)
    tone_passed, tone_msg = check_tone(agent_response) 
    
    overall_passed = struct_res["passed"] and acc_res["passed"] and tone_passed

    details = (
        f"{acc_res['message']}\n"
        f"{tone_msg}\n"
        f"{struct_res['message']}"
    )

    return overall_passed, details
    
    return passed, f"    **DeepEval Score:** {score:.2f}% ({'Passed' if passed else 'Failed'})"
