import streamlit as st
import pandas as pd
import random
import re

# ==================================================
# 基本設定
# ==================================================
st.set_page_config(
    page_title="文系科目は、ゆずれない",
    page_icon="🚀",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ==================================================
# CSS（デザインの復元と微調整）
# ==================================================
st.markdown("""
<style>
.stApp { background:#f7f8fc; }
.block-container { max-width:720px; padding-top:2rem; } 
.main-title { text-align:center; font-size:2rem; font-weight:900; margin-bottom:0.2rem; }
.sub-title { text-align:center; color:#666; font-size:0.9rem; margin-bottom:1.5rem; }

/* カードデザイン */
.card { 
    background:white; padding:22px; border-radius:18px; 
    box-shadow:0 8px 20px rgba(0,0,0,0.06); margin-bottom:1rem; 
    line-height:1.7; font-size:1.05rem; color:#111; 
}
.exp-card {
    background: #fff9db; padding: 18px; border-radius: 14px; 
    border: 1px dashed #fab005; margin-top: 10px; font-size: 0.95rem; color: #444;
}
.pink-card { border-left: 8px solid #e91e63; }
.orange-card { border-left: 8px solid #ff9800; }
.cyan-card { border-left: 8px solid #00bcd4; }

/* ボタン共通設定 */
.stButton button {
    width: 100%; border-radius: 16px; font-size: 1.1rem; font-weight: 800;
    transition: all 0.2s ease; border: 2px solid transparent !important;
}

/* 日本史正誤問題（◯×）専用色 */
button:has(div:contains("⭕️")) {
    background-color: #e7f3ff !important; color: #1877f2 !important; border: 2px solid #1877f2 !important;
}
button:has(div:contains("❌")) {
    background-color: #fff5f5 !important; color: #ff4b4b !important; border: 2px solid #ff4b4b !important;
}

/* 英単語（オレンジ） */
.tango-btn button { background-color: #fff4e6 !important; color: #ff9800 !important; border: 2px solid #ff9800 !important; }
.tango-btn button:hover { background-color: #ff9800 !important; color: white !important; }

/* 日本史（ピンク） */
.nihonshi-btn button { background-color: #fce4ec !important; color: #e91e63 !important; border: 2px solid #e91e63 !important; }
.nihonshi-btn button:hover { background-color: #e91e63 !important; color: white !important; }

/* 世界史（シアン） */
.sekaishi-btn button { background-color: #e3f9fb !important; color: #00bcd4 !important; border: 2px solid #00bcd4 !important; }
.sekaishi-btn button:hover { background-color: #00bcd4 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# ==================================================
# 状態管理
# ==================================================
if "quiz_subject" not in st.session_state:
    st.session_state.quiz_subject = ""
if "quiz_filter" not in st.session_state:
    st.session_state.quiz_filter = ""

def clear_quiz_state():
    for key in ["df", "idx", "answered", "user_choice", "choices", "correct", "selected"]:
        if key in st.session_state: del st.session_state[key]

# ==================================================
# レイアウト：タイトル -> 科目選択
# ==================================================
st.markdown('<div class="main-title">🚀 文系科目は、ゆずれない</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">英語・地歴 統合学習ツール</div>', unsafe_allow_html=True)

subject = st.selectbox("学習する科目を選択", ["選択してください", "英単語", "日本史一問一答", "日本史正誤問題攻略", "世界史一問一答"])

if subject == "選択してください":
    st.info("科目を選択して学習を開始しましょう！")
    st.stop()

# ==================================================
# データ読み込みとフィルタリング
# ==================================================
@st.cache_data
def load_csv(name):
    files = {"英単語":"final_tango_list.csv", "日本史一問一答":"jhcheck.csv", "日本史正誤問題攻略":"seigo_check.csv", "世界史一問一答":"whcheck.csv"}
    return pd.read_csv(files[name], encoding="utf-8-sig").dropna(how='all')

raw_df = load_csv(subject)
current_filter = ""

# サイドバー設定
if subject == "英単語":
    st.sidebar.header("📏 レベル選択")
    menu = ["All", "Fundamental", "Essential", "Advanced", "Final"]
    current_filter = st.sidebar.radio("学習レベル", menu)
    df = raw_df if current_filter == "All" else raw_df[raw_df["level"].astype(str) == current_filter]

elif "chapter" in raw_df.columns:
    st.sidebar.header("🎯 範囲選択")
    # 数値順にソート（第10章が最後に来るように）
    raw_chaps = raw_df["chapter"].dropna().unique().tolist()
    sorted_chaps = sorted(raw_chaps, key=lambda x: int(re.search(r'\d+', str(x)).group()) if re.search(r'\d+', str(x)) else 999)
    
    titles = {"第1章": "日本文化のあけぼの", "第2章": "古墳とヤマト政権", "第3章": "律令国家の形成", "第4章": "貴族政治 of 展開"}
    options = ["すべてを表示"]
    for c in sorted_chaps:
        if subject == "日本史正誤問題攻略":
            options.append(f"{c} {titles.get(c, '')}".strip())
        else:
            options.append(str(c))
    
    sel = st.sidebar.radio("章を選択", options)
    current_filter = sel.split(" ")[0] if sel != "すべてを表示" else "すべて"
    df = raw_df if current_filter == "すべて" else raw_df[raw_df["chapter"].astype(str) == current_filter]
else:
    df = raw_df

# 初期化チェック
if st.session_state.quiz_subject != subject or st.session_state.quiz_filter != current_filter:
    clear_quiz_state()
    st.session_state.quiz_subject = subject
    st.session_state.quiz_filter = current_filter
    st.session_state.df = df.sample(frac=1).reset_index(drop=True)
    st.session_state.idx = 0
    st.session_state.answered = False

# ==================================================
# クイズ本体
# ==================================================
active_df = st.session_state.df
idx = st.session_state.idx

if idx >= len(active_df):
    st.balloons(); st.success("全問終了しました！")
    if st.button("もう一度解く"): clear_quiz_state(); st.rerun()
    st.stop()

row = active_df.iloc[idx]
st.progress((idx + 1) / len(active_df))
st.caption(f"{idx+1} / {len(active_df)} 問目 (範囲: {current_filter})")

# ボタン色用クラス
btn_class = "nihonshi-btn"
if subject == "英単語": btn_class = "tango-btn"
elif subject == "世界史一問一答": btn_class = "sekaishi-btn"

if subject == "日本史正誤問題攻略":
    q, ans = str(row["question"]), str(row["answer"]).strip()
    st.markdown(f'<div class="card pink-card"><b>{q}</b></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("⭕️ 正しい", key=f"o_{idx}", disabled=st.session_state.answered):
            st.session_state.user_choice, st.session_state.answered = "◯", True; st.rerun()
    with c2:
        if st.button("❌ 誤り", key=f"x_{idx}", disabled=st.session_state.answered):
            st.session_state.user_choice, st.session_state.answered = "×", True; st.rerun()
    if st.session_state.answered:
        if st.session_state.user_choice == ans: st.success("正解！")
        else: st.error(f"不正解... 正解は【 {ans} 】")
        if "explanation" in row and pd.notna(row["explanation"]):
            st.markdown(f'<div class="exp-card"><b>💡 解説:</b><br>{row["explanation"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
        if st.button("次の問題へ"): st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

elif "一問一答" in subject:
    q, ans_raw = str(row["question"]), str(row["answer"])
    st.markdown(f'<div class="card {"pink-card" if "日本史" in subject else "cyan-card"}"><b>{q}</b></div>', unsafe_allow_html=True)
    u_in = st.text_input("答えを入力", key=f"in_{idx}")
    st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
    if st.button("解答する", disabled=st.session_state.answered):
        st.session_state.answered = True; st.rerun()
    if st.session_state.answered:
        u_clean = u_in.replace(" ", "").replace("　", "")
        ok_ans = [a.strip().replace(" ", "").replace("　", "") for a in ans_raw.split("/")]
        if u_clean in ok_ans: st.success("正解！")
        else: st.error(f"不正解... 正解：{ans_raw}")
        if st.button("次の問題へ"): st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

else: # 英単語
    word = str(row["question"])
    sentence = re.sub(re.escape(word), f"<span style='color:#ff9800;font-weight:bold'>{word}</span>", str(row["sentence"]), flags=re.IGNORECASE)
    st.markdown(f'<div class="card orange-card">{sentence}</div>', unsafe_allow_html=True)
    if "choices" not in st.session_state:
        ans_list = [x.strip() for x in re.split(r'[,、;]', str(row["all_answers"])) if x.strip()]
        correct = ans_list[0] if ans_list else str(row["all_answers"]).strip()
        dummies = [x.strip() for x in re.split(r'[,、;]', str(row["dummy_pool"])) if x.strip() and x.strip() != correct]
        choices = [correct] + random.sample(dummies, min(3, len(dummies)))
        random.shuffle(choices)
        st.session_state.choices, st.session_state.correct = choices, correct
    
    st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    for i, c in enumerate(st.session_state.choices):
        with (c1 if i % 2 == 0 else c2):
            if st.button(c, key=f"btn_{i}", disabled=st.session_state.answered):
                st.session_state.selected, st.session_state.answered = c, True; st.rerun()
    if st.session_state.answered:
        if st.session_state.selected == st.session_state.correct: st.success("正解！")
        else: st.error(f"不正解... 正解：{st.session_state.correct}")
        st.info(f"意味：{row['all_answers']}\n訳：{row['translation']}")
        if st.button("次の問題へ進む"): st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
