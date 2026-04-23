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
# CSS（配置・科目別カラーの最終構成）
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
    box-shadow: 0 4px 10px rgba(0,0,0,0.08);
}

/* 日本史正誤問題（⭕️/❌）は全科目共通でこの色を優先 */
button:has(div:contains("⭕️")) {
    background-color: #e7f3ff !important; color: #1877f2 !important; border: 2px solid #1877f2 !important;
}
button:has(div:contains("❌")) {
    background-color: #fff5f5 !important; color: #ff4b4b !important; border: 2px solid #ff4b4b !important;
}

/* 科目別ボタン色（コンテナ経由で適用） */
.tango-area button { background-color: #fff4e6 !important; color: #ff9800 !important; border: 2px solid #ff9800 !important; }
.tango-area button:hover { background-color: #ff9800 !important; color: white !important; }

.nihonshi-area button { background-color: #fce4ec !important; color: #e91e63 !important; border: 2px solid #e91e63 !important; }
.nihonshi-area button:hover { background-color: #e91e63 !important; color: white !important; }

.sekaishi-area button { background-color: #e3f9fb !important; color: #00bcd4 !important; border: 2px solid #00bcd4 !important; }
.sekaishi-area button:hover { background-color: #00bcd4 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# ==================================================
# 1. 最上段タイトル
# ==================================================
st.markdown('<div class="main-title">🚀 文系科目は、ゆずれない</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">英語・地歴 統合学習ツール</div>', unsafe_allow_html=True)

# ==================================================
# 2. 科目選択機能（タイトルの直下）
# ==================================================
subject = st.selectbox("学習する科目を選択", ["選択してください", "英単語", "日本史一問一答", "日本史正誤問題攻略", "世界史一問一答"], index=0)

# ==================================================
# 状態管理・共通関数
# ==================================================
def clear_quiz_state():
    for key in ["quiz_subject", "quiz_filter", "df", "idx", "answered", "user_choice", "choices", "correct", "selected"]:
        if key in st.session_state: del st.session_state[key]

def start_quiz(df, subject, filter_val):
    st.session_state.quiz_subject = subject
    st.session_state.quiz_filter = filter_val
    st.session_state.df = df.sample(frac=1).reset_index(drop=True)
    st.session_state.idx = 0
    st.session_state.answered = False

def next_q():
    st.session_state.idx += 1
    st.session_state.answered = False
    for key in ["choices", "correct", "selected", "user_choice"]:
        if key in st.session_state: del st.session_state[key]

# ==================================================
# メイン処理
# ==================================================
if subject == "選択してください":
    st.info("科目を選択して学習を開始しましょう！")
    st.stop()

# CSV読み込み
@st.cache_data
def load_csv(subject_name):
    files = {
        "英単語": "final_tango_list.csv", 
        "日本史一問一答": "jhcheck.csv",
        "日本史正誤問題攻略": "seigo_check.csv",
        "世界史一問一答": "whcheck.csv" 
    }
    try:
        return pd.read_csv(files[subject_name], encoding="utf-8-sig").dropna(how='all')
    except:
        return None

raw_df = load_csv(subject)
if raw_df is None:
    st.error("CSVファイルが読み込めませんでした。ファイル名を確認してください。")
    st.stop()

# サイドバーによるフィルタリング
current_filter = "All"
if subject == "英単語":
    st.sidebar.header("📏 レベル選択")
    level_order = ["All", "Fundamental", "Essential", "Advanced", "Final"]
    # 実際にCSVに存在するレベルを特定
    available = raw_df["level"].unique().tolist()
    menu = [l for l in level_order if l == "All" or l in available]
    current_filter = st.sidebar.radio("学習レベルを選んでください", menu)
    df = raw_df if current_filter == "All" else raw_df[raw_df["level"].astype(str) == current_filter]

elif "chapter" in raw_df.columns:
    st.sidebar.header("🎯 範囲選択")
    chaps = sorted([str(x) for x in raw_df["chapter"].dropna().unique()])
    titles = {"第1章": "日本文化のあけぼの", "第2章": "古墳とヤマト政権", "第3章": "律令国家の形成", "第4章": "貴族政治の展開"}
    
    options = ["すべてを表示"]
    for c in chaps:
        options.append(f"{c} {titles.get(c, '')}".strip() if subject == "日本史正誤問題攻略" else c)
    
    sel = st.sidebar.radio("章を選択してください", options)
    current_filter = sel.split(" ")[0] if sel != "すべてを表示" else "すべて"
    df = raw_df if current_filter == "すべて" else raw_df[raw_df["chapter"].astype(str) == current_filter]
else:
    df = raw_df

# クイズ初期化判定
if ("quiz_subject" not in st.session_state or 
    st.session_state.quiz_subject != subject or 
    st.session_state.quiz_filter != current_filter):
    clear_quiz_state()
    start_quiz(df, subject, current_filter)

# 進捗表示
active_df = st.session_state.df
idx = st.session_state.idx

if idx >= len(active_df):
    st.balloons(); st.success("この範囲の全問をクリアしました！")
    if st.button("もう一度挑戦する"): clear_quiz_state(); st.rerun()
    st.stop()

row = active_df.iloc[idx]
st.progress((idx + 1) / len(active_df))
st.caption(f"{idx+1} / {len(active_df)} 問目 (範囲: {current_filter})")

# ボタン色エリアの開始
area_class = "nihonshi-area"
if subject == "英単語": area_class = "tango-area"
elif subject == "世界史一問一答": area_class = "sekaishi-area"

st.markdown(f'<div class="{area_class}">', unsafe_allow_html=True)

# ==================================================
# 3. クイズ表示
# ==================================================
if subject == "日本史正誤問題攻略":
    q, ans = str(row["question"]), str(row["answer"]).strip()
    st.info("📖 教科書本文をもとにした正誤問題です。")
    st.markdown(f'<div class="card pink-card"><b>{q}</b></div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⭕️ 正しい", key=f"o_{idx}", disabled=st.session_state.answered):
            st.session_state.user_choice, st.session_state.answered = "◯", True; st.rerun()
    with col2:
        if st.button("❌ 誤り", key=f"x_{idx}", disabled=st.session_state.answered):
            st.session_state.user_choice, st.session_state.answered = "×", True; st.rerun()
    if st.session_state.answered:
        if st.session_state.user_choice == ans: st.success("✨ 正解！")
        else: st.error(f"❌ 正解は【 {ans} 】")
        if "explanation" in row and pd.notna(row["explanation"]):
            st.markdown(f'<div class="exp-card"><b>💡 解説:</b><br>{row["explanation"]}</div>', unsafe_allow_html=True)
        if st.button("次の問題へ ➔"): next_q(); st.rerun()

elif subject in ["日本史一問一答", "世界史一問一答"]:
    q, ans_raw = str(row["question"]), str(row["answer"])
    st.markdown(f'<div class="card {"pink-card" if "日本史" in subject else "cyan-card"}"><b>{q}</b></div>', unsafe_allow_html=True)
    user_in = st.text_input("答えを入力してください", key=f"in_{idx}")
    if st.button("解答する", disabled=st.session_state.answered):
        st.session_state.answered = True; st.rerun()
    if st.session_state.answered:
        clean_in = user_in.replace(" ", "").replace("　", "")
        answers = [a.strip().replace(" ", "").replace("　", "") for a in ans_raw.split("/")]
        if clean_in in answers: st.success("✨ 正解！")
        else: st.error(f"❌ 正解：{ans_raw}")
        if "explanation" in row and pd.notna(row["explanation"]):
            st.markdown(f'<div class="exp-card"><b>💡 解説:</b><br>{row["explanation"]}</div>', unsafe_allow_html=True)
        if st.button("次の問題へ進む"): next_q(); st.rerun()

else: # 英単語
    word, sentence = str(row["question"]), str(row["sentence"])
    sentence_h = re.sub(re.escape(word), f"<span style='color:#ff9800;font-weight:bold'>{word}</span>", sentence, flags=re.IGNORECASE)
    st.markdown(f'<div class="card orange-card">{sentence_h}</div>', unsafe_allow_html=True)
    if "choices" not in st.session_state:
        ans_list = [x.strip() for x in re.split(r'[,、;]', str(row["all_answers"])) if x.strip()]
        correct = ans_list[0] if ans_list else str(row["all_answers"]).strip()
        dummies = [x.strip() for x in re.split(r'[,、;]', str(row["dummy_pool"])) if x.strip() and x.strip() != correct]
        choices = [correct] + random.sample(dummies, min(3, len(dummies)))
        random.shuffle(choices)
        st.session_state.choices, st.session_state.correct = choices, correct
    
    c1, c2 = st.columns(2)
    for i, choice in enumerate(st.session_state.choices):
        with (c1 if i % 2 == 0 else c2):
            if st.button(choice, key=f"btn_{i}", disabled=st.session_state.answered):
                st.session_state.selected, st.session_state.answered = choice, True; st.rerun()
    if st.session_state.answered:
        if st.session_state.selected == st.session_state.correct: st.success("### ✨ 正解！")
        else: st.error(f"### ❌ 正解：{st.session_state.correct}")
        st.info(f"意味：{row['all_answers']}\n訳：{row['translation']}")
        if st.button("次の問題へ進む ➔"): next_q(); st.rerun()

st.markdown('</div>', unsafe_allow_html=True) # クラス閉じ
