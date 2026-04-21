import streamlit as st
import pandas as pd
import random

# --- 1. データの読み込み ---
def load_data(file_name, subject):
    try:
        df = pd.read_csv(file_name, engine='python', encoding='utf-8-sig', header=None)
        # 1行目がヘッダー（見出し）なら飛ばす
        first_val = str(df.iloc[0, 0]).lower()
        if any(x in first_val for x in ["question", "word", "単語", "id", "essential"]):
            df = df.iloc[1:].reset_index(drop=True)
        return df
    except Exception:
        return None

# --- 2. 設定 ---
st.set_page_config(page_title="文系科目は、ゆずらない", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #fdfaf5; }
    .highlight-target { color: #2e7d32; font-weight: bold; border-bottom: 2px solid #2e7d32; }
    .sentence-box { background-color: #f0f4f0; padding: 25px; border-radius: 10px; border-left: 8px solid #2e7d32; margin-bottom: 20px; }
    .stButton button { font-size: 16px !important; min-height: 3.5em; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔥 文系科目は、ゆずらない")

# --- 3. 科目選択 ---
selected_subject = st.sidebar.selectbox(
    "学習する科目を選択",
    ["選択してください", "英単語", "古文単語", "日本史一問一答"]
)

subject_map = {
    "古文単語": "kobun350.csv",
    "英単語": "final_tango_list.csv",
    "日本史一問一答": "nihonshi.csv"
}

if selected_subject == "選択してください":
    st.info("サイドバーから科目を選択して開始してください。")
    st.stop()

# 状態リセット処理
if 'last_sub' not in st.session_state or st.session_state.last_sub != selected_subject:
    st.session_state.last_sub = selected_subject
    raw_df = load_data(subject_map[selected_subject], selected_subject)
    if raw_df is not None:
        st.session_state.q_df = raw_df.sample(frac=1).reset_index(drop=True)
        st.session_state.idx = 0
        st.session_state.score = 0
        st.session_state.new_ques = True
        st.session_state.answered = False
    else:
        st.session_state.q_df = None

if st.session_state.q_df is None:
    st.error(f"⚠️ '{subject_map[selected_subject]}' が見つかりません。")
    st.stop()

# --- 4. クイズ表示 ---
df = st.session_state.q_df
if st.session_state.idx < len(df):
    row = df.iloc[st.session_state.idx]
    st.progress((st.session_state.idx + 1) / len(df))
    st.subheader(f"【{selected_subject}】 第 {st.session_state.idx + 1} 問")

    # --- 日本史：記述入力モード ---
    if selected_subject == "日本史一問一答":
        # 0:問題, 1:答え, 2:時代
        q_text = str(row[0])
        correct_answer = str(row[1]).strip()
        
        if len(row) >= 3 and pd.notna(row[2]):
            st.info(f"時代：{row[2]}")

        st.markdown(f'<div class="sentence-box"><p style="font-size:22px;"><b>問題：</b>{q_text}</p></div>', unsafe_allow_html=True)
        st.write("⚠️ 漢字で正確に入力してください。")

        with st.form(key='nihonshi_form', clear_on_submit=True):
            user_input = st.text_input("答えを入力してください", key="nihonshi_input")
            submit_button = st.form_submit_button(label='解答する')

        if submit_button:
            if user_input.strip() == correct_answer:
                st.success(f"✨ 正解！！ 「{correct_answer}」")
                st.session_state.score += 1
            else:
                st.error(f"❌ 不正解... 正解は 「{correct_answer}」 でした。")
            
            st.session_state.answered = True

        if st.session_state.answered:
            if st.button("次の問題へ 👉", type="primary"):
                st.session_state.idx += 1
                st.session_state.answered = False
                st.rerun()

    # --- 英・古文：選択肢モード ---
    else:
        target = str(row[0]).strip()
        correct_raw = str(row[1]).strip()
        dummy_raw = str(row[2]).strip()
        sentence = str(row[3]).strip() if len(row) > 3 else ""
        translation = str(row[4]).strip() if len(row) > 4 else ""

        if st.session_state.new_ques:
            correct_list = [c.strip() for c in correct_raw.split(',')]
            dummy_list = [d.strip() for d in dummy_raw.split(',') if d.strip() != ""]
            display_correct = random.choice(correct_list)
            display_dummies = random.sample(dummy_list, min(len(dummy_list), 3))
            choices = list(set([display_correct] + display_dummies))
            random.shuffle(choices)
            st.session_state.shuffled_choices = choices
            st.session_state.new_ques = False

        if selected_subject == "英単語":
            display_text = f'<div style="text-align:center;"><span style="font-size:35px; font-weight:bold; color:#2e7d32;">{target}</span></div>'
            if sentence and sentence.lower() != "nan":
                display_text += f'<hr><p style="font-size:18px;">{sentence}</p>'
        else: # 古文
            h_target = f'<span class="highlight-target">{target}</span>'
            display_text = sentence.replace(target, h_target) if (sentence and target in sentence) else f"{sentence}<br>({h_target})"
        
        st.markdown(f'<div class="sentence-box"><p style="font-size:20px; color:#333;">{display_text}</p></div>', unsafe_allow_html=True)

        for choice in st.session_state.shuffled_choices:
            if st.button(choice, use_container_width=True, disabled=st.session_state.answered):
                st.session_state.answered = True
                st.session_state.last_res = "correct" if choice in correct_raw.split(',') else "incorrect"
                if st.session_state.last_res == "correct": st.session_state.score += 1
                st.rerun()

        if st.session_state.answered:
            if st.session_state.last_res == "correct": st.success("✨ 正解！")
            else: st.error(f"❌ 不正解... 正解は: {correct_raw}")
            if st.button("次の問題へ 👉", type="primary"):
                st.session_state.idx += 1
                st.session_state.answered = False
                st.session_state.new_ques = True
                st.rerun()

else:
    st.balloons()
    st.write(f"## 🎉 {selected_subject} 全問終了！")
    st.write(f"正解数: {st.session_state.score} / {len(df)}")
    if st.button("最初からやり直す"):
        del st.session_state.q_df
        st.rerun()
