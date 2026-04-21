import streamlit as st
import pandas as pd
import random

# --- 1. 画面設定（全エリアの視認性を確保） ---
st.set_page_config(page_title="文系科目は、ゆずらない", layout="centered")

st.markdown("""
    <style>
    /* メインエリアの背景と文字色 */
    .stApp {
        background-color: white !important;
        color: black !important;
    }
    /* サイドバーの背景と文字色を強制 */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa !important;
        color: black !important;
    }
    /* サイドバー内のラベル、テキスト、セレクトボックスの文字 */
    [data-testid="stSidebar"] .stText, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] p {
        color: black !important;
    }
    /* 問題文ボックス */
    .sentence-box {
        background-color: #f0f2f6 !important;
        color: black !important;
        padding: 25px;
        border-radius: 10px;
        border-left: 8px solid #2e7d32;
        margin-bottom: 20px;
    }
    /* ボタンの文字色 */
    .stButton button {
        color: black !important;
        font-size: 16px !important;
        background-color: #ffffff !important;
        border: 1px solid #ccc !important;
    }
    /* 見出しなどの文字色 */
    h1, h2, h3 {
        color: black !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🔥 文系科目は、ゆずらない")

# --- 2. サイドバー設定 ---
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
            # 英語はヘッダーあり(level, question等)
            return pd.read_csv(files[subject], encoding='utf-8-sig')
        else:
            # 古文・日本史はヘッダーなし
            return pd.read_csv(files[subject], encoding='utf-8-sig', header=None)
    except Exception as e:
        st.error(f"ファイルが見つかりません: {e}")
        return None

# --- 4. メインロジック ---
if selected_subject != "選択してください":
    raw_df = load_raw_data(selected_subject)
    
    if raw_df is not None:
        current_df = raw_df
        # 【英単語専用】レベル選択
        if selected_subject == "英単語" and 'level' in raw_df.columns:
            levels = ["All"] + sorted(raw_df['level'].unique().tolist())
            sel_level = st.sidebar.selectbox("レベルを選択", levels)
            if sel_level != "All":
                current_df = raw_df[raw_df['level'] == sel_level]

        # セッションのリセット
        if 'last_sub' not in st.session_state or st.session_state.last_sub != selected_subject or st.session_state.get('last_level') != (sel_level if selected_subject == "英単語" else None):
            st.session_state.last_sub = selected_subject
            if selected_subject == "英単語": st.session_state.last_level = sel_level
            st.session_state.idx = 0
            st.session_state.answered = False
            st.session_state.q_df = current_df.sample(frac=1).reset_index(drop=True)

        df = st.session_state.q_df

        if st.session_state.idx < len(df):
            row = df.iloc[st.session_state.idx]
            st.subheader(f"【{selected_subject}】 第 {st.session_state.idx + 1} 問")

            # --- 日本史：記述モード ---
            if selected_subject == "日本史一問一答":
                q_text, ans_text = str(row.iloc[0]), str(row.iloc[1]).strip()
                if len(row) > 2: st.info(f"時代：{row.iloc[2]}")
                st.markdown(f'<div class="sentence-box"><h3>問題：{q_text}</h3></div>', unsafe_allow_html=True)
                
                with st.form(key='jp_form_final', clear_on_submit=True):
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

            # --- 英単語・古文：選択肢モード ---
            else:
                if selected_subject == "英単語":
                    word = str(row['question'])
                    correct = str(row['all_answers'])
                    dummy_raw = str(row['dummy_pool'])
                    sentence = str(row['sentence'])
                    trans = str(row['translation'])
                else:
                    word, correct, dummy_raw = str(row.iloc[0]), str(row.iloc[1]), str(row.iloc[2])
                    sentence, trans = str(row.iloc[3]), str(row.iloc[4])

                # 例文の表示
                display_q = sentence.replace(word, f" **{word}** ") if (sentence and sentence.lower() != "nan") else f"単語： **{word}**"
                st.markdown(f'<div class="sentence-box"><p style="font-size:20px;">{display_q}</p></div>', unsafe_allow_html=True)

                if 'choices' not in st.session_state or st.session_state.idx != st.session_state.get('prev_idx'):
                    dummies = [d.strip() for d in dummy_raw.split(',') if d.strip()]
                    st.session_state.choices = random.sample([correct] + random.sample(dummies, min(len(dummies), 3)), min(len(dummies)+1, 4))
                    random.shuffle(st.session_state.choices)
                    st.session_state.prev_idx = st.session_state.idx

                for c in st.session_state.choices:
                    if st.button(c, use_container_width=True, disabled=st.session_state.answered):
                        st.session_state.answered = True
                        st.session_state.is_correct = (c == correct)
                        st.rerun()

                if st.session_state.answered:
                    if st.session_state.is_correct: st.success("✨ 正解！")
                    else: st.error(f"❌ 正解は 「{correct}」")
                    if trans and trans.lower() != "nan": st.info(f"💡 訳・解説: {trans}")
                    if st.button("次の問題へ 👉"):
                        st.session_state.idx += 1
                        st.session_state.answered = False
                        st.rerun()
        else:
            st.balloons()
            st.success("セクション全問終了！")
            if st.button("最初から"):
                st.session_state.idx = 0
                st.rerun()
else:
    st.info("サイドバーから学習したい科目を選択してください。")
