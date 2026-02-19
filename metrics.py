import re

def check_accuracy(agent_output, expected_answer):
    keywords = expected_answer.lower().split()
    matches = sum(1 for word in keywords if word in agent_output.lower())
    score = (matches / len(keywords)) * 100 if keywords else 0
    
    passed = score >= 90 # Matching your calculate_accuracy logic
    status = "Passed" if passed else "Failed"
    return passed, f"    **Accuracy Score:** {score:.2f}% ({status})"

def check_tone(agent_output):
    unprofessional_terms = ["whatever", "dunno", "stupid", "hey bro"]
    found_terms = [word for word in unprofessional_terms if word in agent_output.lower()]
    
    if not found_terms:
        return True, "    **Tone:** Professional and appropriate."
    return False, f"    **Tone:** Unprofessional language detected: {', '.join(found_terms)}"

def check_structure(workflow_data):
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
    
    # Building the bulleted list for structure issues
    if passed:
        message = "    **Structure:** Healthy"
    else:
        issue_list = []
        if not has_error_trigger: issue_list.append("Missing Error Trigger.")
        if orphans: issue_list.append(f"Orphan nodes: {', '.join(orphans)}.")
        if not has_model: issue_list.append("Agent has no Model connected.")
        
        # Format: Header followed by indented bullet points
        formatted_issues = "\n          - ".join(issue_list)
        message = f"    **Structure Issues:** \n          - {formatted_issues}"
    
    return {"passed": passed, "message": message}

def run_all_metrics(workflow_data, agent_response, expected_qa):
    struct_res = check_structure(workflow_data)
    # Using the versions that return clean strings for your desired layout
    acc_passed, acc_msg = check_accuracy(agent_response, expected_qa)
    tone_passed, tone_msg = check_tone(agent_response) 
    
    overall_passed = struct_res["passed"] and acc_passed and tone_passed
    
    # Constructing the final detail block
    details = (
        f"{acc_msg}\n"
        f"{tone_msg}\n"
        f"{struct_res['message']}"
    )
    
    return overall_passed, details
