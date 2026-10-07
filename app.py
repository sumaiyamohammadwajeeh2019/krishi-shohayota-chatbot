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

# ===== FERTILIZER DB (BD market). fraction = elemental nutrient =====
FERTS = {
 "urea": {"bn": "ইউরিয়া", "nut": {"N": 0.46}, "price": 22},
 "tsp": {"bn": "টিএসপি", "nut": {"P": 0.201}, "price": 22},
 "dap": {"bn": "ডিএপি", "nut": {"N": 0.18, "P": 0.201}, "price": 21},
 "mop": {"bn": "এমওপি/পটাশ", "nut": {"K": 0.498}, "price": 15},
 "sop": {"bn": "এসওপি", "nut": {"K": 0.415, "S": 0.18}, "price": 90},
 "gypsum": {"bn": "জিপসাম", "nut": {"S": 0.18, "Ca": 0.23}, "price": 12},
 "amsul": {"bn": "অ্যামোনিয়াম সালফেট", "nut": {"N": 0.21, "S": 0.24}, "price": 35},
 "znmono": {"bn": "জিংক মনো ৩৬%", "nut": {"Zn": 0.36}, "price": 180},
 "znhepta": {"bn": "জিংক হেপ্টা ২১%", "nut": {"Zn": 0.21}, "price": 140},
 "boric": {"bn": "বোরিক এসিড ১৭%", "nut": {"B": 0.17}, "price": 350},
 "borax": {"bn": "বোরাক্স ১১%", "nut": {"B": 0.11}, "price": 250},
 "epsom": {"bn": "এপসম সল্ট", "nut": {"Mg": 0.098, "S": 0.13}, "price": 80},
 "dolomite": {"bn": "ডলোমাইট", "nut": {"Ca": 0.21, "Mg": 0.12}, "price": 15},
}
MICRO_INFO = [
 {"n": "আয়রন (Fe)", "f": "ফেরাস সালফেট", "d": "১০ লি পানিতে ৫০-৮০ গ্রাম", "s": "কচি পাতা সাদা, শিরা সবুজ"},
 {"n": "ম্যাঙ্গানিজ (Mn)", "f": "ম্যাঙ্গানিজ সালফেট", "d": "১০ লিটারে ৩০-৫০ গ্রাম স্প্রে", "s": "পাতায় হলুদ ছিট দাগ"},
 {"n": "কপার (Cu)", "f": "তুঁতে/কপার সালফেট", "d": "১০ লিটারে ২০-৩০ গ্রাম", "s": "আগা মরা"},
 {"n": "মলিবডেনাম (Mo)", "f": "সোডিয়াম মলিবডেট", "d": "১০ লিটারে ৫-১০ গ্রাম", "s": "ফুলকপির সরু পাতা"},
 {"n": "ক্যালসিয়াম (Ca)", "f": "জিপসাম/ডলোচুন", "d": "মাটিতে জিপসাম; টমেটো পচনে ক্যালসিয়াম নাইট্রেট স্প্রে", "s": "টমেটোর গোড়া পচা"},
 {"n": "ম্যাগনেসিয়াম (Mg)", "f": "এপসম সল্ট", "d": "মাটিতে ২০-৪০ কেজি/হে বা স্প্রে ১০০ গ্রাম/১০ লি", "s": "পুরনো পাতা হলুদ"},
]

