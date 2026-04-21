
import streamlit as st
import pandas as pd
import random

# --- 1. データの読み込み関数 ---
@st.cache_data
def load_data(file_name):
    try:
        # header=None で読み込み、列名に依存しないようにする
        df = pd.read_csv(file_name, engine='python', encoding='utf-8-sig', header=None)
        
        # 1行目がヘッダー（英語名など）なら除外
        first_cell = str(df.iloc[0, 0]).lower()
        if any(x in first_cell for x in ["question", "単語", "word", "id"]):
            df = df.iloc[1:].reset_index(drop=True)
        return df
    except Exception as e:
        return None

# --- 2. 画面設定とデザイン ---
st.set_page_config(page_title="受験全科目 網羅クイズ", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #fdfaf5; }
    .highlight-target { color: #2e7d32; font-weight: bold; border-bottom: 2px solid #2e7d32; }
    .stButton button { font-size: 16px !important; min-height: 3.5em; margin-bottom: 5px; }
    .sentence-box { background-color: #f0f4f0; padding: 20px; border-radius: 10px; border-left: 8px solid #2e7d32; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 科目選択（入口） ---
st.title("📚 受験全科目 網羅クイズ")

# セッション状態で科目が変わったら進捗をリセットする
selected_subject = st.sidebar.selectbox(
    "学習する科目を選んでください",
    ["選択してください", "古文単語350", "英単語", "日本史一問一答"]
)

# ファイル名の紐付け
subject_map = {
    "古文単語350": "kobun350.csv",
    "英単語": "english.csv",
    "日本史一問一答": "nihonshi.csv"
}

if selected_subject == "選択してください":
    st.info("左のサイドバーから科目を選択してください。学習を開始します！")
    st.stop()

# 科目が切り替わったらデータを再ロードして状態をリセット
if 'current_subject' not in st.session_state or st.session_state.current_subject != selected_subject:
    st.session_state.current_subject = selected_subject
    st.session_state.df = load_data(subject_map[selected_subject])
    if st.session_state.df is not None:
        st.session_state.questions = st.session_state.df.sample(frac=1).reset_index(drop=True)
    st.session_state.idx = 0
    st.session_state.score = 0
    st.session_state.new_ques = True
    st.session_state.answered = False

df = st.session_state.df

if df is None:
    st.error(f"⚠️ '{subject_map[selected_subject]}' が見つかりません。")
    st.stop()

# --- 4. クイズ本編 ---
st.sidebar.write(f"**科目:** {selected_subject}")
st.sidebar.write(f"進捗: {st.session_state.idx} / {len(st.session_state.questions)}")

if st.session_state.idx < len(st.session_state.questions):
    row = st.session_state.questions.iloc[st.session_state.idx]
    st.progress((st.session_state.idx + 1) / len(st.session_state.questions))
    
    # 共通のデータ取得（列番号で取得）
    # 0:単語, 1:正解, 2:ダミー, 3:例文/ヒント, 4:訳/詳細
    target = str(row[0]).strip()
    correct_list = [a.strip() for a in str(row[1]).split(',')]
    dummy_list = [d.strip() for d in str(row[2]).split(',')]
    
    # D列とE列が空の場合の処理
    sentence = str(row[3]).strip() if len(row) > 3 and pd.notna(row[3]) else ""
    translation = str(row[4]).strip() if len(row) > 4 and pd.notna(row[4]) else ""

    if st.session_state.new_ques:
        display_correct = random.choice(correct_list)
        display_dummies = random.sample(dummy_list, min(len(dummy_list), 3))
        choices = [display_correct] + display_dummies
        random.shuffle(choices)
        st.session_state.shuffled_choices = choices
        st.session_state.new_ques = False
        st.session_state.answered = False

    st.subheader("問題")
    
    # 表示のカスタマイズ（古文ならハイライト、日本史ならヒントとして表示など）
    highlighted_html = f'<span class="highlight-target">{target}</span>'
    if sentence and sentence.lower() != "nan":
        if target in sentence:
            display_text = sentence.replace(target, highlighted_html)
        else:
            display_text = f"{sentence}<br><small>(対象: {highlighted_html})</small>"
    else:
        display_text = f"【問題】 {highlighted_html}"

    st.markdown(f'<div class="sentence-box"><p style="font-size:22px;">{display_text}</p></div>', unsafe_allow_html=True)

    # 選択肢
    for choice in st.session_state.shuffled_choices:
        if st.button(choice, use_container_width=True, disabled=st.session_state.answered):
            st.session_state.answered = True
            st.session_state.last_result = "correct" if choice in correct_list else "incorrect"
            if st.session_state.last_result == "correct":
                st.session_state.score += 1
            st.rerun()

    # 回答後
    if st.session_state.answered:
        if st.session_state.last_result == "correct":
            st.success("✨ 正解！")
        else:
            st.error("❌ 不正解...")
        
        st.info(f"**正解:** {', '.join(correct_list)}")

        if translation and translation.lower() != "nan":
            with st.expander("📖 解説・現代語訳を見る", expanded=True):
                st.write(translation)

        if st.button("次の問題へ 👉", type="primary"):
            st.session_state.idx += 1
            st.session_state.new_ques = True
            st.session_state.answered = False
            st.rerun()
else:
    st.balloons()
    st.write(f"## 🎉 {selected_subject} 全問終了！")
    accuracy = (st.session_state.score / len(st.session_state.questions)) * 100
    st.metric("最終正答率", f"{accuracy:.1f}%")
    if st.button("もう一度（シャッフル）"):
        st.session_state.idx = 0
        st.session_state.score = 0
        st.session_state.questions = st.session_state.df.sample(frac=1).reset_index(drop=True)
        st.session_state.new_ques = True
        st.session_state.answered = False
        st.rerun()
