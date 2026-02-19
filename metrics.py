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

def check_structure(workflow_json):
    """
    Validates that the builder followed the architectural standards.
    """
    nodes = workflow_json.get("nodes", [])
    # Check if they included an Error Trigger node for safety
    has_error_handler = any("errorTrigger" in n.get("type", "") for n in nodes)
    
    if has_error_handler:
        return True, "Structure: Error handling is present."
    return False, "Structure: Missing an Error Trigger node."

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
