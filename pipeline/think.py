import anthropic
from config import ANTHROPIC_API_KEY
from characters.robomaz import get_system_prompt

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def get_response(user_message: str) -> str:
    """Send customer message to Claude, get Robomaz's response."""
    print("[think] Thinking...")
    
    message = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=120,        # keeps responses short and snappy
        system=get_system_prompt(),
        messages=[
            {"role": "user", "content": user_message}
        ]
    )
    
    response = message.content[0].text
    print(f"[think] Response: '{response}'")
    return response