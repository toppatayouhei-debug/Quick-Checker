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
# CSS（カラー・ボタンデザイン改良版）
# ==================================================
st.markdown("""
<style>
.stApp{ background:#f7f8fc; }
.block-container{ max-width:720px; padding-top:4rem; } 
.main-title{ text-align:center; font-size:2rem; font-weight:900; margin-bottom:0.2rem; }
.sub-title{ text-align:center; color:#666; font-size:0.9rem; margin-bottom:1.5rem; }

/* カードデザイン */
.card{ 
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

/* ボタンデザイン（改良版） */
.stButton button {
    width: 100%; border-radius: 16px; font-size: 1.1rem; font-weight: 800;
    transition: all 0.3s ease; border: none; box-shadow: 0 4px 10px rgba(0,0,0,0.08);
}

/* ◯ボタン（青色系） */
div[data-testid="stHorizontalBlock"] div:nth-child(1) button {
    background-color: #e7f3ff; color: #1877f2; border: 2px solid #1877f2;
}
div[data-testid="stHorizontalBlock"] div:nth-child(1) button:hover {
    background-color: #1877f2; color: white;
}

/* ×ボタン（赤色系） */
div[data-testid="stHorizontalBlock"] div:nth-child(2) button {
    background-color: #fff5f5; color: #ff4b4b; border: 2px solid #ff4b4b;
}
div[data-testid="stHorizontalBlock"] div:nth-child(2) button:hover {
    background-color: #ff4b4b; color: white;
}

.guide-text { color: #222222 !important; font-size: 0.88rem; font-weight: 600; margin-bottom: 0.4rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🚀 文系科目は、ゆずれない</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">英語・地歴 統合学習ツール</div>', unsafe_allow_html=True)

# ==================================================
# 章タイトル定義（ここでタイトルを設定）
# ==================================================
CHAPTER_TITLES = {
    "第1章": "日本列島のあけぼの",
    "第2章": "律令国家の形成",
    "第3章": "貴族政治と国風文化",
    "第4章": "中世社会の成立（平安～）",
    # 以降、章が増えたらここに追加
}

# ==================================================
# CSV読み込み
# ==================================================
@st.cache_data
def load_csv(subject):
    files = {
        "英単語": "final_tango_list.csv", 
        "日本史一問一答": "jhcheck.csv",
        "日本史正誤問題攻略": "seigo_check.csv",
        "世界史一問一答": "whcheck.csv" 
    }
    try:
        df = pd.read_csv(files[subject], encoding="utf-8-sig")
        return df.dropna(how='all')
    except Exception as e:
        st.error(f"CSV読み込み失敗: {e}")
        return None

# ==================================================
# 状態管理
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
# メインロジック
# ==================================================
subject = st.selectbox("学習する科目を選択", ["選択してください", "英単語", "日本史一問一答", "日本史正誤問題攻略", "世界史一問一答"])

if subject == "選択してください":
    st.info("科目を選択して学習を開始しましょう！")
    st.stop()

raw_df = load_csv(subject)
if raw_df is None: st.stop()

current_filter = "All"

# --- サイドバー・フィルタリング（日本史系） ---
if "日本史" in subject:
    if "chapter" in raw_df.columns:
        st.sidebar.header("🎯 範囲選択")
        raw_chapters = [str(x) for x in raw_df["chapter"].dropna().unique()]
        
        # 数値順にソート
        def extract_number(text):
            num = re.search(r'\d+', text)
            return int(num.group()) if num else 999
        sorted_chapter_ids = sorted(raw_chapters, key=extract_number)
        
        # 表示用ラベルの作成（"第4章" -> "第4章：平安時代"）
        chapter_labels = ["すべてを表示"]
        for cid in sorted_chapter_ids:
            title = CHAPTER_TITLES.get(cid, "")
            label = f"{cid} {title}".strip()
            chapter_labels.append(label)
        
        selected_label = st.sidebar.radio("学習する章を選択してください", chapter_labels)
        
        if selected_label == "すべてを表示":
            current_filter = "すべて"
            df = raw_df
        else:
            # ラベルからID（"第4章"など）を抽出してフィルタリング
            current_filter = selected_label.split(" ")[0]
            df = raw_df[raw_df["chapter"].astype(str) == current_filter]
    else:
        df = raw_df

# --- 英単語 / 世界史（既存ロジック） ---
elif subject == "世界史一問一答":
    areas = ["すべて"] + sorted([str(x) for x in raw_df["area"].fillna("未分類").unique()])
    current_filter = st.sidebar.selectbox("地域を選択", areas)
    df = raw_df if current_filter == "すべて" else raw_df[raw_df["area"].fillna("未分類").astype(str) == current_filter]
elif subject == "英単語":
    levels = ["All"] + sorted([str(x) for x in raw_df["level"].dropna().unique()])
    current_filter = st.sidebar.selectbox("レベルを選択", levels)
    df = raw_df if current_filter == "All" else raw_df[raw_df["level"].astype(str) == current_filter]

# クイズ開始判定
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
# クイズ表示
# ==================================================

if subject == "日本史正誤問題攻略":
    q, ans_raw = str(row["question"]), str(row["answer"]).strip()
    st.info("📖 『山川 日本史探究』（教科書）の本文をもとにした正誤問題です。")
    st.markdown(f'<div class="card pink-card"><b>{q}</b></div>', unsafe_allow_html=True)
    
    col_o, col_x = st.columns(2)
    with col_o:
        if st.button("⭕️ 正しい", key=f"o_{idx}", disabled=st.session_state.answered):
            st.session_state.user_choice, st.session_state.answered = "◯", True
            st.rerun()
    with col_x:
        if st.button("❌ 誤り", key=f"x_{idx}", disabled=st.session_state.answered):
            st.session_state.user_choice, st.session_state.answered = "×", True
            st.rerun()

    if st.session_state.answered:
        if st.session_state.user_choice == ans_raw:
            st.success("### ✨ 正解！")
        else:
            st.error(f"### ❌ 不正解... 正解は【 {ans_raw} 】")
        if "explanation" in row and pd.notna(row["explanation"]):
            st.markdown(f'<div class="exp-card"><b>💡 解説:</b><br>{row["explanation"]}</div>', unsafe_allow_html=True)
        if st.button("次の問題へ進む ➔"):
            next_q(); st.rerun()

elif subject in ["日本史一問一答", "世界史一問一答"]:
    q, ans_raw = str(row["question"]), str(row["answer"])
    st.markdown(f'<div class="card {"pink-card" if "日本史" in subject else "cyan-card"}"><b>{q}</b></div>', unsafe_allow_html=True)
    user_input = st.text_input("答えを入力", key=f"input_{idx}")
    if st.button("解答する", disabled=st.session_state.answered):
        st.session_state.answered = True; st.rerun()
    if st.session_state.answered:
        user_clean = user_input.replace(" ", "").replace("　", "")
        valid_answers = [a.strip().replace(" ", "").replace("　", "") for a in ans_raw.split("/")]
        if user_clean in valid_answers: st.success("✨ 正解！")
        else: st.error(f"❌ 不正解... 正解：{ans_raw}")
        if "explanation" in row and pd.notna(row["explanation"]):
            st.markdown(f'<div class="exp-card"><b>💡 解説:</b><br>{row["explanation"]}</div>', unsafe_allow_html=True)
        if st.button("次の問題へ"):
            next_q(); st.rerun()

else: # 英単語
    word, sentence = str(row["question"]), str(row["sentence"])
    sentence_html = re.sub(re.escape(word), f"<span style='color:#ff9800;font-weight:bold'>{word}</span>", sentence, flags=re.IGNORECASE)
    st.markdown(f'<div class="card orange-card">{sentence_html}</div>', unsafe_allow_html=True)
    if "choices" not in st.session_state:
        ans_list = [x.strip() for x in re.split(r'[,、;]', str(row["all_answers"])) if x.strip()]
        correct = ans_list[0] if ans_list else str(row["all_answers"]).strip()
        dummies = [x.strip() for x in re.split(r'[,、;]', str(row["dummy_pool"])) if x.strip() and x.strip() != correct]
        choices = [correct] + random.sample(dummies, min(3, len(dummies)))
        random.shuffle(choices)
        st.session_state.choices, st.session_state.correct = choices, correct
    cols = st.columns(2)
    for i, c in enumerate(st.session_state.choices):
        with cols[i % 2]:
            if st.button(c, key=f"btn_{i}", disabled=st.session_state.answered):
                st.session_state.selected, st.session_state.answered = c, True; st.rerun()
    if st.session_state.answered:
        if st.session_state.selected == st.session_state.correct: st.success("✨ 正解！")
        else: st.error(f"❌ 正解：{st.session_state.correct}")
        st.info(f"意味：{row['all_answers']}\n\n訳：{row['translation']}")
        if st.button("次の問題へ"):
            next_q(); st.rerun()
