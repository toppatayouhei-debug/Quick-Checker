import streamlit as st
import pandas as pd
import random

# --- 1. 画面設定（白背景・黒文字を強制） ---
st.set_page_config(page_title="文系科目は、ゆずらない", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: white !important; color: black !important; }
    .sentence-box {
        background-color: #f0f2f6 !important;
        color: black !important;
        padding: 25px;
        border-radius: 10px;
        border-left: 8px solid #2e7d32;
        margin-bottom: 20px;
    }
    .stButton button { color: black !important; font-size: 16px !important; min-height: 3.5em; }
    h1, h2, h3, p, span, div { color: black !important; }
    /* サイドバー内の文字色調整 */
    section[data-testid="stSidebar"] .stSelectbox label p { color: black !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔥 文系科目は、ゆずらない")

# --- 2. 科目選択 ---
selected_subject = st.sidebar.selectbox(
    "学習する科目を選択",
    ["選択してください", "英単語", "古文単語", "日本史一問一答"]
)

if selected_subject == "選択してください":
    st.info("サイドバーから科目を選択してください。")
    st.stop()

# --- 3. データの読み込み ---
@st.cache_data
def load_raw_data(subject):
    files = {"英単語": "final_tango_list.csv", "古文単語": "kobun350.csv", "日本史一問一答": "nihonshi.csv"}
    try:
        # 英単語はレベル分けがあるのでヘッダーありで読み込み
        if subject == "英単語":
            df = pd.read_csv(files[subject], encoding='utf-8-sig')
        else:
            df = pd.read_csv(files[subject], encoding='utf-8-sig', header=None)
        return df
    except Exception as e:
        st.error(f"ファイルが読み込めません: {e}")
        return None

# データロード
raw_df = load_raw_data(selected_subject)
if raw_df is None: st.stop()

# --- 4. 【英単語専用】レベル選択ロジック ---
current_df = raw_df
if selected_subject == "英単語":
    if 'level' in raw_df.columns:
        levels = ["All"] + sorted(raw_df['level'].unique().tolist())
        sel_level = st.sidebar.selectbox("レベルを選択", levels)
        if sel_level != "All":
            current_df = raw_df[raw_df['level'] == sel_level]

# 科目やレベルが変わったらリセット
state_key = f"{selected_subject}_{st.sidebar.get_option('英単語' if selected_subject=='英単語' else '')}" # 簡易キー
if 'last_sub_state' not in st.session_state or st.session_state.last_sub_state != selected_subject + str(current_df.shape[0]):
    st.session_state.last_sub_state = selected_subject + str(current_df.shape[0])
    st.session_state.q_df = current_df.sample(frac=1).reset_index(drop=True)
    st.session_state.idx = 0
    st.session_state.answered = False

df = st.session_state.q_df

# --- 5. クイズ表示 ---
if st.session_state.idx < len(df):
    row = df.iloc[st.session_state.idx]
    st.subheader(f"【{selected_subject}】 第 {st.session_state.idx + 1} 問")

    # --- 日本史一問一答 ---
    if selected_subject == "日本史一問一答":
        q_text, ans_text = str(row.iloc[0]), str(row.iloc[1]).strip()
        if len(row) > 2: st.info(f"時代：{row.iloc[2]}")
        st.markdown(f'<div class="sentence-box"><h3>問題：{q_text}</h3></div>', unsafe_allow_html=True)
        with st.form(key='jp_form', clear_on_submit=True):
            user_input = st.text_input("答えを入力（漢字）")
            if st.form_submit_button("解答する"):
                st.session_state.answered = True
                st.session_state.user_ans = user_input.strip()
        
        if st.session_state.answered:
            if st.session_state.user_ans == ans_text: st.success(f"✨ 正解！！ 「{ans_text}」")
            else: st.error(f"❌ 不正解... 正解は 「{ans_text}」")
            if st.button("次の問題へ"):
                st.session_state.idx += 1
                st.session_state.answered = False
                st.rerun()

    # --- 英単語・古文単語 ---
    else:
        # 英単語(ヘッダーあり)か古文(ヘッダーなし)かで取得方法を分岐
        if selected_subject == "英単語":
            word, correct, dummy_raw = str(row['question']), str(row['all_answers']), str(row['dummy_pool'])
            sentence, trans = str(row['sentence']), str(row['translation'])
        else:
            word, correct, dummy_raw = str(row.iloc[0]), str(row.iloc[1]), str(row.iloc[2])
            sentence, trans = str(row.iloc[3]), str(row.iloc[4])

        # 例文表示
        display_q = sentence.replace(word, f" **{word}** ") if (sentence and sentence.lower() != "nan") else f"単語の意味： **{word}**"
        st.markdown(f'<div class="sentence-box"><p style="font-size:20px;">{display_q}</p></div>', unsafe_allow_html=True)

        # 選択肢
        if 'choices' not in st.session_state or st.session_state.idx != st.session_state.get('prev_idx'):
            dummies = [d.strip() for d in dummy_raw.split(',') if d.strip()]
            st.session_state.choices = random.sample([correct] + random.sample(dummies, min(len(dummies), 3)), 
                                                     min(len(dummies)+1, 4))
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
            if st.button("次の問題へ"):
                st.session_state.idx += 1
                st.session_state.answered = False
                st.rerun()

else:
    st.balloons()
    st.success("全問終了！")
    if st.button("もう一度最初から"):
        st.session_state.idx = 0
        st.session_state.answered = False
        st.rerun()
