"""
KBC - Kaun Banega Crorepati
Python Flask Backend
Run: pip install flask flask-cors
Then: python app.py
"""

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow frontend to call this API

# ─── Question Bank ──────────────────────────────────────────────────────────
QUESTIONS = [
    {
        "id": 1,
        "prize": "₹1,000",
        "question": "Who is the all-time top international goal scorer in football?",
        "options": {"A": "Lionel Messi", "B": "Cristiano Ronaldo", "C": "Neymar Jr.", "D": "Diego Maradona"},
        "answer": "B",
        "lifelines_used": []
    },
    {
        "id": 2,
        "prize": "₹2,000",
        "question": "Which team won the IPL Championship title in 2025?",
        "options": {"A": "Kolkata Knight Riders", "B": "Mumbai Indians", "C": "Royal Challengers Bengaluru", "D": "Chennai Super Kings"},
        "answer": "C",
        "lifelines_used": []
    },
    {
        "id": 3,
        "prize": "₹3,000",
        "question": "Which biriyani restaurant in Kolkata is popularly known as 'Dada Boudi'?",
        "options": {"A": "Arsalan", "B": "Aminia", "C": "D Bapi's", "D": "Dada Boudi Hotel"},
        "answer": "D",
        "lifelines_used": []
    },
    {
        "id": 4,
        "prize": "₹5,000",
        "question": "Which programming language is consistently ranked #1 by the TIOBE Index?",
        "options": {"A": "C", "B": "C++", "C": "Python", "D": "Java"},
        "answer": "C",
        "lifelines_used": []
    },
    {
        "id": 5,
        "prize": "₹10,000",
        "question": "Complete the famous Bengali tongue-twister: 'Ma ka ladle meow...'?",
        "options": {"A": "GOP GOP", "B": "GOP GOP GOP", "C": "GOK GOK", "D": "GUP GUP"},
        "answer": "B",
        "lifelines_used": []
    },
    {
        "id": 6,
        "prize": "₹20,000",
        "question": "What is the capital city of West Bengal?",
        "options": {"A": "Howrah", "B": "Durgapur", "C": "Kolkata", "D": "Siliguri"},
        "answer": "C",
        "lifelines_used": []
    },
    {
        "id": 7,
        "prize": "₹40,000",
        "question": "Which Indian cricketer is known as 'The Wall'?",
        "options": {"A": "Sourav Ganguly", "B": "Rahul Dravid", "C": "Sachin Tendulkar", "D": "VVS Laxman"},
        "answer": "B",
        "lifelines_used": []
    },
    {
        "id": 8,
        "prize": "₹80,000",
        "question": "In which year did India gain independence?",
        "options": {"A": "1945", "B": "1946", "C": "1947", "D": "1948"},
        "answer": "C",
        "lifelines_used": []
    },
    {
        "id": 9,
        "prize": "₹1,60,000",
        "question": "Who wrote the Indian national anthem 'Jana Gana Mana'?",
        "options": {"A": "Bankim Chandra Chatterjee", "B": "Rabindranath Tagore", "C": "Subramanya Bharati", "D": "Sarojini Naidu"},
        "answer": "B",
        "lifelines_used": []
    },
    {
        "id": 10,
        "prize": "₹3,20,000",
        "question": "Which planet in our solar system has the most moons?",
        "options": {"A": "Jupiter", "B": "Saturn", "C": "Uranus", "D": "Neptune"},
        "answer": "B",
        "lifelines_used": []
    },
    {
        "id": 11,
        "prize": "₹6,40,000",
        "question": "What is the largest organ in the human body?",
        "options": {"A": "Liver", "B": "Brain", "C": "Skin", "D": "Intestine"},
        "answer": "C",
        "lifelines_used": []
    },
    {
        "id": 12,
        "prize": "₹12,50,000",
        "question": "Who invented the World Wide Web (WWW)?",
        "options": {"A": "Bill Gates", "B": "Steve Jobs", "C": "Linus Torvalds", "D": "Tim Berners-Lee"},
        "answer": "D",
        "lifelines_used": []
    },
    {
        "id": 13,
        "prize": "₹25,00,000",
        "question": "Which element has the chemical symbol 'Au'?",
        "options": {"A": "Silver", "B": "Gold", "C": "Copper", "D": "Aluminium"},
        "answer": "B",
        "lifelines_used": []
    },
    {
        "id": 14,
        "prize": "₹50,00,000",
        "question": "What is the speed of light in vacuum (approximately)?",
        "options": {"A": "3 × 10⁸ m/s", "B": "3 × 10⁶ m/s", "C": "3 × 10¹⁰ m/s", "D": "3 × 10⁴ m/s"},
        "answer": "A",
        "lifelines_used": []
    },
    {
        "id": 15,
        "prize": "₹1,00,00,000",
        "question": "Which mathematician is known as the 'Prince of Mathematics'?",
        "options": {"A": "Isaac Newton", "B": "Leonhard Euler", "C": "Carl Friedrich Gauss", "D": "Blaise Pascal"},
        "answer": "C",
        "lifelines_used": []
    },
]

