\# Orin



\## Learn. Code. Evolve.



Orin is an AI-powered learning and coding platform designed to help students understand technical concepts, practice programming, receive guided feedback, and track their learning progress in one workspace.



The platform combines AI tutoring, multilingual learning, document-grounded assistance, coding practice, automated evaluation, and progress tracking.



\---



\## Overview



Traditional learning workflows often separate explanation, practice, coding, debugging, and progress tracking across multiple tools.



Orin is designed to connect these activities into a continuous learning workflow:



```text

Learn

&#x20; ↓

Understand

&#x20; ↓

Practice

&#x20; ↓

Code

&#x20; ↓

Test

&#x20; ↓

Feedback

&#x20; ↓

Improve

```



The objective is not simply to provide answers, but to create a structured environment where learners can understand concepts and improve through practice.



\---



\## Core Capabilities



\### AI Tutor



Orin provides a conversational AI tutor designed around the learner's context.



Capabilities include:



\- Streaming AI responses

\- Conversation history

\- Learner skill-level awareness

\- Multilingual explanations

\- Language and script preferences

\- Concept explanations

\- Step-by-step learning assistance

\- Coding explanations and debugging support

\- Image-based questions

\- Conversation management

\- Stop and retry controls



\---



\### Multilingual Learning



The language layer allows Orin to adapt explanations to the learner's preferred language and writing style.



The system includes:



\- Language detection

\- Preferred language settings

\- Script preferences

\- Learner-level context

\- Language-aware prompt construction

\- Technical vocabulary handling



Language-specific behavior is separated from the core tutoring logic so that additional languages can be introduced without restructuring the application.



\---



\### Document-Based Learning



Orin includes a document processing and retrieval pipeline for learning material.



The workflow is:



```text

Document Upload

&#x20;     ↓

Text Extraction

&#x20;     ↓

Chunking

&#x20;     ↓

Embeddings

&#x20;     ↓

Vector Retrieval

&#x20;     ↓

Relevant Context

&#x20;     ↓

Language Model

&#x20;     ↓

Grounded Response

```



The system is designed to allow learners to ask questions about their own study material rather than relying only on general model knowledge.



\---



\### Image-Based Questions



The Tutor supports image attachments for learning-related questions.



Supported workflows include:



\- Image upload

\- Drag and drop

\- Image preview

\- Image lightbox

\- Vision-model based analysis



This can be used for screenshots, diagrams, handwritten notes, code screenshots, and other learning material.



\---



\### Orin Code



Orin includes a dedicated coding environment for structured programming practice.



Current capabilities include:



\- Coding problem browser

\- Python problems

\- JavaScript problems

\- Difficulty filtering

\- Topic organization

\- Problem search

\- Monaco Editor

\- Code execution

\- Code submission

\- Visible test cases

\- Hidden test cases

\- Test results

\- Submission history

\- Coding progress



The coding problem bank is structured as a progression of programming concepts rather than simply a collection of unrelated questions.



\---



\### Code Evaluation



Submitted programs are evaluated against configured test cases.



The evaluation pipeline includes:



```text

Code Submission

&#x20;     ↓

Problem Validation

&#x20;     ↓

Language Validation

&#x20;     ↓

Test Case Loading

&#x20;     ↓

Code Execution

&#x20;     ↓

Output Evaluation

&#x20;     ↓

Test Results

&#x20;     ↓

Submission Storage

```



The evaluator tracks:



\- Passed tests

\- Failed tests

\- Hidden tests

\- Execution time

\- Runtime errors

\- Timeouts

\- Submission status



For local development, Orin can execute code through a local subprocess when explicitly enabled.



This configuration is intended only for trusted development environments. It should not be considered a production-grade sandbox for arbitrary public code execution.



\---



\### Learning Progress



Orin records coding activity and derives progress information from stored submissions.



Current metrics include:



\- Total submissions

\- Problems attempted

\- Problems solved

\- Tests passed

\- Total tests

\- Test accuracy

\- Python submissions

\- JavaScript submissions

\- Recent submissions



The progress interface is based on actual application data rather than placeholder statistics.



\---



\### Authentication and Profiles



Orin includes authenticated user workflows with:



\- User registration

\- Login

\- JWT authentication

\- Protected API routes

\- User profiles

\- Learning preferences



\---



\## Architecture



Orin uses a React and TypeScript frontend backed by a FastAPI application.



```text

&#x20;                        Orin Frontend

&#x20;                             |

&#x20;                   React / TypeScript / Vite

&#x20;                             |

&#x20;                        REST API

&#x20;                             |

&#x20;                   FastAPI Application

&#x20;                             |

&#x20;       +---------------------+---------------------+

&#x20;       |                     |                     |

&#x20;       v                     v                     v

&#x20;   AI Services          RAG Services        Coding Services

&#x20;       |                     |                     |

&#x20;       v                     v                     v

&#x20;  Language Models       Embeddings          Code Evaluator

&#x20;       |                     |                     |

&#x20;       +---------------------+---------------------+

&#x20;                             |

&#x20;                       SQLAlchemy ORM

&#x20;                             |

&#x20;                          SQLite

```



The backend is divided into domain-oriented services:



```text

backend/app/

├── api/

│   ├── auth.py

│   ├── coding.py

│   ├── documents.py

│   ├── tutor.py

│   └── progress.py

│

├── core/

├── models/

├── schemas/

│

└── services/

&#x20;   ├── ai/

&#x20;   ├── coding/

&#x20;   ├── language/

&#x20;   ├── learning/

&#x20;   └── rag/

```



\---



\## AI Architecture



The AI layer uses a provider-oriented structure.



