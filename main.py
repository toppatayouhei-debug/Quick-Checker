import streamlit as st
import pandas as pd
import random

# --- 1. データの読み込み関数 ---
def load_data(file_name):
    try:
        # header=None で読み込み、列名に依存しないようにする
        df = pd.read_csv(file_name, engine='python', encoding='utf-8-sig', header=None)
        
        # 1行目がヘッダー（question, word等）なら除外
        first_cell = str(df.iloc[0, 0]).lower()
        if any(x in first_cell for x in ["question", "単語", "word", "id"]):
            df = df.iloc[1:].reset_index(drop=True)
        return df
    except Exception as e:
        return None

# --- 2. 画面設定とデザイン ---
st.set_page_config(page_title="文系科目は、ゆずらない", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #fdfaf5; }
    .highlight-target { color: #2e7d32; font-weight: bold; border-bottom: 2px solid #2e7d32; }
    .stButton button { font-size: 16px !important; min-height: 3.5em; margin-bottom: 5px; }
    .sentence-box { background-color: #f0f4f0; padding: 20px; border-radius: 10px; border-left: 8px solid #2e7d32; margin-bottom: 20px; min-height: 80px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📚 文系科目は、ゆずらない")

# --- 3. 科目選択（入口） ---
selected_subject = st.sidebar.selectbox(
    "学習する科目を選んでください",
    ["選択してください", "古文単語", "英単語", "日本史一問一答"]
)

# 【重要】あなたのファイル名に合わせて修正しました
subject_map = {
    "古文単語": "kobun350.csv",
    "英単語": "final_tango_list.csv",  # ここを修正
    "日本史一問一答": "nihonshi.csv"
}

if selected_subject == "選択してください":
    st.info("左のサイドバーから科目を選択してください。学習を開始します！")
    st.stop()

# 科目が切り替え時のリセット処理
if 'last_sub' not in st.session_state or st.session_state.last_sub != selected_subject:
    st.session_state.last_sub = selected_subject
    raw_df = load_data(subject_map[selected_subject])
    if raw_df is not None:
        st.session_state.q_df = raw_df.sample(frac=1).reset_index(drop=True)
        st.session_state.idx = 0
        st.session_state.score = 0
        st.session_state.new_ques = True
        st.session_state.answered = False
    else:
        st.session_state.q_df = None

if st.session_state.q_df is None:
    st.error(f"⚠️ '{subject_map[selected_subject]}' が見つかりません。GitHubのファイル名を確認してください。")
    st.stop()

df = st.session_state.q_df

# --- 4. クイズ本編 ---
st.sidebar.write(f"進捗: {st.session_state.idx} / {len(df)}")

if st.session_state.idx < len(df):
    row = df.iloc[st.session_state.idx]
    st.progress((st.session_state.idx + 1) / len(df))
    
    # データの取得（列番号指定。4列目=例文, 5列目=訳）
    target = str(row[0]).strip()
    correct_list = [a.strip() for a in str(row[1]).split(',')]
    dummy_list = [d.strip() for d in str(row[2]).split(',')]
    
    # 例文と訳の取得をさらに強化
    sentence = str(row[3]).strip() if len(row) > 3 and pd.notna(row[3]) else ""
    translation = str(row[4]).strip() if len(row) > 4 and pd.notna(row[4]) else ""

    if st.session_state.new_ques:
        display_correct = random.choice(correct_list)
        display_dummies = random.sample(dummy_list, min(len(dummy_list), 3))
        choices = list(set([display_correct] + display_dummies))
        random.shuffle(choices)
        st.session_state.shuffled_choices = choices
        st.session_state.new_ques = False
        st.session_state.answered = False

    st.subheader(f"【{selected_subject}】 問題")
    
    # 表示のカスタマイズ
    highlighted_html = f'<span class="highlight-target">{target}</span>'
    if sentence and sentence.lower() != "nan" and sentence != "":
        if target in sentence:
            display_text = sentence.replace(target, highlighted_html)
        else:
            display_text = f"{sentence}<br><br>(対象: {highlighted_html})"
    else:
        display_text = f"【単語】 {highlighted_html}"

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
        
        st.info(f"**「{target}」の正解:** {', '.join(correct_list)}")

        if translation and translation.lower() != "nan" and translation != "":
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
    accuracy = (st.session_state.score / len(df)) * 100
    st.metric("最終正答率", f"{accuracy:.1f}%")
    if st.button("もう一度（シャッフル）"):
        st.session_state.idx = 0
        st.session_state.score = 0
        st.session_state.q_df = df.sample(frac=1).reset_index(drop=True)
        st.session_state.new_ques = True
        st.session_state.answered = False
        st.rerun()