# Safe milestones — money kept on wrong answer
SAFE_MILESTONES = {5: "₹10,000", 10: "₹3,20,000", 15: "₹1,00,00,000"}

# ─── Helper ─────────────────────────────────────────────────────────────────
def get_question_data(q):
    """Return question dict without the answer (for client)."""
    return {
        "id": q["id"],
        "prize": q["prize"],
        "question": q["question"],
        "options": q["options"],
    }


# ─── Routes ─────────────────────────────────────────────────────────────────

@app.route("/api/start", methods=["GET"])
def start_game():
    """Return all questions (without answers) and game metadata."""
    return jsonify({
        "total_questions": len(QUESTIONS),
        "safe_milestones": SAFE_MILESTONES,
        "prize_ladder": [{"id": q["id"], "prize": q["prize"]} for q in QUESTIONS],
        "lifelines": ["fifty_fifty", "phone_a_friend", "audience_poll"],
    })


@app.route("/api/question/<int:q_id>", methods=["GET"])
def get_question(q_id):
    """Return a specific question by ID (1-indexed)."""
    q = next((x for x in QUESTIONS if x["id"] == q_id), None)
    if not q:
        return jsonify({"error": "Question not found"}), 404
    return jsonify(get_question_data(q))


@app.route("/api/answer", methods=["POST"])
def check_answer():
    """
    POST body: { "question_id": 1, "selected": "B" }
    Returns: correct/wrong, correct_answer, prize_won, safe_prize, next_question_id
    """
    data = request.get_json()
    q_id = data.get("question_id")
    selected = data.get("selected", "").upper().strip()

    q = next((x for x in QUESTIONS if x["id"] == q_id), None)
    if not q:
        return jsonify({"error": "Invalid question ID"}), 400

    correct = selected == q["answer"]

    # Determine safe money if wrong
    safe_prize = "₹0"
    for milestone_id, prize in sorted(SAFE_MILESTONES.items(), reverse=True):
        if q_id > milestone_id:
            safe_prize = prize
            break

    next_id = q_id + 1 if correct and q_id < len(QUESTIONS) else None

    return jsonify({
        "correct": correct,
        "correct_answer": q["answer"],
        "correct_option_text": q["options"][q["answer"]],
        "selected": selected,
        "prize_won": q["prize"] if correct else safe_prize,
        "is_final": q_id == len(QUESTIONS) and correct,
        "next_question_id": next_id,
    })


@app.route("/api/lifeline/fifty_fifty", methods=["POST"])
def fifty_fifty():
    """
    POST body: { "question_id": 1 }
    Removes 2 wrong answers, returns remaining 2 options.
    """
    data = request.get_json()
    q_id = data.get("question_id")

    q = next((x for x in QUESTIONS if x["id"] == q_id), None)
    if not q:
        return jsonify({"error": "Question not found"}), 404

    correct = q["answer"]
    wrong_options = [k for k in q["options"] if k != correct]

    import random
    to_remove = random.sample(wrong_options, 2)

    remaining = {k: v for k, v in q["options"].items() if k not in to_remove}
    return jsonify({"remaining_options": remaining, "removed": to_remove})


@app.route("/api/lifeline/audience_poll", methods=["POST"])
def audience_poll():
    """
    POST body: { "question_id": 1 }
    Returns simulated audience vote percentages.
    """
    import random

    data = request.get_json()
    q_id = data.get("question_id")

    q = next((x for x in QUESTIONS if x["id"] == q_id), None)
    if not q:
        return jsonify({"error": "Question not found"}), 404

    correct = q["answer"]
    options = list(q["options"].keys())

    # Simulate: correct answer gets majority vote with some noise
    correct_vote = random.randint(50, 75)
    remaining = 100 - correct_vote
    others = [k for k in options if k != correct]

    split = sorted([random.randint(0, remaining) for _ in range(len(others) - 1)] + [remaining])
    parts = [split[0]] + [split[i] - split[i-1] for i in range(1, len(split))]

    votes = {}
    for i, opt in enumerate(others):
        votes[opt] = parts[i]
    votes[correct] = correct_vote

    return jsonify({"votes": votes})


@app.route("/api/lifeline/phone_a_friend", methods=["POST"])
def phone_a_friend():
    """
    POST body: { "question_id": 1 }
    Returns a simulated friend hint message.
    """
    import random

    data = request.get_json()
    q_id = data.get("question_id")

    q = next((x for x in QUESTIONS if x["id"] == q_id), None)
    if not q:
        return jsonify({"error": "Question not found"}), 404

    correct = q["answer"]
    correct_text = q["options"][correct]

    confidence = random.choice(["pretty sure", "almost certain", "quite confident", "not 100% sure but think"])
    friends = ["Rahul", "Priya", "Amit", "Sunita", "Vikram"]
    friend = random.choice(friends)

    message = (
        f"{friend} says: 'Yaar, I'm {confidence} the answer is "
        f"({correct}) {correct_text}. You should go with it!'"
    )

    return jsonify({"message": message, "friend": friend})


# ─── Entry Point ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🎬 KBC Server starting on http://localhost:5000")
    app.run(debug=True, port=5000)
