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
# CSS（レイアウト・視認性調整）
# ==================================================
st.markdown("""
<style>
.stApp{ background:#f7f8fc; }
.block-container{ max-width:720px; padding-top:4rem; } 

.main-title{ text-align:center; font-size:2rem; font-weight:900; margin-bottom:0.2rem; }
.sub-title{ text-align:center; color:#666; font-size:0.9rem; margin-bottom:1.5rem; }
.card{ 
    background:white; padding:22px; border-radius:18px; 
    box-shadow:0 8px 20px rgba(0,0,0,0.06); margin-bottom:1rem; 
    line-height:1.7; font-size:1.05rem; color:#111; 
}
.red{border-left:8px solid #e53935;}
.blue{border-left:8px solid #1565c0;}

.stButton button{ 
    width:100%; border-radius:14px; padding:0.8rem; 
    font-size:0.95rem; font-weight:700; min-height:60px; 
}

.guide-text { 
    color: #222222 !important; 
    font-size: 0.88rem; 
    font-weight: 600;
    margin-bottom: 0.4rem;
}

@media (max-width:768px){ .main-title{font-size:1.55rem;} .card{padding:16px;font-size:0.98rem;} .block-container{ padding-top:3rem; } }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🚀 文系科目は、ゆずれない</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">英語・日本史 統合学習ツール</div>', unsafe_allow_html=True)

# ==================================================
# CSV読み込み
# ==================================================
@st.cache_data
def load_csv(subject):
    files = {
        "英単語": "final_tango_list.csv", 
        "日本史一問一答": "jhcheck.csv" 
    }
    try:
        return pd.read_csv(files[subject], encoding="utf-8-sig")
    except Exception as e:
        st.error(f"CSV読み込み失敗: {e}")
        return None

# ==================================================
# 状態管理
# ==================================================
def clear_quiz_state():
    for key in ["quiz_subject", "quiz_filter", "df", "idx", "answered", "choices", "correct", "selected"]:
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
    for key in ["choices", "correct", "selected"]:
        if key in st.session_state: del st.session_state[key]

# ==================================================
# 科目・フィルタ選択
# ==================================================
subject = st.selectbox("学習する科目を選択", ["選択してください", "英単語", "日本史一問一答"])

if subject == "選択してください":
    st.info("科目を選択して学習を開始しましょう！")
    st.stop()

raw_df = load_csv(subject)
if raw_df is None: st.stop()

current_filter = "All"

if subject == "日本史一問一答":
    if "chapter" in raw_df.columns:
        raw_chapters = raw_df["chapter"].unique().tolist()
        def extract_number(text):
            num = re.search(r'\d+', str(text))
            return int(num.group()) if num else 999
        sorted_chapters = sorted(raw_chapters, key=extract_number)
        chapters = ["すべて"] + sorted_chapters
        current_filter = st.sidebar.selectbox("章（Chapter）を選択", chapters)
        df = raw_df if current_filter == "すべて" else raw_df[raw_df["chapter"] == current_filter]
    else:
        df = raw_df

elif subject == "英単語":
    if "level" in raw_df.columns:
        levels = ["All"] + sorted(raw_df["level"].astype(str).unique().tolist())
        current_filter = st.sidebar.selectbox("レベルを選択", levels)
        df = raw_df if current_filter == "All" else raw_df[raw_df["level"].astype(str) == current_filter]
    else:
        df = raw_df

if ("quiz_subject" not in st.session_state or 
    st.session_state.quiz_subject != subject or 
    st.session_state.quiz_filter != current_filter):
    clear_quiz_state()
    start_quiz(df, subject, current_filter)

active_df = st.session_state.df
idx = st.session_state.idx

if idx >= len(active_df):
    st.balloons()
    st.success("この範囲の全問が終了しました！")
    if st.button("最初から解き直す"): 
        clear_quiz_state()
        st.rerun()
    st.stop()

row = active_df.iloc[idx]
st.progress((idx + 1) / len(active_df))
st.caption(f"{idx+1} / {len(active_df)} 問目（範囲: {current_filter}）")

# ==================================================
# 日本史セクション
# ==================================================
if subject == "日本史一問一答":
    q = str(row["question"])
    ans_raw = str(row["answer"])
    
    st.markdown(f'<div class="card blue"><b>{q}</b></div>', unsafe_allow_html=True)
    st.markdown('<div class="guide-text">⚠️ カタカナの人名は姓と名の間にスペースや記号を加えずに解答してください。</div>', unsafe_allow_html=True)
    st.markdown('<div class="guide-text">💡 重要語句 Check Listの問題です。サイドバーから時代を選択してください。近現代史は後日追加します。</div>', unsafe_allow_html=True)
    
    user_input = st.text_input("答えを入力", key=f"input_{idx}")
    
    if st.button("解答する"):
        st.session_state.answered = True

    if st.session_state.answered:
        user_clean = user_input.replace(" ", "").replace("　", "")
        valid_answers = [a.strip().replace(" ", "").replace("　", "") for a in ans_raw.split("/")]

        if user_clean in valid_answers:
            st.success("✨ 正解！")
            if "/" in ans_raw: st.info(f"正解パターン: {ans_raw.replace('/', ' , ')}")
        else:
            st.error(f"❌ 不正解...")
            st.warning(f"正しい答え：{ans_raw.replace('/', ' または ')}")
        
        if st.button("次の問題へ"):
            next_q(); st.rerun()

# ==================================================
# 英単語セクション
# ==================================================
else:
    word = str(row["question"])
    sentence = str(row["sentence"])
    sentence_html = re.sub(re.escape(word), f"<span style='color:#e53935;font-weight:bold'>{word}</span>", sentence, flags=re.IGNORECASE)
    
    st.markdown(f'<div class="card red">{sentence_html}</div>', unsafe_allow_html=True)
    st.markdown('<div class="guide-text">💡 シス単準拠の単語学習ツールです。左のサイドバーで問題レベルを選んでください。</div>', unsafe_allow_html=True)

    if "choices" not in st.session_state:
        # 全ての答えをリスト化
        ans_list = [x.strip() for x in str(row["all_answers"]).split(",") if x.strip()]
        # 【修正】選択肢には先頭の1つだけを使用する
        correct = ans_list[0] 
        
        dummies = [x.strip() for x in str(row["dummy_pool"]).split(",") if x.strip()]
        choices = [correct] + random.sample(dummies, min(3, len(dummies)))
        random.shuffle(choices)
        st.session_state.choices, st.session_state.correct = choices, correct

    cols = st.columns(2)
    for i, c in enumerate(st.session_state.choices):
        with cols[i % 2]:
            if st.button(c, key=f"btn_{i}", disabled=st.session_state.answered):
                st.session_state.selected, st.session_state.answered = c, True
                st.rerun()

    if st.session_state.answered:
        if st.session_state.selected == st.session_state.correct: st.success("✨ 正解！")
        else: st.error(f"❌ 正解：{st.session_state.correct}")
        
        # 解説画面では全ての意味を表示
        st.info(f"意味：{row['all_answers']}\n\n訳：{row['translation']}")
        
        if st.button("次の問題へ"): 
            next_q(); st.rerun()
