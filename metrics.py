import re

def check_accuracy(agent_output, expected_answer):
    """
    Measures how closely the bot's answer matches the ground truth.
    For complex answers, we look for key technical terms.
    """
    # Simple keyword-based accuracy check
    keywords = expected_answer.lower().split()
    matches = sum(1 for word in keywords if word in agent_output.lower())
    score = (matches / len(keywords)) * 100 if keywords else 0
    
    if score >= 80:
        return True, f"Accuracy Score: {score:.2f}% (Passed)"
    return False, f"Accuracy Score: {score:.2f}% (Failed - expected more matching context)"

def check_tone(agent_output):
    """
    Checks if the bot maintains a professional and helpful tone.
    Flags aggressive or overly informal language.
    """
    unprofessional_terms = ["whatever", "dunno", "stupid", "hey bro"]
    found_terms = [word for word in unprofessional_terms if word in agent_output.lower()]
    
    if not found_terms:
        return True, "Tone: Professional and appropriate."
    return False, f"Tone: Unprofessional language detected: {', '.join(found_terms)}"

def check_structure(workflow_data):
    """Checks if the workflow has required nodes and if they are connected."""
    nodes = workflow_data.get("nodes", [])
    connections = workflow_data.get("connections", {})
    
    node_types = [node.get("type") for node in nodes]
    node_names = [node.get("name") for node in nodes]
    
    # 1. Production Requirement: Error Trigger
    has_error_trigger = "n8n-nodes-base.errorTrigger" in node_types
    
    # 2. Connection Check: Look for Orphan Nodes
    # We check if each node name appears at least once in the connections dictionary
    connected_nodes = set()
    for source_node, targets in connections.items():
        connected_nodes.add(source_node)
        for connection_type in targets.values():
            for connection_list in connection_type:
                for target in connection_list:
                    connected_nodes.add(target.get("node"))
    
    orphans = [name for name in node_names if name not in connected_nodes]
    
    # 3. Logic Check: Does the AI Agent have a Model?
    # Find the AI Agent node name first
    agent_node = next((n for n in nodes if n.get("type") == "@n8n/n8n-nodes-langchain.agent"), None)
    has_model = False
    if agent_node:
        agent_name = agent_node.get("name")
        # Check if any node is connected to the agent's 'ai_languageModel' input
        for source_node, targets in connections.items():
            for connection_type, connections_list in targets.items():
                for branch in connections_list:
                    for conn in branch:
                        if conn.get("node") == agent_name and conn.get("type") == "ai_languageModel":
                            has_model = True

    # Scoring Logic
    passed = has_error_trigger and len(orphans) == 0 and has_model
    
    messages = []
    if not has_error_trigger: messages.append("Missing Error Trigger.")
    if orphans: messages.append(f"Orphan nodes found: {', '.join(orphans)}.")
    if not has_model: messages.append("AI Agent has no Model connected.")
    
    return {
        "passed": passed,
        "message": "Structure: Healthy" if passed else f"Structure Issues: {' '.join(messages)}"
    }
def calculate_accuracy(agent_response, expected_qa):
    """Checks if the agent response contains the expected keywords."""
    # Split expected keywords (e.g., "assistant Batangas" -> ["assistant", "batangas"])
    required_keywords = expected_qa.lower().split()
    response_lower = agent_response.lower()
    
    found_words = [word for word in required_keywords if word in response_lower]
    score = (len(found_words) / len(required_keywords)) * 100
    
    passed = score >= 80 # Threshold: 80% accuracy to pass
    
    return {
        "passed": passed,
        "score": score,
        "message": f"Accuracy Score: {score:.2f}% ({'Passed' if passed else 'Failed'})"
    }

def run_all_metrics(workflow_data, agent_response, expected_qa):
    results = {
        "structure": check_structure(workflow_data),
        "accuracy": calculate_accuracy(agent_response, expected_qa),
        "tone": check_tone(agent_response)
    }
    
    # Final pass/fail is only true if ALL scores are above a threshold
    overall_passed = all(v['passed'] for v in results.values())
    
    return overall_passed, results
