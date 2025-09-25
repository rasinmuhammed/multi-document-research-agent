# Orbuculum.ai - AI-Powered Research Assistant

Orbuculum.ai is a powerful research assistant that leverages large language models to provide comprehensive, well-cited answers by searching through both local documents and web resources. This application allows you to upload your own documents (PDF, Markdown, and TXT files) and then chat with an AI agent that can intelligently query and synthesize information from your local repository and the open web.

## Features

  * **Multi-Document Querying:** Upload and manage a library of PDF, Markdown, and text documents. The AI agent can read and understand the content of these files to answer your questions.
  * **Web Search Integration:** For topics not covered in your local documents, the agent can perform web searches to find the most relevant and up-to-date information.
  * **Intelligent Agent:** The research agent is designed to break down complex questions, create strategic search queries, and synthesize information from multiple sources into a coherent, well-structured response.
  * **Built-in Citations:** Every piece of information in the AI's response is accompanied by a citation, allowing you to easily trace the source of the information, whether it's from a local document or a webpage.
  * **Chat Interface:** An intuitive and user-friendly chat interface, built with React, allows for a seamless conversational experience with the research agent.
  * **Downloadable Reports:** Generate and download detailed research reports in Markdown format, complete with an executive summary, a list of sources, and a step-by-step look at the research methodology.

## Tech Stack

### Backend

  * **Flask:** A lightweight WSGI web application framework in Python.
  * **LangChain:** A framework for developing applications powered by language models.
  * **Groq:** A fast inference engine for large language models.
  * **ChromaDB:** An open-source embedding database for storing and querying document embeddings.
  * **Sentence Transformers:** A Python framework for state-of-the-art sentence, text, and image embeddings.

### Frontend

  * **React:** A JavaScript library for building user interfaces.
  * **Tailwind CSS:** A utility-first CSS framework for rapid UI development.
  * **Lucide React:** A library of simply designed, beautiful icons.

## Getting Started

### Prerequisites

  * Python 3.7+
  * Node.js and npm
  * A Groq API key

### Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/rasinmuhammed/multi-document-research-agent.git
    cd multi-document-research-agent
    ```

2.  **Set up the backend:**

      * Create and activate a virtual environment:

        ```bash
        python -m venv venv
        source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
        ```

      * Install the required Python packages:

        ```bash
        pip install -r requirements.txt
        ```

      * Create a `.env` file in the root directory and add your Groq API key:

        ```
        GROQ_API_KEY=YOUR_GROQ_API_KEY
        ```

3.  **Set up the frontend:**

      * Navigate to the `frontend` directory:

        ```bash
        cd frontend
        ```

      * Install the required npm packages:

        ```bash
        npm install
        ```

### Usage

1.  **Start the backend server:**

      * From the root directory, run:

        ```bash
        python app.py
        ```

      * The backend will be running at `http://localhost:5001`.

2.  **Start the frontend development server:**

      * From the `frontend` directory, run:

        ```bash
        npm start
        ```

      * The frontend will be running at `http://localhost:3000`.

3.  **Open your browser** and navigate to `http://localhost:3000` to start using the application.

## How It Works

1.  **Document Upload:** Users can upload PDF, Markdown, or text files through the web interface.
2.  **Document Processing and Indexing:** The backend processes the uploaded documents, splits them into chunks, generates embeddings for each chunk, and stores them in a ChromaDB vector store.
3.  **Chat Interface:** The user asks a question in the chat interface.
4.  **Research Agent:** The research agent receives the question and, using a series of tools, decides whether to search the local document vector store or the web.
5.  **Information Retrieval and Synthesis:** The agent retrieves the most relevant information from the chosen source(s) and synthesizes it into a comprehensive answer.
6.  **Response with Citations:** The final answer, complete with citations, is displayed in the chat interface.
