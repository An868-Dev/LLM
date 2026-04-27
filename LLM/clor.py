import logging
from typing import List, Dict, Optional
import google.generativeai as genai
from LLM.settings import settings
from LLM.persona import CHRO_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class CHROAgent:

    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            system_instruction=CHRO_SYSTEM_PROMPT,
            generation_config=genai.GenerationConfig(
                temperature=settings.temperature,
                max_output_tokens=settings.max_output_tokens,
            )
        )
        self._chat_session = None

    def reset_session(self):
        self._chat_session = self.model.start_chat(history=[])
        logger.info("💬 CHRO chat session reset")

    def _get_or_create_session(self):
        if self._chat_session is None:
            self.reset_session()
        return self._chat_session

    def respond(
        self,
        query: str,
        rag_context: str = "",
        intent: str = "general_chro",
        sentiment: str = "professional",
        director_hint: Optional[str] = None,  
        metadata: Optional[Dict] = None
    ) -> str:
        chat = self._get_or_create_session()

        prompt_parts = []

        if rag_context:
            prompt_parts.append(rag_context)
            prompt_parts.append("")

        prompt_parts.append(f"[TRẠNG THÁI NGƯỜI DÙNG: {sentiment.upper()}]")
        
        if director_hint:
            prompt_parts.append(f"[CHỈ DẪN GIÁM SÁT: {director_hint}]")

        if intent != "general_chro":
            prompt_parts.append(f"[Phạm vi chuyên môn: {intent.replace('_', ' ').title()}]")

        prompt_parts.append(f"Câu hỏi: {query}")

        full_prompt = "\n".join(prompt_parts)

        try:
            response = chat.send_message(full_prompt)
            answer = response.text
            logger.info(f"CHRO responded (Sentiment: {sentiment})")
            return answer

        except Exception as e:
            logger.error(f"CHRO Agent error: {e}")
            return "Đang gặp sự cố kỹ thuật"

    def get_history(self) -> List[Dict]:
        if not self._chat_session:
            return []

        history = []
        for msg in self._chat_session.history:
            history.append({
                "role": msg.role,
                "content": msg.parts[0].text if msg.parts else ""
            })
        return history