# Crop need kg/ha elemental (BARC FRG rounded, medium soil)
CROPS = {
 "boro": {"bn": "বোরো ধান", "N": 140, "P": 25, "K": 70, "S": 20, "Zn": 3.0, "B": 1.0, "Mg": 0, "Ca": 0, "tip": "ইউরিয়া ৩ কিস্তি: ১০-১৫, ২৫-৩০, ৪০-৪৫ দিনে।"},
 "aman": {"bn": "আমন ধান", "N": 90, "P": 15, "K": 45, "S": 12, "Zn": 2.0, "B": 0.5, "Mg": 0, "Ca": 0, "tip": "ইউরিয়া ৩ কিস্তিতে। জিংক শেষ চাষে।"},
 "wheat": {"bn": "গম", "N": 100, "P": 25, "K": 40, "S": 15, "Zn": 2.0, "B": 1.0, "Mg": 0, "Ca": 0, "tip": "ইউরিয়ার ২/৩ বপনে + ১/৩ শীষের আগে সেচে।"},
 "maize": {"bn": "ভুট্টা", "N": 160, "P": 35, "K": 70, "S": 20, "Zn": 4.0, "B": 1.5, "Mg": 0, "Ca": 0, "tip": "ইউরিয়া ৩ কিস্তি: বপনে, ৩০ দিনে, মোচার আগে।"},
 "potato": {"bn": "আলু", "N": 135, "P": 30, "K": 130, "S": 15, "Zn": 3.0, "B": 1.5, "Mg": 15, "Ca": 0, "tip": "সব সার শেষ চাষে মাটিতে।"},
 "mustard": {"bn": "সরিষা", "N": 60, "P": 18, "K": 35, "S": 25, "Zn": 2.0, "B": 1.5, "Mg": 0, "Ca": 0, "tip": "সরিষায় জিপসাম অবশ্যই — তেল বাড়ে।"},
 "lentil": {"bn": "ডাল (মসুর/মুগ)", "N": 20, "P": 20, "K": 30, "S": 12, "Zn": 1.5, "B": 1.0, "Mg": 0, "Ca": 0, "tip": "সব সার বপনের সময়।"},
 "brinjal": {"bn": "বেগুন", "N": 120, "P": 30, "K": 80, "S": 15, "Zn": 2.0, "B": 1.0, "Mg": 10, "Ca": 0, "tip": "ইউরিয়া+পটাশ ৩ কিস্তি।"},
 "tomato": {"bn": "টমেটো", "N": 110, "P": 35, "K": 100, "S": 15, "Zn": 2.5, "B": 1.5, "Mg": 10, "Ca": 10, "tip": "গোড়া পচনে জিপসাম + সেচ ঠিক রাখুন।"},
 "onion": {"bn": "পেঁয়াজ/রসুন", "N": 100, "P": 25, "K": 80, "S": 30, "Zn": 2.5, "B": 1.0, "Mg": 0, "Ca": 0, "tip": "সালফার বেশি লাগে। ইউরিয়া ২ কিস্তি।"},
 "chili": {"bn": "মরিচ", "N": 100, "P": 25, "K": 70, "S": 15, "Zn": 2.0, "B": 1.0, "Mg": 0, "Ca": 0, "tip": "বেশি ইউরিয়ায় রোগ বাড়ে।"},
 "jute": {"bn": "পাট", "N": 80, "P": 12, "K": 40, "S": 10, "Zn": 1.5, "B": 0.5, "Mg": 0, "Ca": 0, "tip": "ইউরিয়া ২ কিস্তি।"},
 "sugarcane": {"bn": "আখ", "N": 180, "P": 35, "K": 100, "S": 25, "Zn": 4.0, "B": 1.5, "Mg": 0, "Ca": 0, "tip": "ইউরিয়া ৩ কিস্তি। পটাশে চিনি বাড়ে।"},
 "cabbage": {"bn": "বাঁধা/ফুলকপি", "N": 150, "P": 30, "K": 100, "S": 20, "Zn": 2.0, "B": 2.0, "Mg": 10, "Ca": 0, "tip": "বোরন অবশ্যই — ফাঁপা কান্ড রোধে।"},
 "banana": {"bn": "কলা", "N": 150, "P": 30, "K": 180, "S": 15, "Zn": 2.0, "B": 1.5, "Mg": 20, "Ca": 0, "tip": "পটাশ বেশি লাগে। ৩-৪ কিস্তি।"},
}
LAND_HA = {"hectare": 1.0, "acre": 0.404686, "bigha": 0.1338, "decimal": 0.00404686, "katha": 0.006677, "sqft": 0.0000092903}
LAND_BN = {"hectare": "হেক্টর", "acre": "একর", "bigha": "বিঘা", "decimal": "শতক", "katha": "কাঠা", "sqft": "বর্গফুট"}

