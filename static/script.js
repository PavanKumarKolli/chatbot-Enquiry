// ==========================================
// EduAssist AI Chatbot - Client Interaction Script
// ==========================================

document.addEventListener("DOMContentLoaded", () => {
    // DOM Selectors
    const chatForm = document.getElementById("chat-form");
    const userInput = document.getElementById("user-input");
    const chatMessages = document.getElementById("chat-messages");
    const typingIndicator = document.getElementById("typing-indicator");
    const clearBtn = document.getElementById("clear-btn");
    const sidebarExitBtn = document.getElementById("sidebar-exit-btn");
    const exitModal = document.getElementById("exit-modal");
    const welcomeTime = document.getElementById("welcome-time");

    // Set welcome message timestamp to current time
    if (welcomeTime) {
        welcomeTime.textContent = getCurrentTime();
    }

    // Scroll to bottom of chat
    scrollToBottom();

    // Focus input on load
    userInput.focus();

    // Chat form submit handler
    chatForm.addEventListener("submit", (e) => {
        e.preventDefault();
        handleMessageSend();
    });

    // Clear chat button click
    clearBtn.addEventListener("click", () => {
        // Clear all messages except the first welcome message
        const messages = Array.from(chatMessages.querySelectorAll(".message"));
        messages.forEach((msg, index) => {
            if (index > 0) {
                msg.remove();
            }
        });
        appendSystemMessage("Chat history cleared.");
    });

    // Exit Chat Button
    sidebarExitBtn.addEventListener("click", () => {
        // Trigger immediate exit sequence
        triggerExitSequence("Goodbye! Exit requested. Session closed.");
    });

    // Handles user message submission
    function handleMessageSend() {
        const text = userInput.value.trim();
        if (!text) return;

        // 1. Render User Message
        appendMessage(text, "user");
        userInput.value = "";
        scrollToBottom();

        // 2. Show Typing Indicator
        showTypingIndicator(true);

        // 3. Post to backend API
        fetch("/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ message: text })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error("Network response was not ok");
            }
            return response.json();
        })
        .then(data => {
            // Introduce a short artificial delay for typing realism
            setTimeout(() => {
                showTypingIndicator(false);
                appendMessage(data.response, "bot");
                scrollToBottom();

                // If chatbot returned exit signal
                if (data.is_exit) {
                    triggerExitSequence();
                }
            }, 600);
        })
        .catch(err => {
            console.error("Error communicating with chatbot API:", err);
            setTimeout(() => {
                showTypingIndicator(false);
                appendMessage("Sorry, I'm experiencing technical difficulties. Please check if the server is running and try again.", "bot");
                scrollToBottom();
            }, 600);
        });
    }

    // Helper: Get formatted current time (HH:MM AM/PM)
    function getCurrentTime() {
        const now = new Date();
        let hours = now.getHours();
        const minutes = now.getMinutes().toString().padStart(2, "0");
        const ampm = hours >= 12 ? "PM" : "AM";
        hours = hours % 12;
        hours = hours ? hours : 12; // the hour '0' should be '12'
        return `${hours}:${minutes} ${ampm}`;
    }

    // Helper: Scroll to bottom of message container
    function scrollToBottom() {
        setTimeout(() => {
            chatMessages.scrollTo({
                top: chatMessages.scrollHeight,
                behavior: "smooth"
            });
        }, 50);
    }

    // Helper: Show/Hide typing indicator
    function showTypingIndicator(show) {
        typingIndicator.style.display = show ? "flex" : "none";
        scrollToBottom();
    }

    // Helper: Append User or Bot message to DOM
    function appendMessage(text, sender) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", `${sender}-message`);

        const bubbleDiv = document.createElement("div");
        bubbleDiv.classList.add("message-bubble");
        
        if (sender === "bot") {
            // Process markdown syntax for bot messages
            bubbleDiv.innerHTML = parseMarkdown(text);
        } else {
            // Treat user messages as plain text for security
            bubbleDiv.textContent = text;
        }

        const timeSpan = document.createElement("span");
        timeSpan.classList.add("message-time");
        timeSpan.textContent = getCurrentTime();

        messageDiv.appendChild(bubbleDiv);
        messageDiv.appendChild(timeSpan);
        chatMessages.appendChild(messageDiv);
        
        // Auto scroll to the last message
        scrollToBottom();
    }

    // Helper: Append systemic notice text
    function appendSystemMessage(text) {
        const noticeDiv = document.createElement("div");
        noticeDiv.style.textAlign = "center";
        noticeDiv.style.color = "var(--text-muted)";
        noticeDiv.style.fontSize = "11px";
        noticeDiv.style.margin = "10px 0";
        noticeDiv.textContent = text;
        chatMessages.appendChild(noticeDiv);
        scrollToBottom();
    }

    // Custom Markdown-to-HTML parser for bullet lists and bold text
    function parseMarkdown(text) {
        // Split by lines to parse bullet points
        const lines = text.split("\n");
        let inList = false;
        const htmlResult = [];

        lines.forEach(line => {
            let cleanLine = line.trim();
            // Match markdown bullet lines starting with "* " or "- "
            if (cleanLine.startsWith("* ") || cleanLine.startsWith("- ")) {
                if (!inList) {
                    htmlResult.push("<ul>");
                    inList = true;
                }
                const content = cleanLine.substring(2);
                const formattedContent = formatInlineMarkdown(content);
                htmlResult.push(`<li>${formattedContent}</li>`);
            } else {
                if (inList) {
                    htmlResult.push("</ul>");
                    inList = false;
                }
                const formattedContent = formatInlineMarkdown(line);
                htmlResult.push(formattedContent);
            }
        });

        if (inList) {
            htmlResult.push("</ul>");
        }

        // Return combined list and replace consecutive newlines with single break
        return htmlResult.join("<br>").replace(/(<br>){3,}/g, "<br><br>");
    }

    // Process bold (**bold**) inline markdown
    function formatInlineMarkdown(text) {
        return text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    }

    // Triggers Exit sequence (disables input, shows overlay)
    function triggerExitSequence(goodbyeMessage) {
        // 1. Disable inputs
        userInput.disabled = true;
        userInput.placeholder = "Session closed. Click 'Restart Chat' to begin a new session.";
        const sendBtn = document.getElementById("send-btn");
        if (sendBtn) sendBtn.disabled = true;

        if (goodbyeMessage) {
            appendMessage(goodbyeMessage, "bot");
            scrollToBottom();
        }

        // 2. Open End-of-Session modal overlay after a short delay
        setTimeout(() => {
            exitModal.classList.add("active");
        }, 1500);
    }

    // Expose quick query sender to window scope
    window.sendQuickQuery = function(queryText) {
        // Don't send if input is disabled (session ended)
        if (userInput.disabled) return;
        
        userInput.value = queryText;
        handleMessageSend();
    };
});
