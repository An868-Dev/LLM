import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from LLM.router import RouterAgent, RouterOutput
from LLM.clor import CHROAgent
from LLM.vector import VectorStore
from LLM.tools import HRTools  

logger = logging.getLogger(__name__)


@dataclass
class AgentState:
    query: str
    router_output: Optional[RouterOutput] = None
    rag_results: List[Dict] = field(default_factory=list)
    rag_context: str = ""
    tool_context: str = "" 
    final_response: str = ""
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return bool(self.final_response) and not self.error


class Supervisor:
    def __init__(self):
        logger.info("🚀 Initializing Supervisor...")
        self.router = RouterAgent()
        self.vector_store = VectorStore()
        self.chro_agent = CHROAgent()
        self._conversation_history: List[Dict] = []
        logger.info("✅ Supervisor ready")
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Tính độ tương đồng cơ bản giữa 2 câu (Jaccard Similarity) để xem có 'trùng ý' không."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0.0
        overlap = len(words1.intersection(words2)) / len(words1.union(words2))
        return overlap

    def _director_layer(self, state: AgentState) -> Optional[str]:
        history = self._conversation_history
        
        if state.router_output and getattr(state.router_output, 'sentiment', '') == 'confused':
            return "Người dùng đang có vẻ bối rối. Hãy giải thích các khái niệm HR một cách chậm rãi và rõ ràng hơn."

        user_msgs = [m['content'] for m in history if m['role'] == 'user']
        
        if len(user_msgs) >= 3:
            last_3 = user_msgs[-3:] 
            
            sim_1_2 = self._calculate_similarity(last_3[0], last_3[1])
            sim_2_3 = self._calculate_similarity(last_3[1], last_3[2])
            
            if sim_1_2 > 0.4 and sim_2_3 > 0.4: 
                return (
                    "CẢNH BÁO TỪ GIÁM SÁT: Người dùng đang lặp đi lặp lại cùng một ý hỏi 3 lần. "
                    "Hãy thẳng thắn nói với họ rằng 'Việc lặp lại câu hỏi như vậy cũng không giúp ích được gì cho tiến độ dự án', "
                    "sau đó yêu cầu họ đổi hướng suy nghĩ hoặc chủ động đề xuất giải pháp."
                )
        
        return None
    def run(self, query: str) -> AgentState:
        state = AgentState(query=query)
        logger.info(f"\n{'='*60}")
        logger.info(f"📩 New query: {query}")
        try:
            context_str = self._format_conversation_context()
            state.router_output = self.router.route(query, context_str)
            
            user_sentiment = getattr(state.router_output, 'sentiment', 'professional')
            logger.info(f"🔀 Intent: {state.router_output.intent} | Sentiment: {user_sentiment} | RAG: {state.router_output.requires_rag}")

            director_hint = self._director_layer(state)
            if director_hint:
                logger.info(f"Director triggered hint: {director_hint}")
            if "gucci" in query.lower():
                kpi_data = HRTools.get_kpi_metrics("gucci")
                state.tool_context = f"[Hệ thống nội bộ - KPI Gucci]: {kpi_data}\n"
            elif "bottega" in query.lower():
                kpi_data = HRTools.get_kpi_metrics("bottega_veneta")
                state.tool_context = f"[Hệ thống nội bộ - KPI Bottega Veneta]: {kpi_data}\n"

            if not state.router_output.is_off_topic and state.router_output.requires_rag:
                metadata_filter = None
                intent_to_category = {
                    "leadership_development": "leadership_development",
                    "mobility_planning": "mobility_planning",
                    "hr_policy": "hr_policy",
                    "competency_framework": "competency_framework",
                    "org_design": "org_design",
                }
                category = intent_to_category.get(state.router_output.intent)

                if category:
                    state.rag_results = self.vector_store.search(
                        query=query,
                        filter_metadata={"category": category}
                    )

                if not state.rag_results:
                    state.rag_results = self.vector_store.search(query=query)

                state.rag_context = self.vector_store.format_context(state.rag_results)
                logger.info(f"📚 RAG: {len(state.rag_results)} documents retrieved")
            else:
                state.rag_context = "" 
                logger.info("Bỏ qua RAG")
            combined_context = state.tool_context + state.rag_context
            state.final_response = self.chro_agent.respond(query=query,rag_context=combined_context,intent=state.router_output.intent,sentiment=user_sentiment,director_hint=director_hint)
            self._conversation_history.append({"role": "user", "content": query})
            self._conversation_history.append({
                "role": "assistant",
                "content": state.final_response,
                "intent": state.router_output.intent})
            if len(self._conversation_history) > 20:
                self._conversation_history = self._conversation_history[-20:]
        except Exception as e:
            logger.error(f"❌ Supervisor error: {e}", exc_info=True)
            state.error = str(e)
            state.final_response = (
                "Xin lỗi, có lỗi kỹ thuật xảy ra trong quá trình xử lý. "
                "Vui lòng thử lại sau giây lát.")
        return state
    def _format_conversation_context(self) -> str:
        if not self._conversation_history:
            return ""

        recent = self._conversation_history[-6:]  
        lines = []
        for msg in recent:
            role = "User" if msg["role"] == "user" else "CHRO"
            lines.append(f"{role}: {msg['content'][:100]}...")
        return "\n".join(lines)
    def reset_conversation(self):
        self._conversation_history = []
        self.chro_agent.reset_session()
        logger.info("Conversation reset")
    def get_system_status(self) -> Dict:
        db_stats = self.vector_store.get_stats()
        return {
            "status": "operational",
            "vector_db": db_stats,
            "conversation_turns": len(self._conversation_history) // 2,
        }