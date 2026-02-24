from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase

def run_deepeval_check(user_input, agent_output, context):
    """Evaluates the agent using DeepEval's Relevancy metric."""
    metric = AnswerRelevancyMetric(threshold=0.7)
    
    test_case = LLMTestCase(
        input=user_input,
        actual_output=agent_output,
        retrieval_context=context 
    )
    
    metric.measure(test_case)
    
    passed = metric.is_successful()
    score = metric.score * 100
    
    return passed, f"    **DeepEval Score:** {score:.2f}% ({'Passed' if passed else 'Failed'})"

# --- CRITICAL: Move this to the LEFT MARGIN ---
def run_all_metrics(workflow_data, agent_response, expected_qa):
    # 1. Structural Check
    struct_res = check_structure(workflow_data)
    
    # 2. Tone Check
    tone_passed, tone_msg = check_tone(agent_response) 
    
    # 3. DeepEval Check (Using expected_qa as the 'context' for now)
    context = [expected_qa]
    acc_passed, acc_msg = run_deepeval_check(expected_qa, agent_response, context)
    
    # Calculate overall status
    overall_passed = struct_res["passed"] and tone_passed and acc_passed

    details = (
        f"{acc_msg}\n"
        f"{tone_msg}\n"
        f"{struct_res['message']}"
    )

    return overall_passed, details
