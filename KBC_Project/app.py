"""
KBC - Kaun Banega Crorepati
Python Flask Dynamic Backend
Run: pip install flask flask-cors requests
Then: python app.py
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import random
import html

app = Flask(__name__)
CORS(app)  # Allow frontend to call this API

# Global session dictionary to keep track of active games and their generated questions
# In a production app, use a real database/Redis session handler
GAME_SESSIONS = {}

# Safe milestones — money kept on wrong answer
SAFE_MILESTONES = {5: "₹10,000", 10: "₹3,20,000", 15: "₹1,00,00,000"}

PRIZE_LADDER = [
    {"id": 1, "prize": "₹1,00,0"}, {"id": 2, "prize": "₹2,000"}, {"id": 3, "prize": "₹3,000"},
    {"id": 4, "prize": "₹5,000"}, {"id": 5, "prize": "₹10,000"}, {"id": 6, "prize": "₹20,000"},
    {"id": 7, "prize": "₹40,000"}, {"id": 8, "prize": "₹80,000"}, {"id": 9, "prize": "₹1,60,000"},
    {"id": 10, "prize": "₹3,20,000"}, {"id": 11, "prize": "₹6,40,000"}, {"id": 12, "prize": "₹12,50,000"},
    {"id": 13, "prize": "₹25,00,000"}, {"id": 14, "prize": "₹50,00,000"}, {"id": 15, "prize": "₹1,00,00,000"}
]

TOTAL_QUESTIONS = len(PRIZE_LADDER)

# ─── Coding Backup Bank (In case OpenTDB api rate limits or lacks specific tech codes) ───
CODING_QUESTIONS = [
    {"question": "What does CSS stand for?", "options": ["Cascading Style Sheets", "Creative Style Sheets", "Computer Style Sheets", "Colorful Style Sheets"], "answer": "Cascading Style Sheets"},
    {"question": "Which programming language is known as the backbone of web development interactivity?", "options": ["Python", "Java", "JavaScript", "C++"], "answer": "JavaScript"},
    {"question": "In Python, which keyword is used to start a function definition?", "options": ["func", "define", "def", "function"], "answer": "def"},
    {"question": "What is the time complexity of searching in a perfectly balanced Binary Search Tree (BST)?", "options": ["O(1)", "O(n)", "O(log n)", "O(n log n)"], "answer": "O(log n)"},
    {"question": "Which data structure operates on a Last-In-First-Out (LIFO) paradigm?", "options": ["Queue", "Stack", "Linked List", "Heap"], "answer": "Stack"},
    {"question": "What Git command is used to save changes to your local repository?", "options": ["git push", "git save", "git commit", "git add"], "answer": "git commit"},
    {"question": "Which SQL statement is used to extract data from a database?", "options": ["EXTRACT", "GET", "OPEN", "SELECT"], "answer": "SELECT"},
    {"question": "What does API stand for?", "options": ["Application Programming Interface", "Automated Program Integration", "Advanced Processing Instrument", "App Protocol Interlink"], "answer": "Application Programming Interface"}
]

# ─── Helper Functions ────────────────────────────────────────────────────────

def fetch_dynamic_questions():
    """Fetches random questions across easy, medium, and hard difficulty brackets from OpenTDB API."""
    generated_list = []
    
    # KBC Progression Difficulty Mapping: 
    # Q1-5: Easy, Q6-10: Medium, Q11-15: Hard
    difficulty_map = (["easy"] * 5) + (["medium"] * 5) + (["hard"] * 5)
    
    # Categories: Mix of General Knowledge, Computers/Science, and Gadgets
    categories = [9, 18, 30] 

    for idx, difficulty in enumerate(difficulty_map, start=1):
        question_added = False
        
        # Inject random programming specific challenges into mid-to-high tier sets
        if idx in [4, 7, 11, 13] and CODING_QUESTIONS:
            local_q = random.choice(CODING_QUESTIONS)
            shuffled_opts = list(local_q["options"])
            random.shuffle(shuffled_opts)
            
            # Map values to option letters A, B, C, D
            opt_letters = ["A", "B", "C", "D"]
            opt_dict = {opt_letters[i]: shuffled_opts[i] for i in range(4)}
            correct_letter = [k for k, v in opt_dict.items() if v == local_q["answer"]][0]

            generated_list.append({
                "id": idx,
                "prize": PRIZE_LADDER[idx-1]["prize"],
                "question": local_q["question"],
                "options": opt_dict,
                "answer": correct_letter
            })
            continue

        # Try up to 3 times to hit the external API for variety
        for _ in range(3):
            cat = random.choice(categories)
            try:
                url = f"https://opentdb.com/api.php?amount=1&category={cat}&difficulty={difficulty}&type=multiple"
                response = requests.get(url, timeout=4).json()
                
                if response.get("response_code") == 0 and response.get("results"):
                    data = response["results"][0]
                    
                    # Clean escaped HTML codes coming out of OpenTDB
                    question_text = html.unescape(data["question"])
                    correct_ans = html.unescape(data["correct_answer"])
                    wrong_ans = [html.unescape(x) for x in data["incorrect_answers"]]
                    
                    all_opts = wrong_ans + [correct_ans]
                    random.shuffle(all_opts)
                    
                    opt_letters = ["A", "B", "C", "D"]
                    opt_dict = {opt_letters[i]: all_opts[i] for i in range(4)}
                    correct_letter = [k for k, v in opt_dict.items() if v == correct_ans][0]
                    
                    generated_list.append({
                        "id": idx,
                        "prize": PRIZE_LADDER[idx-1]["prize"],
                        "question": question_text,
                        "options": opt_dict,
                        "answer": correct_letter
                    })
                    question_added = True
                    break
            except Exception:
                continue # Fall through to fallback loop if network drops
                
        # Hard fallback local placeholder system to make sure the server NEVER crashes 
        if not question_added:
            fallback_pool = CODING_QUESTIONS if CODING_QUESTIONS else [{"question": "Placeholder Quiz item?", "options": ["A","B","C","D"], "answer": "A"}]
            dummy = random.choice(fallback_pool)
            shuffled_opts = list(dummy["options"]) if "options" in dummy else ["True Choice", "False Option 1", "False Option 2", "False Option 3"]
            random.shuffle(shuffled_opts)
            
            opt_dict = {"A": shuffled_opts[0], "B": shuffled_opts[1], "C": shuffled_opts[2], "D": shuffled_opts[3]}
            ans_val = dummy.get("answer", shuffled_opts[0])
            correct_letter = next((k for k, v in opt_dict.items() if v == ans_val), "A")
            
            generated_list.append({
                "id": idx,
                "prize": PRIZE_LADDER[idx-1]["prize"],
                "question": dummy.get("question", f"Dynamic Coding Question Challenge #{idx}"),
                "options": opt_dict,
                "answer": correct_letter
            })
            
    return generated_list

def get_clean_client_question(q):
    """Filters out answer fields securely before sharing data with UI client."""
    return {
        "id": q["id"],
        "prize": q["prize"],
        "question": q["question"],
        "options": q["options"],
    }


# ─── Updated API Endpoints ─────────────────────────────────────────────────

@app.route("/api/start", methods=["GET"])
def start_game():
    """Generates a fresh completely unique random 15-question array pool for this session."""
    # Generate random question layout list for this current runtime run
    fresh_session_questions = fetch_dynamic_questions()
    
    # Store globally referencing user tracking key session index identifier token logic
    # Using a simple single-session pattern. (Resets every time /api/start runs)
    GAME_SESSIONS["current_game"] = fresh_session_questions

    return jsonify({
        "total_questions": TOTAL_QUESTIONS,
        "safe_milestones": SAFE_MILESTONES,
        "prize_ladder": PRIZE_LADDER,
        "lifelines": ["fifty_fifty", "phone_a_friend", "audience_poll"],
    })


@app.route("/api/question/<int:q_id>", methods=["GET"])
def get_question(q_id):
    """Fetches specific target indexed entry tracking data from current session matrix storage."""
    questions = GAME_SESSIONS.get("current_game")
    if not questions:
        return jsonify({"error": "No active session. Please start game first."}), 400
        
    q = next((x for x in questions if x["id"] == q_id), None)
    if not q:
        return jsonify({"error": "Question tracking index limit exceeded"}), 404
        
    return jsonify(get_clean_client_question(q))


@app.route("/api/answer", methods=["POST"])
def check_answer():
    """Evaluates client answer submission match records across dynamically compiled indexes."""
    questions = GAME_SESSIONS.get("current_game")
    if not questions:
        return jsonify({"error": "No game context database tracking array index map records found"}), 400

    data = request.get_json() or {}
    q_id = data.get("question_id")
    selected = str(data.get("selected", "")).upper().strip()

    q = next((x for x in questions if x["id"] == q_id), None)
    if not q:
        return jsonify({"error": "Invalid target question tracking key index parameters"}), 400

    correct = (selected == q["answer"])

    # Establish safety ladder fallback benchmarks
    safe_prize = "₹0"
    for milestone_id, prize in sorted(SAFE_MILESTONES.items(), reverse=True):
        if q_id > milestone_id:
            safe_prize = prize
            break

    next_id = q_id + 1 if (correct and q_id < TOTAL_QUESTIONS) else None

    return jsonify({
        "correct": correct,
        "correct_answer": q["answer"],
        "correct_option_text": q["options"][q["answer"]],
        "selected": selected,
        "prize_won": q["prize"] if correct else safe_prize,
        "is_final": (q_id == TOTAL_QUESTIONS and correct),
        "next_question_id": next_id,
    })


@app.route("/api/lifeline/fifty_fifty", methods=["POST"])
def fifty_fifty():
    questions = GAME_SESSIONS.get("current_game")
    if not questions: return jsonify({"error": "Session missing"}), 400

    data = request.get_json() or {}
    q_id = data.get("question_id")
    q = next((x for x in questions if x["id"] == q_id), None)
    
    if not q: return jsonify({"error": "Question target missing"}), 404

    correct = q["answer"]
    wrong_options = [k for k in q["options"].keys() if k != correct]
    to_remove = random.sample(wrong_options, 2)

    remaining = {k: v for k, v in q["options"].items() if k not in to_remove}
    return jsonify({"remaining_options": remaining, "removed": to_remove})


@app.route("/api/lifeline/audience_poll", methods=["POST"])
def audience_poll():
    questions = GAME_SESSIONS.get("current_game")
    if not questions: return jsonify({"error": "Session missing"}), 400

    data = request.get_json() or {}
    q_id = data.get("question_id")
    q = next((x for x in questions if x["id"] == q_id), None)
    
    if not q: return jsonify({"error": "Question not found"}), 404

    correct = q["answer"]
    options = list(q["options"].keys())

    correct_vote = random.randint(58, 82) # Dynamically weight audience to lean smart
    remaining = 100 - correct_vote
    others = [k for k in options if k != correct]

    split = sorted([random.randint(0, remaining) for _ in range(len(others) - 1)] + [remaining])
    parts = [split[0]] + [split[i] - split[i-1] for i in range(1, len(split))]

    votes = {opt: parts[i] for i, opt in enumerate(others)}
    votes[correct] = correct_vote

    return jsonify({"votes": votes})


@app.route("/api/lifeline/phone_a_friend", methods=["POST"])
def phone_a_friend():
    questions = GAME_SESSIONS.get("current_game")
    if not questions: return jsonify({"error": "Session missing"}), 400

    data = request.get_json() or {}
    q_id = data.get("question_id")
    q = next((x for x in questions if x["id"] == q_id), None)
    
    if not q: return jsonify({"error": "Question not found"}), 404

    correct = q["answer"]
    correct_text = q["options"][correct]

    confidence = random.choice(["absolutely certain", "90% confident", "pretty sure", "leaning heavily towards"])
    friend = random.choice(["Rahul", "Priya", "Amit", "Ananya", "Vikram"])

    message = f"{friend} says: 'Hey! I am {confidence} that the correct option is ({correct}) {correct_text}.'"
    return jsonify({"message": message, "friend": friend})


if __name__ == "__main__":
    print("🎬 Highly Dynamic KBC Server active on http://localhost:5000")
    app.run(debug=True, port=5000)
