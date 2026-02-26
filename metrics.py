from deepeval.metrics import AnswerRelevancyMetric, GEval, HallucinationMetric
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

def check_workflow_structure(workflow_data):
    """Scans the JSON for AI Agent nodes, Model connections, and Orphan nodes."""
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
    has_agent = any(n.get("type") == "@n8n/n8n-nodes-langchain.agent" for n in nodes)
    has_model = "ai_languageModel" in str(connections)

    if not has_agent:
        return False, "**Structure Error**: No AI Agent node found."
    if not has_model:
        return False, "**Structure Error**: AI Agent has no Model connected."
    if orphans:
        orphan_list = ", ".join(orphans)
        return False, f"**Structure Error**: Orphan nodes detected: [{orphan_list}]."
    
    return True, "**Structure**: Correct (No orphans, Agent & Model active)."

# REMOVED: workflow_data from the arguments here to match the call below
def run_deepeval_metrics(agent_response, user_input, context):
    """Handles the heavy lifting of LLM evaluation."""
    relevancy_metric = AnswerRelevancyMetric(threshold=0.7)
    tone_metric = GEval(
        name="Tone",
        criteria="Professional and Helpful language.",
        evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT],
        threshold=0.7
    )
    hallucination_metric = HallucinationMetric(threshold=0.5)

    test_case = LLMTestCase(
        input=user_input,
        actual_output=agent_response,
        context=context
    )
    
    relevancy_metric.measure(test_case)
    tone_metric.measure(test_case)
    hallucination_metric.measure(test_case)
    
    passed = (relevancy_metric.is_successful() and 
              tone_metric.is_successful() and 
              hallucination_metric.is_successful())
    
    details = (
        f"    **Accuracy:** {relevancy_metric.score*100:.2f}% ({'Passed' if relevancy_metric.is_successful() else 'Failed'})\n"
        f"    **Tone:** {tone_metric.score*100:.2f}% ({'Passed' if tone_metric.is_successful() else 'Failed'})\n"
        f"    **Factual Consistency:** {hallucination_metric.score*100:.1f}% ({'Passed' if hallucination_metric.is_successful() else 'Failed'})\n"
        f"    **DeepEval Reason:** ```{hallucination_metric.reason}```"
    )
    
    return passed, details

def run_all_metrics(workflow_data, agent_response, expected_qa):
    # 1. Structural Check (Uses workflow_data)
    struct_passed, struct_msg = check_workflow_structure(workflow_data)
    if not struct_passed:
        return False, struct_msg

    # 2. DeepEval Metrics (No longer needs workflow_data)
    deepeval_passed, deepeval_details = run_deepeval_metrics(
        agent_response=agent_response,
        user_input="Verify workflow functionality",
        context=[expected_qa]
    )
    
    overall_passed = struct_passed and deepeval_passed
    full_report = f"{struct_msg}\n{deepeval_details}"
    
    return overall_passed, full_report
