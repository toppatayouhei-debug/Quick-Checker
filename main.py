import streamlit as st
import pandas as pd
import random
import re

# --- 1. 画面設定（視認性確保） ---
st.set_page_config(page_title="文系科目は、ゆずらない", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: white !important; color: black !important; }
    [data-testid="stSidebar"] { background-color: #f8f9fa !important; color: black !important; }
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p { color: black !important; }
    .sentence-box {
        background-color: #f0f2f6 !important;
        color: black !important;
        padding: 25px;
        border-radius: 10px;
        border-left: 8px solid #2e7d32;
        margin-bottom: 20px;
    }
    .stButton button { color: black !important; background-color: white !important; border: 1px solid #ccc !important; }
    h1, h2, h3, p, span { color: black !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔥 文系科目は、ゆずらない")

# --- 2. 科目選択 ---
selected_subject = st.sidebar.selectbox(
    "学習する科目を選択",
    ["選択してください", "英単語", "古文単語", "日本史一問一答"]
)

# --- 3. データ読み込み関数 ---
@st.cache_data
def load_raw_data(subject):
    files = {"英単語": "final_tango_list.csv", "古文単語": "kobun350.csv", "日本史一問一答": "nihonshi.csv"}
    try:
        if subject == "英単語":
            return pd.read_csv(files[subject], encoding='utf-8-sig')
        else:
            return pd.read_csv(files[subject], encoding='utf-8-sig', header=None)
    except:
        return None

# --- 4. メイン処理 ---
if selected_subject != "選択してください":
    raw_df = load_raw_data(selected_subject)
    
    if raw_df is not None:
        # --- A. 英単語専用設定 ---
        if selected_subject == "英単語":
            levels = ["All"] + sorted(raw_df['level'].unique().tolist(), key=lambda x: int(x) if str(x).isdigit() else 999)
            sel_level = st.sidebar.selectbox("レベルを選択", levels)
            current_df = raw_df if sel_level == "All" else raw_df[raw_df['level'] == sel_level]
        else:
            current_df = raw_df
            sel_level = None

        # --- B. セッションリセット（科目・レベル変更時） ---
        state_key = f"{selected_subject}_{sel_level}"
        if st.session_state.get('last_state_key') != state_key:
            st.session_state.last_state_key = state_key
            st.session_state.q_df = current_df.sample(frac=1).reset_index(drop=True)
            st.session_state.idx = 0
            st.session_state.answered = False
            # 選択肢もリセット
            if 'choices' in st.session_state: del st.session_state.choices

        df = st.session_state.q_df
        
        if st.session_state.idx < len(df):
            row = df.iloc[st.session_state.idx]
            st.subheader(f"【{selected_subject}】 第 {st.session_state.idx + 1} 問")

            # --- C. 科目別出し分け ---
            
            # 1. 日本史 (記述)
            if selected_subject == "日本史一問一答":
                q_text, ans_text = str(row.iloc[0]), str(row.iloc[1]).strip()
                if len(row) > 2: st.info(f"時代：{row.iloc[2]}")
                st.markdown(f'<div class="sentence-box"><h3>問題：{q_text}</h3></div>', unsafe_allow_html=True)
                with st.form(key='jp_form', clear_on_submit=True):
                    user_input = st.text_input("答え（漢字）")
                    if st.form_submit_button("解答する"):
                        st.session_state.answered = True
                        st.session_state.user_ans = user_input.strip()
                
                if st.session_state.answered:
                    if st.session_state.user_ans == ans_text: st.success(f"✨ 正解！ 「{ans_text}」")
                    else: st.error(f"❌ 正解は 「{ans_text}」")
                    if st.button("次の問題へ 👉"):
                        st.session_state.idx += 1
                        st.session_state.answered = False
                        st.rerun()

            # 2. 英単語・古文 (選択肢)
            else:
                if selected_subject == "英単語":
                    word, correct = str(row['question']), str(row['all_answers'])
                    dummy_raw = str(row['dummy_pool'])
                    sentence, trans = str(row['sentence']), str(row['translation'])
                    # 英単語ハイライト
                    display_q = re.sub(re.escape(word), f'<span style="color:red; font-weight:bold;">{word}</span>', sentence, flags=re.IGNORECASE) if sentence and sentence != "nan" else f"単語：{word}"
                else: # 古文
                    word, correct, dummy_raw = str(row.iloc[0]), str(row.iloc[1]), str(row.iloc[2])
                    sentence, trans = str(row.iloc[3]), str(row.iloc[4])
                    # 古文ハイライト
                    display_q = sentence.replace(word, f'<span style="color:#2e7d32; font-weight:bold;">{word}</span>') if sentence and sentence != "nan" else f"単語：{word}"

                st.markdown(f'<div class="sentence-box"><p style="font-size:22px;">{display_q}</p></div>', unsafe_allow_html=True)

                # 選択肢の生成・保持（回答するまで固定）
                if 'choices' not in st.session_state or st.session_state.get('last_idx') != st.session_state.idx:
                    dummies = [d.strip() for d in dummy_raw.split(',') if d.strip()]
                    pool = [correct] + random.sample(dummies, min(len(dummies), 3))
                    random.shuffle(pool)
                    st.session_state.choices = pool
                    st.session_state.last_idx = st.session_state.idx

                for c in st.session_state.choices:
                    if st.button(c, use_container_width=True, disabled=st.session_state.answered):
                        st.session_state.answered = True
                        st.session_state.is_correct = (c == correct)
                        st.rerun()

                if st.session_state.answered:
                    if st.session_state.is_correct: st.success("✨ 正解！")
                    else: st.error(f"❌ 正解は 「{correct}」")
                    if trans and trans != "nan": st.info(f"💡 訳・解説: {trans}")
                    if st.button("次の問題へ 👉"):
                        st.session_state.idx += 1
                        st.session_state.answered = False
                        st.rerun()

        else:
            st.balloons()
            st.success("終了！")
            if st.button("もう一度"):
                st.session_state.idx = 0
                st.session_state.answered = False
                st.rerun()
else:
    st.info("サイドバーから科目を選択してください。")
