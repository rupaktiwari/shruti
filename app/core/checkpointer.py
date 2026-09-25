   # app/core/checkpointer.py
from langgraph.checkpoint.sqlite import SqliteSaver
checkpointer = SqliteSaver.from_conn_string("shruti_conversations.db")