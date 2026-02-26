from deepeval.metrics import AnswerRelevancyMetric, GEval, HallucinationMetric
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

def check_workflow_structure(workflow_data):
    """
    Scans the JSON for AI Agent nodes, Model connections, and Orphan nodes.
    """
    nodes = workflow_data.get("nodes", [])
    connections = workflow_data.get("connections", {})
    
   # 1. Identity all nodes by their names
    all_node_names = {n.get("name") for n in nodes}
    
    # 2. Map all nodes that are part of a connection
    connected_nodes = set()
    for source_node, targets in connections.items():
        connected_nodes.add(source_node) # Node sending data
        for connection_type in targets.values():
            for branch in connection_type:
                for connection in branch:
                    connected_nodes.add(connection.get("node"))

    # 3. Identify Orphans
    orphans = all_node_names - connected_nodes
    
    # 4. Check for AI Essentials
    has_agent = any(n.get("type") == "@n8n/n8n-nodes-langchain.agent" for n in nodes)
    has_model = "ai_languageModel" in str(connections)

    if not has_agent:
        return False, "**Structure Error**: No AI Agent node found."
    if not has_model:
        return False, "**Structure Error**: AI Agent has no Model connected."
    if orphans:
        # We list the specific orphans to help you find them in n8n
        orphan_list = ", ".join(orphans)
        return False, f"**Structure Error**: Orphan nodes detected: [{orphan_list}]. Please connect or delete them."
    
    return True, "**Structure**: Correct (No orphans, Agent & Model active)."
    
def run_deepeval_metrics(workflow_data, agent_response, user_input, context):
    """
    DeepEval implementation using GEval for Tone, 
    AnswerRelevancy for Accuracy, and 
    Hallucination for Consistency.
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
        context=context
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
    # Layer 1: Check the actual JSON code
    struct_passed, struct_msg = check_workflow_structure(workflow_data)
    
    if not struct_passed:
        return False, struct_msg

    # Layer 2: Run DeepEval on the Output
    deepeval_passed, deepeval_details = run_deepeval_metrics(
        agent_response=agent_response,
        user_input="Verify workflow functionality",
        context=[expected_qa]
    )
    
    overall_passed = struct_passed and deepeval_passed
    full_report = f"{struct_msg}\n{deepeval_details}"
    
    return overall_passed, full_report
