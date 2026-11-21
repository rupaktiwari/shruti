from app.agents.graph import build_graph
from app.core.logging_config import get_logger
from app.services import memory_service

logger = get_logger(__name__)


class OrchestratorService:
    def __init__(self):
        self.graph = build_graph()
        logger.info("Shruti and Smriti graph compiled.")

    def respond(
        self,
        transcript: str,
        session_id: str,
        *,
        mode: str,
        notebook_id: int | None = None,
    ) -> dict:
        history = memory_service.get_history(session_id)
        result = self.graph.invoke(
            {
                "mode": mode,
                "transcript": transcript,
                "session_id": session_id,
                "notebook_id": notebook_id,
                "history": history,
                "route": None,
                "context": None,
                "citations": [],
                "answer": None,
            }
        )
        answer = result["answer"]
        citations = result.get("citations") or []
        memory_service.append_message(
            session_id,
            "user",
            transcript,
            mode=mode,
            notebook_id=notebook_id,
        )
        memory_service.append_message(
            session_id,
            "assistant",
            answer,
            mode=mode,
            notebook_id=notebook_id,
            citations=citations,
        )
        return {"answer": answer, "citations": citations, "mode": mode}


orchestrator = OrchestratorService()
