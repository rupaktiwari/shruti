from app.agents.graph import build_graph
from app.core.logging_config import get_logger
from app.services import memory_service
from app.services.llm_service import llm

logger = get_logger(__name__)


class OrchestratorService:
    def __init__(self):
        self.graph = build_graph()
        logger.info("Concierge graph compiled.")

    def respond(self, transcript: str, session_id: str, mode: str = "smart") -> dict:
        history = memory_service.get_history(session_id)

        if mode == "general":
            answer = llm.invoke(transcript).content
            route = "general"
        else:
            result = self.graph.invoke(
                {
                    "transcript": transcript,
                    "session_id": session_id,
                    "history": history,
                    "route": None,
                    "answer": None,
                }
            )
            answer = result["answer"]
            route = result["route"]

        memory_service.append_message(session_id, "user", transcript)
        memory_service.append_message(session_id, "assistant", answer, route=route)
        return {"answer": answer, "route": route}


orchestrator = OrchestratorService()
