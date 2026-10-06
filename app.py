from flask import Flask, render_template, request, jsonify
import json
import os
import difflib

base_dir = os.path.dirname(os.path.abspath(__file__))
knowledge_path = os.path.join(base_dir, 'knowledge.json')

def load_knowledge():
    try:
        with open(knowledge_path, encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list) and data:
                print(f"Loaded {len(data)} knowledge items")
                return data
    except Exception as e:
        print(f"knowledge.json load failed: {e}")
    return []

knowledge = load_knowledge()

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({"ok": True, "items": len(knowledge)})

def norm(s):
    return str(s or '').strip().lower()

@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.get_json(force=True, silent=True) or {}
        msg = norm(data.get('message', ''))
        division = norm(data.get('division', 'dhaka')) or 'dhaka'

        if not msg:
            return jsonify({"reply": "কিছু লিখুন, তারপর পাঠান।"})

        # 1) Direct substring match
        for item in knowledge:
            keywords = [norm(k) for k in item.get('keywords', []) if k]
            if any(k and (k in msg or msg in k) for k in keywords):
                answers = item.get('answers', {}) or {}
                if not answers and 'answer' in item:
                    return jsonify({"reply": item['answer']})
                reply = answers.get(division) or answers.get('dhaka')
                if reply:
                    return jsonify({"reply": reply})

        # 2) Token match: any word in message matches keyword (handles suffixes like লাউয়ে vs লাউ)
        words = msg.replace(',', ' ').replace('।', ' ').split()
        best, best_score = None, 0
        for item in knowledge:
            keywords = [norm(k) for k in item.get('keywords', []) if k]
            for kw in keywords:
                for w in words:
                    if not kw or not w:
                        continue
                    # stem-ish: match if one contains the other minus last char
                    if kw in w or w in kw:
                        score = len(kw)
                    else:
                        score = int(difflib.SequenceMatcher(None, kw, w).ratio() * 10)
                        if score < 8:  # threshold ~0.8
                            continue
                    if score > best_score:
                        best_score = score
                        best = item
        if best is not None:
            answers = best.get('answers', {}) or {}
            if not answers and 'answer' in best:
                return jsonify({"reply": best['answer']})
            reply = answers.get(division) or answers.get('dhaka')
            if reply:
                return jsonify({"reply": reply})

        # 3) Fallback per division — ALWAYS replies
        defaults = {
            "sylhet": "বুঝছি না বাই, আরেকবার কও চাই। যেমন 'ধানো পোকা'।",
            "dhaka": "দুঃখিত, বুঝতে পারিনি। 'ধান পোকা' লিখে দেখুন।",
            "chattogram": "ন বুঝিলাম, আরেকবার কও চাই।",
            "rajshahi": "বুঝতে পারলাম না। 'ধান পোকা' লিখে দেখো।",
            "khulna": "বুঝতি পারলাম না, আরেকবার কও।",
            "barishal": "বুঝতে পারি নাই মনু, আরেকবার কও।",
            "rangpur": "বুঝবার পালুং না বাহে, আরেকবার কন।",
            "mymensingh": "বুঝতে পারলাম না, আরেকবার কও।",
        }
        return jsonify({"reply": defaults.get(division, defaults['dhaka'])})
    except Exception as e:
        print("ASK ERROR:", e)
        return jsonify({"reply": "সার্ভারে সমস্যা হয়েছে, আবার চেষ্টা করুন।"}), 200

if __name__ == '__main__':
    print("Open in browser: http://127.0.0.1:5000  (press Ctrl+C to stop)")
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)


