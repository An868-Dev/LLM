import json
import logging
from dataclasses import dataclass
from typing import Optional
import google.generativeai as genai
from LLM.settings import settings
from LLM.persona import ROUTER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

VALID_INTENTS = {
    "leadership_development",
    "talent_acquisition",
    "mobility_planning",
    "hr_policy",
    "competency_framework",
    "org_design",
    "general_chro",
    "off_topic",
}


@dataclass
class RouterOutput:
    intent: str
    confidence: float
    reasoning: str
    requires_rag: bool
    sentiment: str  
    
    @property
    def is_valid(self) -> bool:
        return self.intent in VALID_INTENTS and self.confidence > 0.3

    @property
    def is_off_topic(self) -> bool:
        return self.intent == "off_topic"


class RouterAgent:
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            system_instruction=ROUTER_SYSTEM_PROMPT,
            generation_config=genai.GenerationConfig(
                temperature=0.1, 
                max_output_tokens=256,
                response_mime_type="application/json"
            )
        )

    def route(self, query: str, conversation_context: Optional[str] = None) -> RouterOutput:
        prompt = f"Câu hỏi: {query}"
        if conversation_context:
            prompt = f"Bối cảnh hội thoại:\n{conversation_context}\n\n{prompt}"

        try:
            response = self.model.generate_content(prompt)
            raw = response.text.strip()

            # Parse JSON response
            data = json.loads(raw)
            output = RouterOutput(
                intent=data.get("intent", "general_chro"),
                confidence=float(data.get("confidence", 0.7)),
                reasoning=data.get("reasoning", ""),
                requires_rag=bool(data.get("requires_rag", True)),
                sentiment=data.get("sentiment", "professional") 
            )

            # Validate intent
            if output.intent not in VALID_INTENTS:
                output.intent = "general_chro"

            logger.info(f"🔀 Router: '{query[:40]}' → {output.intent} (conf: {output.confidence:.2f}) | sentiment: {output.sentiment}")
            return output

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"⚠️ Router parsing error: {e}, defaulting to general_chro & professional")

            return RouterOutput(
                intent="general_chro",
                confidence=0.5,
                reasoning="Parsing failed, using default",
                requires_rag=True,
                sentiment="professional" 
            )