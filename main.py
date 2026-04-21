import streamlit as st
import pandas as pd
import random

# --- 1. データの読み込み ---
def load_data(file_name, subject):
    try:
        df = pd.read_csv(file_name, engine='python', encoding='utf-8-sig', header=None)
        
        # 1行目がヘッダー（見出し）なら飛ばす判定
        first_val = str(df.iloc[0, 0]).lower()
        if subject == "英単語" or "essential" in first_val or "level" in first_val or "question" in first_val:
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

# アプリタイトルの変更
st.title("🔥 文系科目は、ゆずらない")

# --- 3. 科目選択 ---
selected_subject = st.sidebar.selectbox(
    "学習する科目を選択",
    ["選択してください", "英単語", "古文単語", "日本史一問一答"]
)

# ファイル名との紐付け（GitHub上のファイル名と一致させてください）
subject_map = {
    "古文単語": "kobun350.csv",
    "英単語": "final_tango_list.csv",
    "日本史一問一答": "nihonshi.csv"
}

if selected_subject == "選択してください":
    st.info("サイドバーから科目を選択して、学習を開始しましょう！")
    st.stop()

# 状態リセット
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
    st.error(f"⚠️ '{subject_map[selected_subject]}' が見つかりません。GitHubのファイル名を確認してください。")
    st.stop()

# --- 4. クイズ表示 ---
df = st.session_state.q_df
if st.session_state.idx < len(df):
    row = df.iloc[st.session_state.idx]
    
    # 共通データ取得 (0:単語/問題, 1:正解, 2:誤答, 3:例文/問題文, 4:訳/解説)
    target = str(row[0]).strip()
    correct_list = [a.strip() for a in str(row[1]).split(',')]
    dummy_list = [d.strip() for d in str(row[2]).split(',')]
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

    st.subheader(f"【{selected_subject}】 第 {st.session_state.idx + 1} 問")
    
    # 科目別の表示カスタマイズ
    if selected_subject == "古文単語":
        h_target = f'<span class="highlight-target">{target}</span>'
        if sentence and sentence.lower() != "nan":
            display_text = sentence.replace(target, h_target) if target in sentence else f"{sentence}<br><br>({h_target})"
        else:
            display_text = f"（単語） {h_target}"
            
    elif selected_subject == "英単語":
        display_text = f'<div style="text-align:center;"><span style="font-size:32px; font-weight:bold;">{target}</span></div>'
        if sentence and sentence.lower() != "nan":
            display_text += f'<hr><p style="font-size:18px;">{sentence.replace(target, f"<b>{target}</b>")}</p>'
            
    else: # 日本史
        display_text = sentence if sentence and sentence.lower() != "nan" else f"【問題】 {target}"

    st.markdown(f'<div class="sentence-box"><p style="font-size:20px; color:#333;">{display_text}</p></div>', unsafe_allow_html=True)

    # 選択肢
    for choice in st.session_state.shuffled_choices:
        if st.button(choice, use_container_width=True, disabled=st.session_state.answered):
            st.session_state.answered = True
            st.session_state.last_res = "correct" if choice in correct_list else "incorrect"
            if st.session_state.last_res == "correct": st.session_state.score += 1
            st.rerun()

    if st.session_state.answered:
        if st.session_state.last_res == "correct": st.success("✨ 正解！")
        else: st.error("❌ 不正解...")
        st.info(f"**正解:** {', '.join(correct_list)}")
        if translation and translation.lower() != "nan":
            with st.expander("📖 解説・訳を見る", expanded=True): st.write(translation)
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
    if st.button("もう一度挑戦（シャッフル）"):
        del st.session_state.q_df
        st.rerun()