```text

User Request

&#x20;    ↓

User Profile

&#x20;    ↓

Language Context

&#x20;    ↓

Prompt Construction

&#x20;    ↓

AI Provider

&#x20;    ↓

Language Model

&#x20;    ↓

Streaming Response

```



The architecture separates:



\- AI provider interfaces

\- Provider implementations

\- Prompt construction

\- Language profiles

\- Tutor behavior

\- Retrieval context

\- Image-based requests



This allows model providers to be changed or extended without coupling the entire application to a single implementation.



\---



\## Technology Stack



| Layer | Technology |

|---|---|

| Frontend | React |

| Frontend Language | TypeScript |

| Build Tool | Vite |

| Styling | Tailwind CSS |

| Code Editor | Monaco Editor |

| Backend | FastAPI |

| Backend Language | Python |

| ORM | SQLAlchemy |

| Database | SQLite |

| Authentication | JWT |

| AI Integration | Configurable LLM providers |

| Local AI | Ollama |

| Retrieval | Embeddings and vector search |

| API | REST |

| Version Control | Git |



\---



\## Project Structure



```text

orin/

├── backend/

│   ├── app/

│   │   ├── api/

│   │   ├── core/

│   │   ├── models/

│   │   ├── schemas/

│   │   └── services/

│   │

│   ├── tests/

│   ├── tools/

│   ├── requirements.txt

│   └── .env.example

│

├── frontend/

│   ├── src/

│   │   ├── components/

│   │   ├── context/

│   │   ├── layouts/

│   │   ├── lib/

│   │   ├── pages/

│   │   └── services/

│   │

│   ├── package.json

│   └── vite.config.ts

│

├── docs/

│   └── SETUP.md

│

├── README.md

└── .gitignore

```



\---



\## Local Development



\### Requirements



The current development environment uses:



\- Python 3.10+

\- Node.js

\- npm

\- Ollama for local AI usage



\### Clone the repository



```bash

git clone https://github.com/thvarsha00/orin.git

cd orin

```



\### Backend



```powershell

cd backend

python -m venv venv

venv\\Scripts\\activate

pip install -r requirements.txt

```



Create the local environment configuration from:



```text

backend/.env.example

```



Start the backend:



```powershell

uvicorn app.main:app --reload --port 8000

```



The API will be available at:



```text

http://localhost:8000

```



FastAPI documentation:



```text

http://localhost:8000/docs

```



\### Frontend



Open another terminal:



```powershell

cd frontend

npm install

npm run dev

```



Vite will display the local development URL.



\### Production build



```powershell

cd frontend

npm run build

```



The production build is generated in:



```text

frontend/dist/

```



\---



\## Environment Configuration



Local environment variables should be stored in:



```text

backend/.env

```



The repository provides:



```text

backend/.env.example

```



as the configuration template.



Depending on the selected AI configuration, environment variables may include:



```text

AI\_PROVIDER

OLLAMA\_BASE\_URL

OLLAMA\_MODEL

CODE\_RUNNER

CODE\_ALLOW\_UNSAFE\_LOCAL

```



Real credentials and secrets must never be committed to the repository.



\---



\## Coding Problem Bank



Coding problems are maintained as structured data and seeded into the application database.



A problem can contain:



\- Title

\- Description

\- Difficulty

\- Topic

\- Tags

\- Hints

\- Constraints

\- Starter code

\- Examples

\- Visible tests

\- Hidden tests

\- Reference solution

\- Expected complexity



The problem bank is designed around progressive learning across programming concepts.



\---



\## Testing



Backend tests are located in:



```text

backend/tests/

```



Run the backend tests with:



```powershell

cd backend

venv\\Scripts\\activate

pytest

```



The frontend production build performs TypeScript checking and Vite compilation:



```powershell

cd frontend

npm run build

```



\---



\## Development Status



Orin is an actively developed project.



\### Implemented



\- Authentication

\- User profiles

\- AI Tutor

\- Streaming conversations

\- Conversation history

\- Multilingual language support

\- Language and script preferences

\- Image-based Tutor questions

\- Document processing

\- Retrieval-augmented generation

\- Source-aware document responses

\- Coding problem bank

\- Coding workspace

\- Monaco Editor integration

\- Code execution for supported development languages

\- Automated test evaluation

\- Submission history

\- Coding progress

\- Dashboard

\- Progress page

\- Settings



\### In Development



\- Voice input

\- Text-to-speech and read-aloud features

\- Additional coding languages

\- Expanded adaptive learning

\- Deeper personalized recommendations

\- Production-grade isolated code execution

\- Deployment hardening

\- Expanded automated test coverage



\---



\## Production Considerations



Orin is currently a development-stage application.



Before public production deployment, the following areas require additional hardening:



\- Secret management

\- HTTPS

\- Production database configuration

\- Rate limiting

\- Authentication hardening

\- File upload security

\- RAG storage security

\- Resource limits

\- Isolated code execution

\- Production logging

\- Monitoring

\- Error handling

\- CORS configuration



In particular, arbitrary submitted code should not be executed through an unrestricted local subprocess in a public production environment.



\---



\## Product Direction



Orin is being developed around a simple principle:



> AI should help students understand, not just answer.



The long-term platform combines:



```text

AI Tutoring

&#x20;    +

Multilingual Learning

&#x20;    +

Document-Grounded Learning

&#x20;    +

Coding Practice

&#x20;    +

Automated Evaluation

&#x20;    +

Progress Tracking

&#x20;    +

Adaptive Recommendations

```



into one connected learning environment.



\---



\## Author



\*\*Varsha Vanganuru\*\*



AI / ML · Generative AI · Data Analytics



GitHub:



https://github.com/thvarsha00



\---



\## Documentation



Additional setup and development information is available in:



```text

docs/SETUP.md

```



\---



\## License



License information will be added as the project moves toward public release.

