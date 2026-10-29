import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";


const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";


function App() {
  const [documents, setDocuments] = useState([]);

  const [conversations, setConversations] = useState([]);

  const [conversationId, setConversationId] = useState(null);

  const [messages, setMessages] = useState([]);

  const [question, setQuestion] = useState("");

  const [sources, setSources] = useState([]);

  const [selectedFile, setSelectedFile] = useState(null);

  const [uploadStatus, setUploadStatus] = useState("");

  const [isLoading, setIsLoading] = useState(false);

  const [isUploading, setIsUploading] = useState(false);

  const [deletingDocumentId, setDeletingDocumentId] = useState(null);


  // =========================================================
  // INITIAL DATA LOAD
  // =========================================================

  useEffect(() => {
    loadDocuments();
    loadConversations();
  }, []);


  // =========================================================
  // LOAD DOCUMENTS
  // =========================================================

  const loadDocuments = async () => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/documents/`
      );

      setDocuments(response.data);
    } catch (error) {
      console.error(
        "Unable to load documents:",
        error
      );
    }
  };


  // =========================================================
  // LOAD CONVERSATIONS
  // =========================================================

  const loadConversations = async () => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/chat/conversations`
      );

      setConversations(response.data);
    } catch (error) {
      console.error(
        "Unable to load conversations:",
        error
      );
    }
  };


  // =========================================================
  // FILE SELECTION
  // =========================================================

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    setSelectedFile(file);
    setUploadStatus("");
  };


  // =========================================================
  // UPLOAD DOCUMENT
  // =========================================================

  const uploadDocument = async () => {
    if (!selectedFile) {
      setUploadStatus(
        "Please select a document first."
      );

      return;
    }

    const formData = new FormData();

    formData.append(
      "file",
      selectedFile
    );

    setIsUploading(true);

    setUploadStatus(
      "Uploading document..."
    );

    try {
      const response = await axios.post(
        `${API_BASE_URL}/documents/upload`,
        formData
      );

      setUploadStatus(
        `${response.data.filename} uploaded successfully. ` +
        `${response.data.chunks_created} chunks and ` +
        `${response.data.embeddings_created} embeddings created.`
      );

      setSelectedFile(null);

      const fileInput =
        document.getElementById(
          "document-upload"
        );

      if (fileInput) {
        fileInput.value = "";
      }

      await loadDocuments();

    } catch (error) {
      console.error(
        "Unable to upload document:",
        error
      );

      const detail =
        error.response?.data?.detail;

      setUploadStatus(
        detail ||
        "Unable to upload the document."
      );

    } finally {
      setIsUploading(false);
    }
  };


  // =========================================================
  // DELETE DOCUMENT
  // =========================================================

  const deleteDocument = async (
    documentId,
    filename
  ) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${filename}"?`
    );

    if (!confirmed) {
      return;
    }

    setDeletingDocumentId(documentId);

    try {
      await axios.delete(
        `${API_BASE_URL}/documents/${documentId}`
      );

      setUploadStatus(
        `${filename} deleted successfully.`
      );

      await loadDocuments();

      // Clear sources if the deleted document
      // was being displayed in the current chat.
      setSources([]);

    } catch (error) {
      console.error(
        "Unable to delete document:",
        error
      );

      const detail =
        error.response?.data?.detail;

      setUploadStatus(
        detail ||
        "Unable to delete the document."
      );

    } finally {
      setDeletingDocumentId(null);
    }
  };


  // =========================================================
  // START NEW CONVERSATION
  // =========================================================

  const startNewConversation = () => {
    setConversationId(null);

    setMessages([]);

    setSources([]);

    setQuestion("");
  };


  // =========================================================
  // OPEN EXISTING CONVERSATION
  // =========================================================

  const openConversation = async (id) => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/chat/conversations/${id}`
      );

      setConversationId(
        response.data.id
      );

      setMessages(
        response.data.messages || []
      );

      setSources([]);

      setQuestion("");

    } catch (error) {
      console.error(
        "Unable to load conversation:",
        error
      );
    }
  };


  // =========================================================
  // SEND QUESTION
  // =========================================================

  const sendQuestion = async () => {
    if (
      !question.trim() ||
      isLoading
    ) {
      return;
    }

    const currentQuestion =
      question.trim();

    setQuestion("");

    setIsLoading(true);

    // Display user's message immediately.
    setMessages(
      (previousMessages) => [
        ...previousMessages,
        {
          role: "user",
          content: currentQuestion,
        },
      ]
    );

    try {
      const response =
        await axios.post(
          `${API_BASE_URL}/chat/ask`,
          {
            question: currentQuestion,
            conversation_id:
              conversationId,
            top_k: 3,
          }
        );

      const data =
        response.data;

      setConversationId(
        data.conversation_id
      );

      setMessages(
        (previousMessages) => [
          ...previousMessages,
          {
            role: "assistant",
            content: data.answer,
          },
        ]
      );

      setSources(
        data.sources || []
      );

      await loadConversations();

    } catch (error) {
      console.error(
        "Unable to send question:",
        error
      );

      setMessages(
        (previousMessages) => [
          ...previousMessages,
          {
            role: "assistant",
            content:
              "Unable to process the question. " +
              "Please make sure the backend and Ollama are running.",
          },
        ]
      );

    } finally {
      setIsLoading(false);
    }
  };


  // =========================================================
  // ENTER KEY HANDLING
  // =========================================================

  const handleQuestionKeyDown = (
    event
  ) => {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();

      sendQuestion();
    }
  };


  // =========================================================
  // CONVERSATION TITLE
  // =========================================================

  const getConversationTitle = (
    conversation
  ) => {
    const firstUserMessage =
      conversation.messages?.find(
        (message) =>
          message.role === "user"
      );

    if (!firstUserMessage) {
      return `Conversation #${conversation.id}`;
    }

    const title =
      firstUserMessage.content.trim();

    if (title.length <= 42) {
      return title;
    }

    return `${title.substring(0, 42)}...`;
  };


  // =========================================================
  // FORMAT DATE
  // =========================================================

  const formatDate = (
    createdAt
  ) => {
    if (!createdAt) {
      return "";
    }

    return new Date(
      createdAt
    ).toLocaleDateString();
  };


  // =========================================================
  // UI
  // =========================================================

  return (
    <div className="app">

      {/* =====================================================
          LEFT SIDEBAR
      ====================================================== */}

      <aside className="sidebar">

        <div className="sidebar-header">

          <h1>
            Enterprise Knowledge
          </h1>

          <p>
            AI Assistant
          </p>

        </div>


        {/* ---------------------------------------------------
            NEW CHAT
        ---------------------------------------------------- */}

        <button
          className="new-chat-button"
          onClick={
            startNewConversation
          }
        >
          + New Chat
        </button>


        {/* ---------------------------------------------------
            CONVERSATIONS
        ---------------------------------------------------- */}

        <section className="sidebar-section">

          <h2>
            Conversations
          </h2>

          {conversations.length === 0 ? (

            <p className="empty-state">
              No conversations yet.
            </p>

          ) : (

            <div className="conversation-list">

              {conversations.map(
                (conversation) => (

                  <button
                    key={
                      conversation.id
                    }
                    className={
                      conversationId ===
                      conversation.id
                        ? "conversation-item active"
                        : "conversation-item"
                    }
                    onClick={() =>
                      openConversation(
                        conversation.id
                      )
                    }
                  >

                    <span className="conversation-icon">
                      💬
                    </span>

                    <span className="conversation-title">
                      {getConversationTitle(
                        conversation
                      )}
                    </span>

                  </button>

                )
              )}

            </div>

          )}

        </section>


        {/* ---------------------------------------------------
            KNOWLEDGE BASE
        ---------------------------------------------------- */}

        <section className="sidebar-section">

          <h2>
            Knowledge Base
          </h2>


          {/* Upload */}

          <div className="upload-area">

            <input
              id="document-upload"
              type="file"
              accept=".pdf,.txt"
              onChange={
                handleFileChange
              }
            />

            {selectedFile && (

              <p className="selected-file">
                {selectedFile.name}
              </p>

            )}

            <button
              className="upload-button"
              onClick={
                uploadDocument
              }
              disabled={
                !selectedFile ||
                isUploading
              }
            >
              {isUploading
                ? "Uploading..."
                : "Upload Document"}
            </button>

            {uploadStatus && (

              <p className="upload-status">
                {uploadStatus}
              </p>

            )}

          </div>


          {/* Documents */}

          <div className="document-list">

            {documents.length === 0 ? (

              <p className="empty-state">
                No documents uploaded yet.
              </p>

            ) : (

              documents.map(
                (document) => (

                  <div
                    className="document-item"
                    key={
                      document.id
                    }
                  >

                    <div className="document-main">

                      <span className="document-icon">
                        📄
                      </span>

                      <div className="document-info">

                        <strong>
                          {document.filename}
                        </strong>

                        <span>
                          Document #{document.id}
                        </span>

                        <span>
                          {document.chunk_count} chunks
                        </span>

                        <span>
                          {formatDate(
                            document.created_at
                          )}
                        </span>

                      </div>

                    </div>


                    <button
                      className="delete-button"
                      onClick={() =>
                        deleteDocument(
                          document.id,
                          document.filename
                        )
                      }
                      disabled={
                        deletingDocumentId ===
                        document.id
                      }
                      title="Delete document"
                    >
                      {deletingDocumentId ===
                      document.id
                        ? "..."
                        : "Delete"}
                    </button>

                  </div>

                )
              )

            )}

          </div>

        </section>

      </aside>


      {/* =====================================================
          CHAT PANEL
      ====================================================== */}

      <main className="chat-panel">

        <header className="chat-header">

          <div>

            <h2>
              Enterprise Knowledge Assistant
            </h2>

            <p>
              Ask questions about your
              uploaded enterprise documents.
            </p>

          </div>


          {conversationId && (

            <span className="conversation-id">
              Conversation #{conversationId}
            </span>

          )}

        </header>


        {/* ---------------------------------------------------
            MESSAGES
        ---------------------------------------------------- */}

        <div className="messages">

          {messages.length === 0 ? (

            <div className="welcome-message">

              <div className="welcome-icon">
                🤖
              </div>

              <h2>
                How can I help?
              </h2>

              <p>
                Ask a question about the
                documents in your knowledge base.
              </p>

              <div className="example-question">

                Example:

                <strong>
                  How much vacation time do
                  employees receive?
                </strong>

              </div>

            </div>

          ) : (

            messages.map(
              (message, index) => (

                <div
                  key={
                    message.id ||
                    `${message.role}-${index}`
                  }
                  className={
                    message.role === "user"
                      ? "message user-message"
                      : "message assistant-message"
                  }
                >

                  <div className="message-role">

                    {message.role === "user"
                      ? "You"
                      : "AI Assistant"}

                  </div>

                  <div className="message-content">
                    {message.content}
                  </div>

                </div>

              )
            )

          )}


          {isLoading && (

            <div className="message assistant-message">

              <div className="message-role">
                AI Assistant
              </div>

              <div className="message-content loading">
                Thinking...
              </div>

            </div>

          )}

        </div>


        {/* ---------------------------------------------------
            CHAT INPUT
        ---------------------------------------------------- */}

        <div className="chat-input-area">

          <textarea
            value={question}
            onChange={(event) =>
              setQuestion(
                event.target.value
              )
            }
            onKeyDown={
              handleQuestionKeyDown
            }
            placeholder="Ask a question about your documents..."
            rows={2}
            disabled={isLoading}
          />

          <button
            className="send-button"
            onClick={sendQuestion}
            disabled={
              !question.trim() ||
              isLoading
            }
          >
            {isLoading
              ? "..."
              : "Send"}
          </button>

        </div>

      </main>


      {/* =====================================================
          SOURCES PANEL
      ====================================================== */}

      <aside className="sources-panel">

        <div className="sources-header">

          <h2>
            Sources
          </h2>

          <p>
            Retrieved document references
          </p>

        </div>


        {sources.length === 0 ? (

          <div className="sources-empty">

            <span>
              🔎
            </span>

            <p>
              Sources will appear here after
              you ask a question.
            </p>

          </div>

        ) : (

          <div className="source-list">

            {sources.map(
              (source, index) => (

                <div
                  className="source-card"
                  key={
                    source.chunk_id ||
                    index
                  }
                >

                  <div className="source-title">
                    📄 {source.filename}
                  </div>

                  <div className="source-details">

                    <span>
                      Document #{source.document_id}
                    </span>

                    <span>
                      Chunk #{source.chunk_index}
                    </span>

                    <span>
                      Similarity:{" "}
                      {source.similarity}
                    </span>

                  </div>

                </div>

              )
            )}

          </div>

        )}

      </aside>

    </div>
  );
}


export default App;