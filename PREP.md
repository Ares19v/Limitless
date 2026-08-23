# PREP — Limitless (From-Scratch Study Guide)

Welcome to the beginner-friendly developer study guide for **Limitless**! In this guide, you will learn the algorithms, design patterns, and mathematical frameworks behind state-of-the-art Hybrid RAG (Retrieval-Augmented Generation) pipelines and AI Agents.

---

## 1. Hybrid Search & Reciprocal Rank Fusion (RRF)

Standard vector search (dense embeddings) is fantastic for finding semantic meaning, but it struggles with specific keywords, product codes, or exact match strings. Limitless solves this by combining two search styles:

### 1. Sparse Search (BM25)
* **What it is**: An advanced version of TF-IDF (Term Frequency-Inverse Document Frequency) that ranks documents based on the exact appearance of query words, adjusted for document length.
* **Best at**: Finding exact matches, names, and precise technical codes (e.g. "Satoshi Nakamoto", "v2.1").

### 2. Dense Search (Vector Embeddings)
* **What it is**: Converts text passages into coordinates in high-dimensional space (e.g. 384 dimensions) using a local neural model (`all-MiniLM-L6-v2`). Cosine similarity calculates how close the query is to a passage.
* **Best at**: Finding synonyms and conceptual answers (e.g. "How does the system handle consensus?" -> finds paragraphs on proof-of-work even if the word "consensus" isn't explicitly used).

### 3. Fusing the Results: Reciprocal Rank Fusion (RRF)
To merge these two distinct rankings into a single optimal list, we use **RRF**.
RRF scores each document based on its rank in both sparse and dense outputs, penalizing lower ranks:

$$RRF\_Score(d) = \sum_{m \in M} \frac{1}{k + r_m(d)}$$

Where:
* $M$ represents the search engines (Sparse & Dense).
* $r_m(d)$ is the rank of document $d$ in search engine $m$ (1-indexed).
* $k$ is a constant smoothing factor (standard value: $60$).

*Why this works*: If a document is ranked 1st in dense search and 2nd in sparse search, it receives a very high combined score. If it's ranked 100th in both, its score drops drastically.

---

## 2. Bi-Encoders vs. Cross-Encoders (Re-ranking)

Converting all documents into vectors to search them is called **Bi-Encoding**. It is fast and scalable, but has limited accuracy because the query and document are represented separately.

### What is a Cross-Encoder?
A **Cross-Encoder** feeds the query and a retrieved passage **simultaneously** into a transformer model, allowing self-attention layers to calculate the exact word-to-word relationships between the query and the text.

```
Bi-Encoder (Fast, Less Accurate):
Query ──► [Encoder] ──► Vector ──┐
                                 ├─► Cosine Similarity
Passage ─► [Encoder] ──► Vector ─┘

Cross-Encoder (Slow, Highly Accurate):
[ Query ] + [ Passage ] ──► [ Cross-Encoder Transformer ] ──► Similarity Score (0 to 1)
```

### The Re-ranking Workflow:
1. Fetch the top 15 candidate passages using **Hybrid Search** (Fast).
2. Pass all 15 passages through the local `ms-marco-MiniLM-L-6-v2` **Cross-Encoder** against the exact query (Accurate).
3. Filter down to the absolute top 5 highest-scoring passages to feed to the LLM.

---

## 3. The ReAct Agent Framework

In **Agent Mode**, Limitless shifts from basic search to an autonomous solver using the **ReAct** (Reasoning and Acting) paradigm.

### How ReAct Works:
Instead of directly generating an answer, the model goes through a loop of:
1. **Thought**: The model reasons about the current situation.
2. **Action**: The model chooses a tool (Document Search, Google Web Search, Math Calculator) and writes input parameters.
3. **Observation**: The system executes the tool and feeds the raw results back to the model.
4. **Repeat / Final Answer**: The loop continues until the model determines it has sufficient information to resolve the user prompt.

```
[User Query] ➔ [Thought] ➔ [Select Tool] ➔ [Execute & Observe] ➔ [Final Answer]
```

---

## 4. Measuring RAG Performance (Evaluation)

To build reliable RAG systems, developers must quantitatively measure system accuracy. Limitless includes an automated evaluation suite (`scripts/eval.py`):

* **Context Precision**: Did the search engine successfully retrieve the necessary information to answer the question?
* **Faithfulness (Hallucination Detection)**: Is the generated LLM response strictly derived from the retrieved documents, or did it make up external facts?
* **Answer Relevance**: Did the model directly address the user's specific query?

---

## 5. Exercises & Self-Guided Challenges

1. **Implement Cosine Similarity manually**: Write a Python function in `app/utils/math.py` that computes the cosine similarity between two 1D NumPy lists without relying on Scikit-Learn or Pinecone.
2. **Add a custom Calculator Tool**: Integrate a simple safe math calculator tool (`numexpr`) into `app/services/agent.py` to prevent the LLM from making basic arithmetic errors when analyzing numbers inside PDFs.
3. **Convert RAG Eval to LLM-as-a-Judge**: Modify `scripts/eval.py` to call Groq Llama-3 to grade responses as "PASS/FAIL" semantically instead of relying on string keyword checks.
