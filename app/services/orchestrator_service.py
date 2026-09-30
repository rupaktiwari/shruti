from app.agents.graph import build_graph
from app.services.llm_service import llm
from app.core.logging_config import get_logger

logger = get_logger(__name__)

class OrchestratorService:
    def __init__(self):
        self.graph = build_graph()
        logger.info("Orchestrator graph compiled and ready.")

    def respond(self, transcript: str, thread_id: str, mode: str = "smart") -> dict:
        if mode == "general":
            # Bypass routing/RAG/escalation entirely — plain LLM only
            answer = llm.invoke(transcript).content
            return {"answer": answer, "route": "general"}

        config = {"configurable": {"thread_id": thread_id}}
        result = self.graph.invoke(
            {"transcript": transcript, "thread_id": thread_id, "route": None, "confidence": None, "answer": None},
            config=config,
        )
        return {"answer": result["answer"], "route": result["route"]}

orchestrator = OrchestratorService()