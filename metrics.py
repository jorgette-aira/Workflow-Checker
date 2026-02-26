from deepeval.metrics import AnswerRelevancyMetric, GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval.models.gpt_model import GPTModel

# Initialize a cheaper model (gpt-4o-mini)
cheap_model = GPTModel(model="gpt-4o-mini")
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
        criteria="Determine if the response is professional, helpful, and avoids informal slang.",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.7,
        model=cheap_model
    )
    
    # 3. Create the Test Case
    test_case = LLMTestCase(
        input=user_input,
        actual_output=agent_response,
        # We pass the workflow structure as context so the LLM can see the nodes
        retrieval_context=[str(workflow_data)] 
    )
    
    # 4. Measure
    relevancy_metric.measure(test_case)
    tone_metric.measure(test_case)
    
    # Calculate scores
    rel_score = relevancy_metric.score * 100
    tone_score = tone_metric.score * 100
    
    # Overall Pass/Fail logic
    passed = relevancy_metric.is_successful() and tone_metric.is_successful()
    
    # Formatting for your Discord Notification
    details = (
        f"    **Accuracy (Relevancy):** {rel_score:.2f}% ({'Passed' if relevancy_metric.is_successful() else 'Failed'})\n"
        f"    **Tone (Professionalism):** {tone_score:.2f}% ({'Passed' if tone_metric.is_successful() else 'Failed'})\n"
        f"    **DeepEval Reason:** {relevancy_metric.reason}"
    )
    
    return passed, details

def run_all_metrics(workflow_data, agent_response, expected_qa):
    # Map the expected_qa to user_input for the DeepEval check
    return run_deepeval_metrics(workflow_data, agent_response, expected_qa)
