from deepeval.metrics import AnswerRelevancyMetric, StyleMetric
from deepeval.test_case import LLMTestCase

def run_deepeval_metrics(workflow_data, agent_response, user_input):
    """
    Pure DeepEval implementation for Workflow-Checker.
    Uses LLM-based evaluation for all metrics.
    """
    
    # 1. Answer Relevancy Metric
    # Replaces your old keyword-matching accuracy check.
    relevancy_metric = AnswerRelevancyMetric(threshold=0.8)
    
    # 2. Tone/Style Metric
    # Replaces the unprofessional_terms list check.
    tone_metric = StyleMetric(
        evaluation_params=["professional", "helpful", "concise"],
        threshold=0.7
    )
    
    # 3. Create the Test Case
    test_case = LLMTestCase(
        input=user_input,
        actual_output=agent_response,
        retrieval_context=[str(workflow_data)] # Passing structure as context for analysis
    )
    
    # 4. Measure
    relevancy_metric.measure(test_case)
    tone_metric.measure(test_case)
    
    # Calculate scores
    rel_score = relevancy_metric.score * 100
    tone_score = tone_metric.score * 100
    
    # Logic for overall pass (DeepEval logic)
    passed = relevancy_metric.is_successful() and tone_metric.is_successful()
    
    # Formatting for Discord
    details = (
        f"    **Accuracy (Relevancy):** {rel_score:.2f}% ({'Passed' if relevancy_metric.is_successful() else 'Failed'})\n"
        f"    **Tone (Professionalism):** {tone_score:.2f}% ({'Passed' if tone_metric.is_successful() else 'Failed'})\n"
        f"    **DeepEval Reason:** {relevancy_metric.reason}"
    )
    
    return passed, details

# Standard orchestrator name for your main.py import
def run_all_metrics(workflow_data, agent_response, expected_qa):
    return run_deepeval_metrics(workflow_data, agent_response, expected_qa)
