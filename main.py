import streamlit as st
import pandas as pd
import random
import re
import urllib.parse
import base64
import requests

# ==================================================
# 1. 基本設定
# ==================================================
st.set_page_config(
    page_title="文系科目は、ゆずれない",
    page_icon="🚀",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ==================================================
# 2. CSS（デザイン・レイアウト）
# ==================================================
st.markdown("""
<style>
.stApp { background:#f7f8fc; }
.block-container { max-width:720px; padding-top: 4rem !important; } 
.main-title { text-align:center; font-size:1.8rem; font-weight:900; margin-bottom:0.2rem; }
.sub-title { text-align:center; color:#666; font-size:0.85rem; margin-bottom:1.5rem; }

/* 問題カード */
.card { background:white; padding:22px; border-radius:18px; box-shadow:0 8px 20px rgba(0,0,0,0.06); margin-bottom:1rem; line-height:1.7; font-size:1.05rem; color:#111; }
.orange-card { border-left: 8px solid #ff9800; } 
.pink-card   { border-left: 8px solid #e91e63; }
.violet-card { border-left: 8px solid #9c27b0; }
.cyan-card   { border-left: 8px solid #00bcd4; }

/* 解説カード */
.exp-card { background: #fff9db; padding: 18px; border-radius: 14px; border: 1px dashed #fab005; margin-top: 10px; font-size: 0.95rem; color: #333; }

/* ボタンデザイン */
.stButton button { width: 100%; border-radius: 16px; font-size: 1.1rem; font-weight: 800; min-height: 55px; transition: 0.2s; }
.tango-btn button { background-color: #fff4e6 !important; color: #ff9800 !important; border: 2px solid #ff9800 !important; }
.nihonshi-btn button { background-color: #fce4ec !important; color: #e91e63 !important; border: 2px solid #e91e63 !important; }
.shiryo-btn button { background-color: #f3e5f5 !important; color: #9c27b0 !important; border: 2px solid #9c27b0 !important; }
.sekaishi-btn button { background-color: #e3f9fb !important; color: #00bcd4 !important; border: 2px solid #00bcd4 !important; }

/* 正誤問題用の特殊ボタン（⭕️/❌） */
button:has(div:contains("⭕️")) { background-color: #e7f3ff !important; color: #1877f2 !important; border: 2px solid #1877f2 !important; }
button:has(div:contains("❌")) { background-color: #fff5f5 !important; color: #ff4b4b !important; border: 2px solid #ff4b4b !important; }

.guide-text { color: #222222 !important; font-size: 0.88rem; font-weight: 600; margin-bottom: 0.4rem; }

/* === かわいい再生ボタンのスタイル（復元・強化） === */
.audio-container {
    background-color: #f8f9fa;
    border-radius: 15px;
    padding: 10px;
    margin-top: 10px;
    display: flex;
    align-items: center;
    border: 1px solid #ddd;
}
.audio-text {
    font-size: 0.85rem;
    color: #ff9800;
    font-weight: bold;
    margin-right: auto;
    padding-left: 5px;
}
audio::-webkit-media-controls-panel {
    background-color: #fff4e6;
}
audio::-webkit-media-controls-play-button {
    background-color: #ff9800;
    border-radius: 50%;
    transition: 0.2s;
}
audio::-webkit-media-controls-play-button:hover {
    background-color: #e68a00;
}
audio::-webkit-media-controls-current-time-display,
audio::-webkit-media-controls-time-remaining-display {
    color: #333;
}
</style>
""", unsafe_allow_html=True)

# 音声生成関数（かわいいデザインを埋め込み）
def play_voice(text, label="音声を聞く"):
    try:
        q = urllib.parse.quote(text)
        # client=tw-ob は client=t よりも安定する場合があります
        url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={q}&tl=en&client=tw-ob"
        res = requests.get(url, timeout=5) # タイムアウトを設定
        if res.status_code == 200:
            b64 = base64.b64encode(res.content).decode()
            # かわいいスタイルを適用したHTML
            md = f'''
                <div class="audio-container">
                    <span class="audio-text">🎧 {label}</span>
                    <audio src="data:audio/mp3;base64,{b64}" controls autoplay style="height: 35px;"></audio>
                </div>
            '''
            st.markdown(md, unsafe_allow_html=True)
        else:
            st.error("音声データの取得に失敗しました。")
    except Exception as e:
        st.error(f"音声再生エラー: {e}")

def reset_quiz_engine():
    keys = ["df", "idx", "answered", "choices", "correct", "selected", "user_choice", "quiz_filter", "quiz_subject", "study_mode"]
    for k in keys:
        if k in st.session_state: del st.session_state[k]

def clean_text(t):
    # 音声比較用なので、記号も消す
    return re.sub(r'[「」『』・=＝\s　.,?!-]', '', str(t))

# ==================================================
# 3. メイン画面
# ==================================================
st.markdown('<div class="main-title">🚀 文系科目は、ゆずれない</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">英語・地歴 統合学習ツール</div>', unsafe_allow_html=True)

subject = st.selectbox("学習する科目を選択", [
    "選択してください", "システム英単語", "暗唱例文集",
    "日本史一問一答", "日本史正誤問題攻略", "日本史史料問題攻略", "世界史一問一答"
])

if subject == "選択してください": st.stop()

# ==================================================
# 4. データ読み込み
# ==================================================
@st.cache_data
def load_csv(name):
    files = {
        "システム英単語":"final_tango_list.csv", "暗唱例文集":"english_sent.csv",
        "日本史一問一答":"jhcheck.csv", "日本史正誤問題攻略":"seigo_check.csv", 
        "日本史史料問題攻略":"shiryo_check.csv", "世界史一問一答":"whcheck.csv"
    }
    try:
        # UTF-8 (BOM付き) 対応
        return pd.read_csv(files[name], encoding="utf-8-sig").dropna(how='all')
    except:
        return pd.DataFrame()

raw_df = load_csv(subject)
if raw_df.empty:
    st.warning(f"データファイル ({subject}) が読み込めません。")
    st.stop()

# ==================================================
# 5. サイドバー・フィルタリング（タイトル維持）
# ==================================================
current_filter = "All"
nihonshi_titles = {
    "第1章": "歴史のはじまり", "第2章": "飛鳥時代", "第3章": "奈良時代", "第4章": "平安時代",
    "第5章": "院政と武士の躍進", "第6章": "武家政権の成立", "第7章": "武家社会の成長", 
    "第8章": "近世の幕開け", "第9章": "幕藩体制の成立と展開", "第10章": "幕藩体制の動揺",
    "第11章": "近世から近代へ", "第12章": "近代国家の成立", "第13章": "近代国家の展開", "第14章": "近代の産業と生活"
}

if subject == "システム英単語":
    level_map = {"All":"All", "Fundamental(1-600)":"Fundamental", "Essential(601-1200)":"Essential", "Advanced(1201-1700)":"Advanced", "Final(1701-2027)":"Final"}
    sel_level = st.sidebar.radio("レベル選択", list(level_map.keys()))
    current_filter = level_map[sel_level]
    df = raw_df if current_filter == "All" else raw_df[raw_df["level"].astype(str).str.contains(current_filter, na=False)]
elif "chapter" in raw_df.columns:
    raw_chaps = sorted([str(x).strip() for x in raw_df["chapter"].dropna().unique().tolist()], key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 999)
    if "日本史" in subject:
        options = ["すべてを表示"] + [f"{c} {nihonshi_titles.get(c, '')}".strip() for c in raw_chaps]
    else:
        options = ["すべてを表示"] + raw_chaps
    sel_range = st.sidebar.radio("範囲を選択", options)
    # 章番号だけを抽出
    current_filter = sel_range.split(" ")[0] if sel_range != "すべてを表示" else "すべて"
    df = raw_df if current_filter == "すべて" else raw_df[raw_df["chapter"].astype(str).str.strip() == current_filter]
elif subject == "世界史一問一答" and "area" in raw_df.columns:
    areas = sorted([str(x).strip() for x in raw_df["area"].dropna().unique().tolist()])
    sel_area = st.sidebar.radio("地域を選択", ["すべてを表示"] + areas)
    current_filter = sel_area
    df = raw_df if sel_area == "すべてを表示" else raw_df[raw_df["area"].astype(str).str.strip() == sel_area]
else:
    df = raw_df

# --- エンジン制御 ---
if st.session_state.get("quiz_subject") != subject or st.session_state.get("quiz_filter") != current_filter:
    reset_quiz_engine()
    st.session_state.quiz_subject, st.session_state.quiz_filter = subject, current_filter
    # ランダムに並べ替え
    st.session_state.df = df.sample(frac=1).reset_index(drop=True) if not df.empty else pd.DataFrame()
    st.session_state.idx, st.session_state.answered = 0, False
    st.session_state.study_mode = "全文暗唱"

active_df = st.session_state.get("df", pd.DataFrame())
idx = st.session_state.get("idx", 0)

if active_df.empty:
    st.info("対象の問題が見つかりません。範囲を変更してください。")
    st.stop()
if idx >= len(active_df):
    st.balloons(); st.success("全問終了！"); st.button("もう一度最初から", on_click=reset_quiz_engine); st.stop()

row = active_df.iloc[idx]
st.progress((idx + 1) / len(active_df))

# ==================================================
# 7. クイズUI
# ==================================================

# --- 暗唱例文集 ---
if subject == "暗唱例文集":
    c_m1, c_m2 = st.columns(2)
    with c_m1:
        if st.button("🔴 全文暗唱"): st.session_state.study_mode = "全文暗唱"; st.rerun()
    with c_m2:
        if st.button("🔵 ヒントはここ"): st.session_state.study_mode = "空欄補充"; st.rerun()

    # 太字部分を [ ____ ] に
    disp = re.sub(r'\*\*(.*?)\*\*', "[ ____ ]", str(row["English"])) if st.session_state.study_mode == "空欄補充" else "（英文を思い出してください）"
    st.markdown(f'<div class="card orange-card">【日本語】<br><b>{row["japanese"]}</b><hr>【英文】<br>{disp}</div>', unsafe_allow_html=True)

    if not st.session_state.answered:
        if st.button("答えを確認する"): st.session_state.answered = True; st.rerun()
    else:
        # 太字部分をピンク色に
        ans_highlight = re.sub(r'\*\*(.*?)\*\*', r'<span style="color:#e91e63; font-weight:800; border-bottom:2px solid;">\1</span>', str(row["English"]))
        st.markdown(f'<div class="exp-card">【正解】<br><span style="font-size:1.3rem; font-family:serif;">{ans_highlight}</span></div>', unsafe_allow_html=True)
        # 音声再生（かわいいボタン）
        play_voice(str(row["English"]).replace("**", ""), "例文を聞く")
        st.write("---")
        c1, c2 = st.columns(2)
        if c1.button("✅ 次へ"): st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
        if c2.button("🔄 もう一度"): st.session_state.answered = False; st.rerun()

# --- システム英単語 ---
elif subject == "システム英単語":
    word = str(row["question"])
    # 例文中の英単語を強調
    sent = re.sub(re.escape(word), f"<span style='color:#ff9800;font-weight:bold'>{word}</span>", str(row["sentence"]), flags=re.IGNORECASE)
    st.markdown(f'<div class="card orange-card">{sent}</div>', unsafe_allow_html=True)
    if "choices" not in st.session_state:
        ans_list = [x.strip() for x in re.split(r'[,、;]', str(row["all_answers"]))]
        correct = ans_list[0]
        dummies = [x.strip() for x in re.split(r'[,、;]', str(row["dummy_pool"])) if x.strip() != correct]
        # ダミーが足りない場合の補償（シス単データ依存）
        if len(dummies) < 3: dummies = dummies + ["(ダミーなし)"] * (3 - len(dummies))
        st.session_state.choices = random.sample([correct] + random.sample(dummies, 3), 4)
        random.shuffle(st.session_state.choices)
        st.session_state.correct = correct

    st.markdown('<div class="tango-btn">', unsafe_allow_html=True)
    cols = st.columns(2)
    for i, val in enumerate(st.session_state.choices):
        if cols[i%2].button(val, key=f"t_{i}", disabled=st.session_state.answered):
            st.session_state.selected, st.session_state.answered = val, True; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.answered:
        if st.session_state.selected == st.session_state.correct: st.success("正解！")
        else: st.error(f"不正解... 正解：{st.session_state.correct}")
        st.info(f"意味：{row['all_answers']}\n訳：{row['translation']}")
        # 解答表示後に音声を生成（かわいいボタン）
        play_voice(str(row["question"]), "単語を聞く")
        st.write("---")
        c1, c2 = st.columns(2)
        if c1.button("✅ 次へ"): 
            if "choices" in st.session_state: del st.session_state.choices
            st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
        if c2.button("🔄 もう一度"): st.session_state.answered = False; st.rerun()

# --- 日本史正誤問題 ---
elif subject == "日本史正誤問題攻略":
    st.markdown(f'<div class="card pink-card"><b>{row["question"]}</b></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    ans = str(row["answer"]).strip()
    if c1.button("⭕️ 正しい", disabled=st.session_state.answered): st.session_state.user_choice, st.session_state.answered = "◯", True; st.rerun()
    if c2.button("❌ 誤り", disabled=st.session_state.answered): st.session_state.user_choice, st.session_state.answered = "×", True; st.rerun()
    if st.session_state.answered:
        if st.session_state.user_choice == ans: st.success("正解！")
        else: st.error(f"不正解... 正解は【 {ans} 】")
        if pd.notna(row.get("explanation")): st.markdown(f'<div class="exp-card"><b>解説：</b><br>{row["explanation"]}</div>', unsafe_allow_html=True)
        st.write("---")
        c1, c2 = st.columns(2)
        if c1.button("✅ 次へ"): st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
        if c2.button("🔄 もう一度"): st.session_state.answered = False; st.rerun()

# --- 日本史史料問題 ---
elif subject == "日本史史料問題攻略":
    st.markdown(f'<div class="card violet-card"><b>【史料文】</b><br>{row["question"]}</div>', unsafe_allow_html=True)
    ans_raw = str(row["answer"])
    correct_list = [a.strip() for a in ans_raw.split("/") if a.strip()]
    user_inputs = []
    cols = st.columns(min(len(correct_list), 3)) # 最大3列
    for i, corr in enumerate(correct_list):
        user_inputs.append(cols[i % len(cols)].text_input(f"空欄 {chr(65+i)}", key=f"s_{idx}_{i}"))
    if st.button("解答する", disabled=st.session_state.answered): st.session_state.answered = True; st.rerun()
    if st.session_state.answered:
        all_ok = True
        for i, (u, c) in enumerate(zip(user_inputs, correct_list)):
            if clean_text(u) == clean_text(c): st.success(f"{chr(65+i)}: 正解! ({c})")
            else: st.error(f"{chr(65+i)}: 不正解. 正解: {c}"); all_ok = False
        if pd.notna(row.get("explanation")): st.markdown(f'<div class="exp-card"><b>出典・ポイント：</b><br>{row["explanation"]}</div>', unsafe_allow_html=True)
        st.write("---")
        c1, c2 = st.columns(2)
        if c1.button("✅ 次へ"): st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
        if c2.button("🔄 もう一度"): st.session_state.answered = False; st.rerun()

# --- その他（一問一答・世界史） ---
else:
    card_c = "pink-card" if "日本史" in subject else "cyan-card"
    st.markdown(f'<div class="card {card_c}"><b>{row["question"]}</b></div>', unsafe_allow_html=True)
    u_in = st.text_input("答えを入力", key=f"in_{idx}")
    if st.button("解答する", disabled=st.session_state.answered): st.session_state.answered = True; st.rerun()
    if st.session_state.answered:
        ans_raw = str(row["answer"])
        # 表記ゆれを考慮して判定
        if clean_text(u_in) in [clean_text(a) for a in ans_raw.split("/")]: st.success(f"正解！ ({ans_raw})")
        else: st.error(f"不正解... 正解：{ans_raw}")
        if pd.notna(row.get("explanation")): st.markdown(f'<div class="exp-card"><b>解説：</b><br>{row["explanation"]}</div>', unsafe_allow_html=True)
        st.write("---")
        c1, c2 = st.columns(2)
        if c1.button("✅ 次へ"): st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
        if c2.button("🔄 もう一度"): st.session_state.answered = False; st.rerun()
