# tests/test_converse.py
import requests

API_URL = "http://127.0.0.1:8000/converse"

test_queries = [
    ("kyc-thread", "Why is my KYC not verified yet?"),
    ("jupiter-thread", "How many moons does Jupiter have?"),
    ("weird-thread", "My cousin's payment went to the wrong account somehow, what do I do?"),
]

for thread_id, question in test_queries:
    response = requests.post(API_URL, json={"transcript": question, "thread_id": thread_id})

    print(f"Q: {question}")
    if response.status_code == 200:
        result = response.json()
        print(f"-> route: {result['route']}")
        print(f"-> answer: {result['answer']}")
    else:
        print(f"-> ERROR {response.status_code}: {response.text}")
    print()