import os
from deepeval.metrics import AnswerRelevancyMetric, GEval, HallucinationMetric, FaithfulnessMetric
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")

def check_workflow_structure(workflow_data):
    nodes = workflow_data.get("nodes", [])
    connections = workflow_data.get("connections", {})
    
    all_node_names = {n.get("name") for n in nodes}
    connected_nodes = set()

    for source_node, targets in connections.items():
        connected_nodes.add(source_node)
        for connection_type in targets.values():
            for branch in connection_type:
                for connection in branch:
                    connected_nodes.add(connection.get("node"))

    orphans = all_node_names - connected_nodes

    has_agent = any("agent" in n.get("type", "").lower() for n in nodes)
    has_model = "ai_languageModel" in str(connections)

    if not has_agent:
        return False, "**Structure Error**: No AI Agent node found."
    if not has_model:
        return False, "**Structure Error**: AI Agent has no Model connected."
    if orphans:
        orphan_list = ", ".join(orphans)
    
    return True, "**Structure**: Correct (Agent & Model active)."

def run_deepeval_metrics(agent_response, user_input, context):

    if not os.environ.get("OPENAI_API_KEY"):
        return False, "❌ Error: OPENAI_API_KEY is missing from environment."
        
    relevancy_metric = AnswerRelevancyMetric(threshold=0.7)
    hallucination_metric = HallucinationMetric(threshold=0.5)

    tone_metric = GEval(
        name="Tone",
        criteria="Supportive, peer-like energy, and appropriate for a student collaborator.",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.7
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

def run_all_metrics(workflow_data, agent_response, expected_qa, user_input):
    struct_passed, struct_msg = check_workflow_structure(workflow_data)
    

    deepeval_passed, deepeval_details = run_deepeval_metrics(
        agent_response=agent_response,
        user_input=user_input, 
        context=[expected_qa]
    )
    
    overall_passed = struct_passed and deepeval_passed
    full_report = f"{struct_msg}\n{deepeval_details}"
    
    return overall_passed, full_report
