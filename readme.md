# The "AI Co-worker" Engine - Gucci Group CHRO

This repository contains the prototype for an AI-powered Chief Human Resources Officer (CHRO) simulation, developed as part of the AI Engineer Intern Take-home Assignment for Edtronaut.

The system goes beyond a standard Q&A chatbot by implementing an orchestration layer, dynamic sentiment routing, a pure-Python RAG pipeline, and an invisible director layer to keep the user on track.

## ✨ Key Features
* **Role-Playing Fidelity:** The AI rigidly adheres to the Gucci Group CHRO persona, protecting brand DNA and utilizing a 4-pillar competency framework (Vision, Entrepreneurship, Passion, Trust).
* **Supervisor Architecture:** A multi-agent orchestration pattern handling Routing, Tool Use, Retrieval, and Response Generation.
* **Invisible Director Layer:** Uses Jaccard Similarity to detect if the user is stuck in a loop (>40% vocabulary overlap) and subtly injects hints to guide them.
* **Smart Routing & Sentiment:** Dynamically categorizes queries by intent and user sentiment (professional, frustrated, confused) using Gemini-2.5-Flash to adjust the AI's tone in real-time.
* **Pure-Python VectorStore:** A custom, dependency-light Vector Database computing Cosine Similarity directly in RAM. Ensures 100% portability without complex C++ library installations (like FAISS/Chroma).

## 🛠️ Tech Stack
* **Language:** Python 3.11
* **LLM Provider:** Google Generative AI (Gemini 2.5 Flash & Text Embedding 004)
* **Backend:** FastAPI, Uvicorn
* **Configuration:** Pydantic, python-dotenv
