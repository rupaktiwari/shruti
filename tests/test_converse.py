"""Manual checks against a running local API. Not part of the unit tests."""

import requests

API_URL = "http://127.0.0.1:8000/converse"

test_queries = [
    ("policy-thread", "What time is check-in, and is breakfast included with a deluxe room?"),
    ("jupiter-thread", "How many moons does Jupiter have?"),
    ("refund-thread", "I was charged twice and I want a refund."),
    (
        "book-thread",
        "Book a deluxe room for Sita Sharma, sita@example.com, check-in 2026-12-12, check-out 2026-12-15, 2 guests.",
    ),
]

for thread_id, question in test_queries:
    response = requests.post(API_URL, json={"transcript": question, "thread_id": thread_id}, timeout=120)
    print(f"Q: {question}")
    if response.status_code == 200:
        result = response.json()
        print(f"-> route: {result['route']}")
        print(f"-> answer: {result['answer']}")
    else:
        print(f"-> ERROR {response.status_code}: {response.text}")
    print()