def calc_fert(need, ha, use_dap=False, zn_src="znmono", b_src="boric", k_src="mop"):
    rem = dict(need); out = {}
    def take(fkey, nutrient, rem_need):
        if rem_need <= 0: return 0.0
        frac = FERTS[fkey]["nut"][nutrient]
        amt = round(rem_need * ha / frac, 2)
        for n2, f2 in FERTS[fkey]["nut"].items():
            rem[n2] = rem.get(n2, 0) - amt / ha * f2
        out[fkey] = round(out.get(fkey, 0) + amt, 2)
        return amt
    if use_dap:
        take("dap", "P", rem.get("P", 0))
    else:
        take("tsp", "P", rem.get("P", 0))
    take(k_src if k_src in ("mop", "sop") else "mop", "K", rem.get("K", 0))
    take(zn_src if zn_src in ("znmono", "znhepta") else "znmono", "Zn", rem.get("Zn", 0))
    take(b_src if b_src in ("boric", "borax") else "boric", "B", rem.get("B", 0))
    mg_need = rem.get("Mg", 0)
    ca_need = rem.get("Ca", 0)
    if mg_need > 0 and ca_need > 0:
        take("dolomite", "Ca", ca_need)
        mg_need = rem.get("Mg", 0)
        if mg_need > 0: take("epsom", "Mg", mg_need)
    elif mg_need > 0:
        take("epsom", "Mg", mg_need)
    elif ca_need > 0:
        take("gypsum", "Ca", ca_need)
    s_rem = rem.get("S", 0)
    if s_rem > 0: take("gypsum", "S", s_rem)
    n_rem = rem.get("N", 0)
    if n_rem > 0:
        if FERTS.get(k_src, {}).get("nut", {}).get("S") and rem.get("S", 0) > 5:
            take("amsul", "N", min(n_rem, rem.get("S", 0) / 0.24 * 0.21))
            n_rem = rem.get("N", 0)
        if n_rem > 0: take("urea", "N", n_rem)
    total = sum(out.values())
    cost = sum(out[k] * FERTS[k]["price"] for k in out)
    rows = [{"key": k, "name": FERTS[k]["bn"], "kg": out[k], "cost": round(out[k] * FERTS[k]["price"])} for k in out if out[k] > 0]
    return {"items": rows, "total_kg": round(total, 2), "cost": round(cost)}

@app.route('/fert-data')
def fert_data():
    return jsonify({"crops": {k: {"bn": v["bn"], "tip": v.get("tip", "")} for k, v in CROPS.items()},
                    "ferts": {k: {"bn": v["bn"], "price": v["price"]} for k, v in FERTS.items()},
                    "lands": LAND_BN, "micro": MICRO_INFO})

@app.route('/fert-calc', methods=['POST'])
def fert_calc():
    try:
        d = request.get_json(force=True, silent=True) or {}
        crop = d.get("crop", "boro")
        unit = d.get("unit", "bigha")
        try: qty = float(d.get("qty", 1))
        except: qty = 1.0
        if qty <= 0 or qty > 100000: return jsonify({"error": "জমির পরিমাণ ভুল।"}), 400
        ha = qty * LAND_HA.get(unit, 0.1338)
        if crop == "custom":
            need = {}
            for n in ("N", "P", "K", "S", "Zn", "B", "Mg", "Ca"):
                try: need[n] = max(0.0, float(d.get(n, 0) or 0))
                except: need[n] = 0.0
            cname, tip = "কাস্টম ডোজ (kg/ha)", "মাটি পরীক্ষা অনুযায়ী।"
        else:
            c = CROPS.get(crop, CROPS["boro"])
            need = {n: float(c.get(n, 0) or 0) for n in ("N", "P", "K", "S", "Zn", "B", "Mg", "Ca")}
            cname, tip = c["bn"], c.get("tip", "")
        r = calc_fert(need, ha, d.get("use_dap", False), d.get("zn_src", "znmono"), d.get("b_src", "boric"), d.get("k_src", "mop"))
        r.update({"crop": cname, "tip": tip, "ha": round(ha, 4), "land": f"{qty} {LAND_BN.get(unit, unit)}", "need_ha": need})
        return jsonify(r)
    except Exception as e:
        print("FERT ERROR:", e)
        return jsonify({"error": "হিসাবে সমস্যা হয়েছে।"}), 500

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
    port = int(os.environ.get('PORT', 5000))
    print(f"Open in browser: http://127.0.0.1:{port}  (press Ctrl+C to stop)")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)


