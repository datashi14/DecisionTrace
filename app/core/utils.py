import json
import re
from typing import Any, Dict, Optional

def extract_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Extracts JSON from a string, handling potential LLM markdown artifacts.
    """
    try:
        # Try direct parse
        return json.loads(text)
    except json.JSONDecodeError:
        # Try finding JSON block
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                return None
    return None
