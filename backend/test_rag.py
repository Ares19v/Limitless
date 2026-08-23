import asyncio
import json
import httpx
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1"

TEST_DATA = [
    {
        "file": "../demo_docs/bitcoin_whitepaper.pdf",
        "questions": [
            "What is the main problem this paper tries to solve?",
            "How does the system prevent double-spending?",
            "What cryptographic hash function is used?",
            "What happens when two competing blocks are found?",
            "How are new coins created?",
            "What is a Merkle Tree used for in this system?",
            "Does the system rely on identities?",
            "What happens if a greedy attacker has more CPU power than honest nodes?",
            "How is privacy maintained?",
            "What is the role of an honest node?"
        ]
    },
    {
        "file": "../demo_docs/attention_is_all_you_need.pdf",
        "questions": [
            "What does the Transformer architecture replace?",
            "What are the two main components of the Transformer?",
            "How is positional information injected?",
            "What is the equation for Scaled Dot-Product Attention?",
            "Why scale the dot-product attention?",
            "How many attention heads are used in the base model?",
            "What is the dimensionality of the model (d_model)?",
            "What optimizer is used for training?",
            "How is regularization applied?",
            "On which translation task did it set a new state-of-the-art?"
        ]
    },
    {
        "file": "../demo_docs/gpt3_language_models.pdf",
        "questions": [
            "How many parameters does the largest GPT-3 model have?",
            "What are the three settings evaluated for in-context learning?",
            "Does GPT-3 use gradient updates during few-shot learning?",
            "What architecture is GPT-3 based on?",
            "What is the context window size of GPT-3?",
            "How does GPT-3 perform on the LAMBADA dataset?",
            "What is a known limitation of GPT-3 regarding bidirectionality?",
            "Does GPT-3 struggle with any specific types of tasks?",
            "What potential societal impacts of GPT-3 are discussed?",
            "How was the training data filtered?"
        ]
    }
]

async def process_stream(response):
    full_text = ""
    async for line in response.aiter_lines():
        if line.startswith("data: "):
            content = line[6:]
            if content == "[DONE]":
                break
            if content.startswith("[") or content.startswith("{"):
                continue
            full_text += content
    return full_text

async def run_tests():
    with open("test_results.txt", "w", encoding="utf-8") as out_f:
        def log(msg):
            print(msg)
            out_f.write(msg + "\n")
            out_f.flush()

        async with httpx.AsyncClient(timeout=120.0) as client:
            for doc in TEST_DATA:
                file_path = Path(doc["file"])
                log(f"\n{'='*60}\nTesting document: {file_path.name}\n{'='*60}")
                
                # 1. Upload
                with open(file_path, "rb") as f:
                    res = await client.post(f"{BASE_URL}/upload", files={"file": (file_path.name, f, "application/pdf")})
                
                if res.status_code != 202:
                    log(f"Failed to upload {file_path.name}: {res.text}")
                    continue
                
                doc_id = res.json()["document_id"]
                log(f"Uploaded! Document ID: {doc_id}")
                
                # 2. Poll status
                log("Waiting for PDF to be processed, chunked, and embedded (this takes 10-30s)...")
                while True:
                    res = await client.get(f"{BASE_URL}/documents/{doc_id}")
                    status = res.json()["status"]
                    if status == "ready":
                        break
                    elif status == "error":
                        log(f"Error processing document: {res.json().get('error_message')}")
                        break
                    await asyncio.sleep(2)
                
                if status != "ready":
                    continue
                
                log(f"Document ready! Running {len(doc['questions'])} questions...\n")
                
                # 3. Ask questions
                for i, q in enumerate(doc["questions"], 1):
                    log(f"Q{i}: {q}")
                    req = {
                        "document_id": doc_id,
                        "message": q
                    }
                    try:
                        async with client.stream("POST", f"{BASE_URL}/chat/{doc_id}", json=req) as response:
                            answer = await process_stream(response)
                        log(f"A{i}: {answer.strip()}\n")
                    except Exception as e:
                        log(f"A{i}: Error: {e}\n")

if __name__ == "__main__":
    asyncio.run(run_tests())
