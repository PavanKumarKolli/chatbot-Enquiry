import json
import re
import random
import difflib

# Define a set of English stop words to filter out
STOP_WORDS = {
    "a", "an", "the", "is", "are", "am", "was", "were", "to", "for", "at", 
    "in", "on", "of", "with", "about", "you", "your", "please", "would", 
    "could", "should", "do", "does", "did", "have", "has", "had", "i",
    "me", "my", "we", "our", "us", "it", "its", "they", "them", "their",
    "can", "will", "shall", "tell", "show", "give", "get", "want", "need",
    "know", "like", "information", "info", "details", "detail"
}

class StudentChatbot:
    def __init__(self, dataset_path="dataset.json"):
        self.dataset_path = dataset_path
        self.load_dataset()

    def load_dataset(self):
        try:
            with open(self.dataset_path, "r", encoding="utf-8") as f:
                self.dataset = json.load(f)
        except Exception as e:
            print(f"Error loading dataset: {e}")
            self.dataset = {}

    def preprocess_text(self, text):
        """
        Normalize text: lowercase, remove special characters, tokenise, and filter stop words.
        """
        # Convert to lowercase and strip whitespace
        text = text.lower().strip()
        # Remove punctuation/special characters
        text = re.sub(r"[^\w\s]", "", text)
        # Tokenize by split
        tokens = text.split()
        # Filter stop words
        filtered_tokens = [t for t in tokens if t not in STOP_WORDS]
        return text, set(filtered_tokens)

    def get_response(self, user_query):
        """
        Processes user query, finds the best matching category using token overlap and
        sequence matching, and returns a response, category name, and exit flag.
        """
        if not user_query or not user_query.strip():
            return "Please type a question, and I'll do my best to help!", "empty", False

        normalized_query, query_tokens = self.preprocess_text(user_query)

        # 1. Check for immediate goodbye / exit commands
        exit_keywords = {"exit", "quit", "stop", "close", "bye", "goodbye"}
        if normalized_query in exit_keywords or any(w in query_tokens for w in {"exit", "quit", "stop"}):
            responses = self.dataset.get("goodbyes", {}).get("responses", ["Goodbye!"])
            return random.choice(responses), "goodbyes", True

        # 2. Check for general help
        help_keywords = {"help", "menu", "options", "commands"}
        if normalized_query in help_keywords or any(w in query_tokens for w in {"help", "menu"}):
            responses = self.dataset.get("help", {}).get("responses", ["How can I help?"])
            return random.choice(responses), "help", False

        # 3. Check greetings (exact word matches or starts with common greetings)
        greeting_keywords = {"hi", "hello", "hey", "greetings", "hola"}
        words_in_query = set(normalized_query.split())
        if normalized_query in greeting_keywords or not words_in_query.isdisjoint(greeting_keywords):
            # Check if it's just a greeting or start of message
            # If the query contains other major words, let the similarity check handle it
            if len(words_in_query) <= 3:
                responses = self.dataset.get("greetings", {}).get("responses", ["Hello!"])
                return random.choice(responses), "greetings", False

        # 4. Search and match other categories
        best_category = None
        best_score = 0.0

        # High priority keywords to boost specific categories
        keyword_boosts = {
            "chitchat_status": ["how are you", "doing", "going", "feeling", "ok", "fine", "good"],
            "chitchat_identity": ["who are you", "your name", "about yourself", "who is", "creator", "bot", "assistant", "what are you"],
            "chitchat_appreciation": ["thank", "thanks", "nice", "awesome", "great", "cool", "perfect", "helpful", "good job", "buddy"],
            "chitchat_jokes": ["joke", "jokes", "laugh", "funny", "riddle"],
            "stress_comfort": ["stress", "stressed", "tired", "exhausted", "anxious", "sad", "overwhelmed", "bad day", "rough day", "down"],
            "relax_tips": ["relax", "unwind", "calm", "tips", "breathing", "stretch", "bored"],
            "chitchat_user_status": ["good", "fine", "ok", "doing well", "happy", "great", "doing good", "not bad"]
        }

        # Exclude internal categories from general similarity search
        search_categories = [c for c in self.dataset.keys() if c not in ["greetings", "goodbyes", "help", "fallback"]]

        for category in search_categories:
            patterns = self.dataset[category].get("patterns", [])
            
            # Category keyword boost
            boost = 0.0
            if category in keyword_boosts:
                for kw in keyword_boosts[category]:
                    if kw in normalized_query:
                        boost += 0.25 # Boost for keyword match

            for pattern in patterns:
                norm_pattern, pattern_tokens = self.preprocess_text(pattern)

                # Token Jaccard Similarity
                overlap = len(query_tokens & pattern_tokens)
                union = len(query_tokens | pattern_tokens)
                token_similarity = overlap / union if union > 0 else 0.0

                # String Sequence Similarity (difflib)
                seq_similarity = difflib.SequenceMatcher(None, normalized_query, norm_pattern).ratio()

                # Combined score
                score = (0.4 * token_similarity) + (0.6 * seq_similarity) + boost
                
                # Cap the score at 1.0 (after boost)
                score = min(score, 1.0)

                if score > best_score:
                    best_score = score
                    best_category = category

        # Matching threshold
        THRESHOLD = 0.35

        if best_category and best_score >= THRESHOLD:
            responses = self.dataset[best_category].get("responses", [])
            return random.choice(responses), best_category, False
        else:
            # If no academic category matched but the query contains a greeting keyword, answer with a greeting
            if not words_in_query.isdisjoint(greeting_keywords) or any(w in query_tokens for w in greeting_keywords):
                responses = self.dataset.get("greetings", {}).get("responses", ["Hello!"])
                return random.choice(responses), "greetings", False

            # Fallback response
            fallback_responses = self.dataset.get("fallback", {}).get("responses", [
                "I'm sorry, I don't have information on that. Please ask about courses, fees, timings, or contact details."
            ])
            return random.choice(fallback_responses), "fallback", False

if __name__ == "__main__":
    # Test the chatbot in console mode
    bot = StudentChatbot()
    print("Chatbot Initialized. Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        response, category, is_exit = bot.get_response(user_input)
        print(f"Bot ({category}): {response}")
        if is_exit:
            break
