import streamlit as st
import pandas as pd
import random

# --- 1. 画面設定 ---
st.set_page_config(page_title="文系科目は、ゆずらない", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #fdfaf5; }
    .sentence-box { background-color: #f0f4f0; padding: 25px; border-radius: 10px; border-left: 8px solid #2e7d32; margin-bottom: 20px; }
    .stButton button { font-size: 16px !important; min-height: 3.5em; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔥 文系科目は、ゆずらない")

# --- 2. 科目選択 ---
selected_subject = st.sidebar.selectbox(
    "学習する科目を選択",
    ["選択してください", "英単語", "古文単語", "日本史一問一答"]
)

# --- 3. セッション状態の初期化 ---
if 'sub' not in st.session_state or st.session_state.sub != selected_subject:
    st.session_state.sub = selected_subject
    st.session_state.idx = 0
    st.session_state.score = 0
    st.session_state.answered = False
    st.session_state.q_df = None

if selected_subject == "選択してください":
    st.info("サイドバーから科目を選択してください。")
    st.stop()

# --- 4. データロード（科目ごとに最適化） ---
@st.cache_data
def load_subject_data(subject):
    files = {"英単語": "final_tango_list.csv", "古文単語": "kobun350.csv", "日本史一問一答": "nihonshi.csv"}
    try:
        # 英語だけはヘッダーあり(level, question等)、他はヘッダーなし
        if subject == "英単語":
            df = pd.read_csv(files[subject], encoding='utf-8-sig')
        else:
            df = pd.read_csv(files[subject], encoding='utf-8-sig', header=None)
        return df.sample(frac=1).reset_index(drop=True)
    except:
        return None

if st.session_state.q_df is None:
    st.session_state.q_df = load_subject_data(selected_subject)

df = st.session_state.q_df
if df is None:
    st.error(f"ファイルが見つかりません: {selected_subject}")
    st.stop()

# --- 5. 学習モード ---

# A: 【日本史】記述入力モード
if selected_subject == "日本史一問一答":
    row = df.iloc[st.session_state.idx]
    q_text = str(row[0]) # 1列目: 問題
    ans_text = str(row[1]).strip() # 2列目: 答え
    
    st.subheader(f"第 {st.session_state.idx + 1} 問")
    if len(row) >= 3: st.info(f"時代：{row[2]}")
    st.markdown(f'<div class="sentence-box"><h3>問題：{q_text}</h3></div>', unsafe_allow_html=True)
    
    with st.form(key='history_form', clear_on_submit=True):
        user_input = st.text_input("答えを漢字で入力")
        submit = st.form_submit_button("解答する")
    
    if submit or st.session_state.answered:
        st.session_state.answered = True
        if user_input.strip() == ans_text:
            st.success(f"✨ 正解！ 「{ans_text}」")
        else:
            st.error(f"❌ 残念！ 正解は 「{ans_text}」")
        
        if st.button("次の問題へ"):
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()

# B: 【英単語・古文】選択肢モード
else:
    row = df.iloc[st.session_state.idx]
    
    # データの割り当てを整理
    if selected_subject == "英単語":
        word = str(row['question'])
        correct = str(row['all_answers'])
        dummies = str(row['dummy_pool']).split(',')
        sentence = str(row['sentence'])
        translation = str(row['translation'])
    else: # 古文
        word = str(row[0])
        correct = str(row[1])
        dummies = str(row[2]).split(',')
        sentence = str(row[3])
        translation = str(row[4])

    st.subheader(f"第 {st.session_state.idx + 1} 問")
    
    # 問題文の表示
    display_q = sentence.replace(word, f" **【 {word} 】** ") if word in sentence else f"{sentence}\n\n(単語: {word})"
    st.markdown(f'<div class="sentence-box"><p style="font-size:20px;">{display_q}</p></div>', unsafe_allow_html=True)

    # 選択肢の生成
    if 'choices' not in st.session_state or st.session_state.new_q:
        c_list = [correct] + random.sample([d.strip() for d in dummies if d.strip()], min(len(dummies), 3))
        random.shuffle(c_list)
        st.session_state.choices = c_list
        st.session_state.new_q = False

    for c in st.session_state.choices:
        if st.button(c, use_container_width=True, disabled=st.session_state.answered):
            st.session_state.answered = True
            st.session_state.is_correct = (c == correct)
            st.rerun()

    if st.session_state.answered:
        if st.session_state.is_correct: st.success("✨ 正解！")
        else: st.error(f"❌ 不正解... 正解は「{correct}」")
        
        st.info(f"💡 訳・解説: {translation}")
        if st.button("次の問題へ"):
            st.session_state.idx += 1
            st.session_state.answered = False
            st.session_state.new_q = True
            st.rerun()

# --- 6. 終了判定 ---
if st.session_state.idx >= len(df):
    st.balloons()
    st.success("全問終了！お疲れ様でした！")
    if st.button("最初からやり直す"):
        st.session_state.idx = 0
        st.session_state.q_df = None
        st.rerun()
