import os
import re
import json
import datetime
from langchain_groq import ChatGroq

class MockResponse:
    def __init__(self, content):
        self.content = content

class MockLLM:
    def __init__(self, model_name):
        self.model_name = model_name

    def invoke(self, messages, **kwargs):
        # Find user message content and system message
        user_msg = ""
        system_msg = ""
        
        if isinstance(messages, str):
            system_msg = messages
        else:
            # messages can be a list of dicts or standard langchain Message objects
            for m in messages:
                if isinstance(m, dict):
                    role = m.get("role")
                    content = m.get("content", "")
                else:
                    role = getattr(m, "type", "user")
                    content = getattr(m, "content", "")
                
                if role == "user":
                    user_msg = content
                elif role == "system":
                    system_msg = content

        user_lower = user_msg.lower()
        system_lower = system_msg.lower()

        # 1. Intent routing
        if "classify the intent" in system_lower:
            if any(x in user_lower for x in ["change", "update", "edit", "modify"]):
                return MockResponse("edit_interaction")
            elif any(x in user_lower for x in ["search", "find", "lookup"]):
                return MockResponse("lookup_hcp")
            elif any(x in user_lower for x in ["schedule", "followup", "follow-up"]):
                return MockResponse("schedule_followup")
            elif any(x in user_lower for x in ["history", "summary", "summarize"]):
                return MockResponse("summarize_history")
            elif any(x in user_lower for x in ["met", "visit", "email", "call", "log", "talked"]):
                return MockResponse("log_interaction")
            else:
                return MockResponse("general_query")

        # 2. Entity extraction
        elif "extract structured information" in system_lower:
            hcp_name = "Dr. Anil Sharma"
            if "mehta" in user_lower:
                hcp_name = "Dr. Sunita Mehta"
            elif "patel" in user_lower:
                hcp_name = "Dr. Rajesh Patel"
            elif "nair" in user_lower:
                hcp_name = "Dr. Priya Nair"
            elif "gupta" in user_lower:
                hcp_name = "Dr. Sanjay Gupta"
            
            inter_type = "visit"
            if "call" in user_lower or "phoned" in user_lower or "phone" in user_lower:
                inter_type = "call"
            elif "email" in user_lower or "emailed" in user_lower:
                inter_type = "email"
            elif "conference" in user_lower or "meeting" in user_lower:
                inter_type = "conference"
                
            sentiment = "neutral"
            if any(x in user_lower for x in ["positive", "happy", "enthusiastic", "great", "good"]):
                sentiment = "positive"
            elif any(x in user_lower for x in ["negative", "uninterested", "bad", "angry"]):
                sentiment = "negative"
                
            topics = ["Product efficacy"]
            if "cardioshield" in user_lower:
                topics = ["CardioShield launch & efficacy"]
            elif "glynase" in user_lower:
                topics = ["Glynase update & samples"]
                
            products = []
            if "cardioshield" in user_lower:
                products = ["CardioShield"]
            elif "glynase" in user_lower:
                products = ["Glynase"]
                
            follow_up = False
            follow_up_date = None
            if any(x in user_lower for x in ["followup", "follow-up", "next week", "tomorrow", "remind"]):
                follow_up = True
                follow_up_date = (datetime.date.today() + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
                
            samples = None
            # Find numbers for samples
            qty_match = re.search(r'(\d+)\s*samples?', user_lower)
            if qty_match:
                qty = int(qty_match.group(1))
                prod_name = products[0] if products else "CardioShield"
                samples = {prod_name: qty}
            elif "sample" in user_lower:
                samples = {"CardioShield": 10}

            extracted = {
                "hcp_name": hcp_name,
                "interaction_type": inter_type,
                "topics_discussed": topics,
                "products_discussed": products,
                "sentiment": sentiment,
                "follow_up_required": follow_up,
                "follow_up_date": follow_up_date,
                "samples_distributed": samples
            }
            return MockResponse(json.dumps(extracted))

        # 3. Response formatting
        elif "executed a database tool" in system_lower:
            # Generate friendly confirmation based on tool name
            if "log_interaction" in system_lower:
                return MockResponse("Logged! Interaction successfully recorded in the CRM database.")
            elif "edit_interaction" in system_lower:
                return MockResponse("Updated! The interaction log details have been updated successfully.")
            elif "schedule_followup" in system_lower:
                return MockResponse("Follow-up scheduled! Reminders set in the CRM.")
            else:
                return MockResponse("Action completed successfully. CRM database updated.")

        # 4. History summaries or general conversational queries
        else:
            if "relationship summary" in system_lower:
                return MockResponse("""Here is the relationship summary:
• **Key Talking Points**: Discussed product updates, trial results, and efficacy profiles.
• **Sentiment Trend**: Receptive and positive.
• **Outstanding Actions**: Follow-up pending for next visit.
• **Recent Samples**: Distributed CardioShield packs.""")
            
            return MockResponse("Hello! I am your AI CRM Assistant. How can I help you log or manage your HCP interactions today?")

def get_llm(context_model=False):
    """
    Returns an instance of the Groq LLM client.
    If GROQ_API_KEY is not configured or set to placeholder, falls back to a MockLLM
    so that the application works seamlessly for demos and offline testing.
    """
    api_key = os.getenv("GROQ_API_KEY", "")
    
    # Check if key is empty or placeholder
    if not api_key or api_key in ["dummy_key", "your_groq_api_key_here", "gsk_your_actual_key_here"]:
        model_name = "mock-model"
        return MockLLM(model_name)
        
    model_name = os.getenv(
        "GROQ_CONTEXT_MODEL" if context_model else "GROQ_PRIMARY_MODEL",
        "llama-3.3-70b-versatile" if context_model else "llama-3.1-8b-instant"
    )
    
    return ChatGroq(
        groq_api_key=api_key,
        model_name=model_name,
        temperature=0.0
    )
