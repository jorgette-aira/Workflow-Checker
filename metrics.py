import os
from deepeval.metrics import AnswerRelevancyMetric, GEval, HallucinationMetric
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval.models import GPTModel 

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")

def run_deepeval_metrics(agent_response, user_input, context):
    if not os.environ.get("OPENAI_API_KEY"):
        return False, "❌ Error: OPENAI_API_KEY is missing from environment."

    relevancy_metric = AnswerRelevancyMetric(threshold=0.7, model="gpt-4o-mini")
    hallucination_metric = HallucinationMetric(threshold=0.5, model="gpt-4o-mini")

    tone_metric = GEval(
        name="Tone",
        criteria="anyreadble test tone",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.5,
        model="gpt-4o-mini"
    )

    test_case = LLMTestCase(
        input=user_input,
        actual_output=agent_response,
        context=context if isinstance(context, list) else [context]
    )

    relevancy_metric.measure(test_case)
    tone_metric.measure(test_case)
    hallucination_metric.measure(test_case)
    
    hallucination_score = hallucination_metric.score
    passed = (relevancy_metric.is_successful() and 
              tone_metric.is_successful() and 
              hallucination_score <= 0.5) 

    details = (
        f"    **Accuracy:** {relevancy_metric.score*100:.2f}% ({'Pass' if relevancy_metric.is_successful() else 'Fail'})\n"
        f"    **Tone:** {tone_metric.score*100:.2f}% ({'Pass' if tone_metric.is_successful() else 'Fail'})\n"
        f"    **Hallucination Risk:** {hallucination_score*100:.1f}% ({'Pass' if hallucination_score <= 0.5 else 'Fail'})\n"
        f"    **DeepEval Reason:** ```{hallucination_metric.reason}```"
    )
    
    return passed, details

def run_all_metrics(agent_response, expected_qa, user_input):

    deepeval_passed, deepeval_details = run_deepeval_metrics(
        agent_response=agent_response,
        user_input=user_input, 
        context=[expected_qa]
    )
    
    overall_passed = deepeval_passed
    full_report = f"{struct_msg}\n{deepeval_details}"
    
    return overall_passed, full_report
