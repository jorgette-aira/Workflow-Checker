import re

def check_accuracy(agent_output, expected_answer):
    """Measures how closely the bot's answer matches the ground truth."""
    required_keywords = expected_answer.lower().split()
    response_lower = agent_output.lower()
    
    found_words = [word for word in required_keywords if word in response_lower]
    score = (len(found_words) / len(required_keywords)) * 100 if required_keywords else 0
    
    passed = score >= 90 # Threshold: 90% accuracy to pass
    status = "Passed" if passed else "Failed"
    
    return passed, f"    **Accuracy Score:** {score:.2f}% ({status})"

def check_tone(agent_output):
    """Checks for professional and helpful tone."""
    unprofessional_terms = ["whatever", "dunno", "stupid", "hey bro"]
    found_terms = [word for word in unprofessional_terms if word in agent_output.lower()]
    
    if not found_terms:
        return True, "    **Tone:** Professional and appropriate."
    return False, f"    **Tone:** Unprofessional language detected: {', '.join(found_terms)}"

def check_structure(workflow_data):
    """Checks if the workflow has required nodes and if they are connected."""
    nodes = workflow_data.get("nodes", [])
    connections = workflow_data.get("connections", {})
    
    node_types = [node.get("type") for node in nodes]
    node_names = [node.get("name") for node in nodes]
    
    has_error_trigger = "n8n-nodes-base.errorTrigger" in node_types
    
    connected_nodes = set()
    for source_node, connection_types in connections.items():
        connected_nodes.add(source_node)
        for connection_branches in connection_types.values():
            for branch in connection_branches:
                for target in branch:
                    connected_nodes.add(target.get("node"))
    
    orphans = [name for name in node_names if name not in connected_nodes]

    agent_node = next((n for n in nodes if n.get("type") == "@n8n/n8n-nodes-langchain.agent"), None)
    has_model = False
    if agent_node:
        agent_name = agent_node.get("name")
        for source_node, connection_types in connections.items():
            if "ai_languageModel" in connection_types:
                for branch in connection_types["ai_languageModel"]:
                    for target in branch:
                        if target.get("node") == agent_name:
                            has_model = True

    passed = has_error_trigger and len(orphans) == 0 and has_model
    
    if passed:
        message = "    **Structure:** Healthy"
    else:
        issue_list = []
        if not has_error_trigger: issue_list.append("Missing Error Trigger.")
        if orphans: issue_list.append(f"Orphan nodes: {', '.join(orphans)}.")
        if not has_model: issue_list.append("Agent has no Model connected.")
        
        # Format the list with exact indentation for Discord
        formatted_issues = "\n          - ".join(issue_list)
        message = f"    **Structure Issues:** \n          - {formatted_issues}"
    
    return {"passed": passed, "message": message}

def run_all_metrics(workflow_data, agent_response, expected_qa):
    """Orchestrates checks and builds the final multi-line string."""
    struct_res = check_structure(workflow_data)
    acc_passed, acc_msg = check_accuracy(agent_response, expected_qa)
    tone_passed, tone_msg = check_tone(agent_response) 
    
    overall_passed = struct_res["passed"] and acc_passed and tone_passed
    
    # Combined string construction
    details = (
        f"{acc_msg}\n"
        f"{tone_msg}\n"
        f"{struct_res['message']}"
    )
    
    return overall_passed, details
