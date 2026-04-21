import streamlit as st
import pandas as pd
import random
import re

# --- 1. 画面設定（視認性確保とボタンの修正） ---
st.set_page_config(page_title="文系科目は、ゆずらない", layout="centered")

st.markdown("""
    <style>
    /* 全体背景と基本文字色 */
    .stApp { background-color: white !important; color: black !important; }
    [data-testid="stSidebar"] { background-color: #f8f9fa !important; }
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p { color: black !important; }
    
    /* 問題文ボックス（枠を少し太くして視認性アップ） */
    .sentence-box {
        background-color: #f0f2f6 !important;
        color: black !important;
        padding: 25px;
        border-radius: 12px;
        border-left: 10px solid #2e7d32;
        margin-bottom: 25px;
        line-height: 1.6;
    }
    
    /* ボタンの修正：黒く潰れるのを防ぐ */
    .stButton button {
        color: #333 !important;
        background-color: #ffffff !important;
        border: 1px solid #bbb !important;
        font-weight: bold !important;
    }
    /* 日本史の「解答する」ボタン（Form内）を特別扱い */
    button[kind="primaryFormSubmit"] {
        background-color: #2e7d32 !important;
        color: white !important;
        border: none !important;
    }
    
    h1, h2, h3, p, span { color: black !important; }
    
    /* ハイライト用のスタイル */
    .hl-eng { color: #d32f2f !important; font-weight: bold; text-decoration: underline; }
    .hl-kobun { color: #2e7d32 !important; font-weight: bold; border-bottom: 2px solid #2e7d32; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔥 文系科目は、ゆずらない")

# --- 2. 科目選択 ---
selected_subject = st.sidebar.selectbox(
    "学習する科目を選択",
    ["選択してください", "英単語", "古文単語", "日本史一問一答"]
)

@st.cache_data
def load_raw_data(subject):
    files = {"英単語": "final_tango_list.csv", "古文単語": "kobun350.csv", "日本史一問一答": "nihonshi.csv"}
    try:
        if subject == "英単語":
            return pd.read_csv(files[subject], encoding='utf-8-sig')
        else:
            return pd.read_csv(files[subject], encoding='utf-8-sig', header=None)
    except: return None

# --- 3. メインロジック ---
if selected_subject != "選択してください":
    raw_df = load_raw_data(selected_subject)
    if raw_df is not None:
        if selected_subject == "英単語":
            levels = ["All"] + sorted(raw_df['level'].unique().tolist(), key=lambda x: int(x) if str(x).isdigit() else 999)
            sel_level = st.sidebar.selectbox("レベルを選択", levels)
            current_df = raw_df if sel_level == "All" else raw_df[raw_df['level'] == sel_level]
        else:
            current_df, sel_level = raw_df, None

        state_key = f"{selected_subject}_{sel_level}"
        if st.session_state.get('last_state_key') != state_key:
            st.session_state.last_state_key = state_key
            st.session_state.q_df = current_df.sample(frac=1).reset_index(drop=True)
            st.session_state.idx = 0
            st.session_state.answered = False

        df = st.session_state.q_df
        if st.session_state.idx < len(df):
            row = df.iloc[st.session_state.idx]
            st.subheader(f"【{selected_subject}】 第 {st.session_state.idx + 1} 問")

            # --- 日本史 ---
            if selected_subject == "日本史一問一答":
                q_text, ans_text = str(row.iloc[0]), str(row.iloc[1]).strip()
                if len(row) > 2: st.info(f"時代：{row.iloc[2]}")
                st.markdown(f'<div class="sentence-box"><h3 style="margin:0;">問題：{q_text}</h3></div>', unsafe_allow_html=True)
                with st.form(key='history_form'):
                    user_input = st.text_input("答えを入力（漢字）")
                    if st.form_submit_button("解答する"):
                        st.session_state.answered = True
                        st.session_state.user_ans = user_input.strip()
                
                if st.session_state.answered:
                    if st.session_state.user_ans == ans_text: st.success(f"✨ 正解！！ 「{ans_text}」")
                    else: st.error(f"❌ 不正解... 正解は 「{ans_text}」")
                    if st.button("次の問題へ 👉"):
                        st.session_state.idx += 1
                        st.session_state.answered = False
                        st.rerun()

            # --- 英単語・古文 ---
            else:
                if selected_subject == "英単語":
                    word, correct = str(row['question']), str(row['all_answers'])
                    dummy_raw, sentence, trans = str(row['dummy_pool']), str(row['sentence']), str(row['translation'])
                    # 英単語ハイライト（赤字）
                    highlighted = re.sub(re.escape(word), f'<span class="hl-eng">{word}</span>', sentence, flags=re.IGNORECASE) if (sentence and sentence != "nan") else f"単語：<span class=\"hl-eng\">{word}</span>"
                else:
                    word, correct, dummy_raw = str(row.iloc[0]), str(row.iloc[1]), str(row.iloc[2])
                    sentence, trans = str(row.iloc[3]), str(row.iloc[4])
                    # 古文ハイライト（緑字）
                    highlighted = sentence.replace(word, f'<span class="hl-kobun">{word}</span>') if (sentence and sentence != "nan") else f"古語：<span class=\"hl-kobun\">{word}</span>"

                st.markdown(f'<div class="sentence-box"><p style="font-size:22px; color:black;">{highlighted}</p></div>', unsafe_allow_html=True)

                if 'choices' not in st.session_state or st.session_state.get('last_idx') != st.session_state.idx:
                    dummies = [d.strip() for d in dummy_raw.split(',') if d.strip()]
                    pool = [correct] + random.sample(dummies, min(len(dummies), 3))
                    random.shuffle(pool)
                    st.session_state.choices, st.session_state.last_idx = pool, st.session_state.idx

                for c in st.session_state.choices:
                    if st.button(c, use_container_width=True, disabled=st.session_state.answered):
                        st.session_state.answered, st.session_state.is_correct = True, (c == correct)
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
            if st.button("全問終了！最初から"):
                st.session_state.idx = 0
                st.session_state.answered = False
                st.rerun()
else:
    st.info("サイドバーから科目を選択してください。")
