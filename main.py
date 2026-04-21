import streamlit as st
import pandas as pd
import random

# --- 1. 画面設定 ---
st.set_page_config(page_title="文系科目は、ゆずらない", layout="centered")
st.title("🔥 文系科目は、ゆずらない")

# --- 2. 科目選択 ---
# ここで選んだものによって、完全にルートを分けます
selected_subject = st.sidebar.selectbox(
    "学習する科目を選択",
    ["選択してください", "英単語", "古文単語", "日本史一問一答"]
)

if selected_subject == "選択してください":
    st.info("サイドバーから科目を選択してください。")
    st.stop()

# --- 3. データの読み込み（キャッシュを使用して混同を防止） ---
@st.cache_data
def load_specific_data(subject):
    try:
        if subject == "英単語":
            # 英語はヘッダーありと仮定
            df = pd.read_csv('final_tango_list.csv', encoding='utf-8-sig')
        elif subject == "古文単語":
            # 古文はヘッダーなし
            df = pd.read_csv('kobun350.csv', encoding='utf-8-sig', header=None)
        else:
            # 日本史はヘッダーなし
            df = pd.read_csv('nihonshi.csv', encoding='utf-8-sig', header=None)
        return df.sample(frac=1).reset_index(drop=True)
    except Exception as e:
        st.error(f"ファイル読み込みエラー ({subject}): {e}")
        return None

# セッションの初期化（科目が変わったら全リセット）
if 'current_sub' not in st.session_state or st.session_state.current_sub != selected_subject:
    st.session_state.current_sub = selected_subject
    st.session_state.q_df = load_specific_data(selected_subject)
    st.session_state.idx = 0
    st.session_state.answered = False
    st.session_state.score = 0

df = st.session_state.q_df
if df is None:
    st.stop()

# --- 4. クイズ本編（科目ごとに処理を完全に分ける） ---
row = df.iloc[st.session_state.idx]
st.subheader(f"【{selected_subject}】 第 {st.session_state.idx + 1} 問")

# --- 【日本史】 記述モード ---
if selected_subject == "日本史一問一答":
    # あなたの提示コードに合わせた列指定: 0列目=問題, 1列目=答え, 2列目=時代
    q_text = str(row.iloc[0])
    ans_text = str(row.iloc[1]).strip()
    
    if len(row) > 2:
        st.info(f"時代：{row.iloc[2]}")
    
    st.markdown(f'<div style="background-color:#f0f4f0; padding:20px; border-radius:10px; border-left:8px solid #2e7d32;"><h3>問題：{q_text}</h3></div>', unsafe_allow_html=True)
    
    with st.form(key='jp_history_form', clear_on_submit=True):
        user_input = st.text_input("答えを入力（漢字）")
        submit = st.form_submit_button("解答する")
    
    if submit or st.session_state.answered:
        st.session_state.answered = True
        if user_input.strip() == ans_text:
            st.success(f"✨ 正解！！ 「{ans_text}」")
        else:
            st.error(f"❌ 不正解... 正解は 「{ans_text}」")
        
        if st.button("次の問題へ 👉"):
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()

# --- 【英単語】 選択肢モード ---
elif selected_subject == "英単語":
    # 英語CSVの列名に合わせる（question, all_answers, dummy_pool, sentence, translation）
    # もし列名がなければ iloc[0], iloc[1]... に自動で切り替わります
    try:
        word = str(row['question'])
        correct = str(row['all_answers'])
        dummies = str(row['dummy_pool']).split(',')
        sentence = str(row['sentence'])
        trans = str(row['translation'])
    except:
        word, correct, dummy_raw, sentence, trans = row.iloc[0], row.iloc[1], row.iloc[2], row.iloc[3], row.iloc[4]
        dummies = str(dummy_raw).split(',')

    st.markdown(f'<div style="background-color:#f0f4f0; padding:20px; border-radius:10px; border-left:8px solid #007bff;"><h3>単語: {word}</h3><p>{sentence}</p></div>', unsafe_allow_html=True)
    
    if 'choices' not in st.session_state or st.session_state.idx != st.session_state.get('prev_idx'):
        c_list = [correct] + random.sample([d.strip() for d in dummies if d.strip()], min(len(dummies), 3))
        random.shuffle(c_list)
        st.session_state.choices = c_list
        st.session_state.prev_idx = st.session_state.idx

    for c in st.session_state.choices:
        if st.button(c, use_container_width=True, disabled=st.session_state.answered):
            st.session_state.answered = True
            st.session_state.is_correct = (c == correct)
            st.rerun()

    if st.session_state.answered:
        if st.session_state.is_correct: st.success("✨ 正解！")
        else: st.error(f"❌ 正解は 「{correct}」")
        st.info(f"意味: {trans}")
        if st.button("次の問題へ 👉"):
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()

# --- 【古文単語】 選択肢モード ---
elif selected_subject == "古文単語":
    # 古文はヘッダーなし: 0=単語, 1=正解, 2=ダミー, 3=例文, 4=訳
    word, correct, dummy_raw, sentence, trans = row.iloc[0], row.iloc[1], row.iloc[2], row.iloc[3], row.iloc[4]
    dummies = str(dummy_raw).split(',')

    st.markdown(f'<div style="background-color:#f0f4f0; padding:20px; border-radius:10px; border-left:8px solid #d32f2f;"><h3>古文: {word}</h3><p>{sentence}</p></div>', unsafe_allow_html=True)
    
    if 'choices' not in st.session_state or st.session_state.idx != st.session_state.get('prev_idx'):
        c_list = [correct] + random.sample([d.strip() for d in dummies if d.strip()], min(len(dummies), 3))
        random.shuffle(c_list)
        st.session_state.choices = c_list
        st.session_state.prev_idx = st.session_state.idx

    for c in st.session_state.choices:
        if st.button(c, use_container_width=True, disabled=st.session_state.answered):
            st.session_state.answered = True
            st.session_state.is_correct = (c == correct)
            st.rerun()

    if st.session_state.answered:
        if st.session_state.is_correct: st.success("✨ 正解！")
        else: st.error(f"❌ 正解は 「{correct}」")
        st.info(f"現代語訳: {trans}")
        if st.button("次の問題へ 👉"):
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()

# 終了判定
if st.session_state.idx >= len(df):
    st.balloons()
    st.success("セクション全問終了！")
    if st.button("最初から解く"):
        st.session_state.idx = 0
        st.session_state.q_df = load_specific_data(selected_subject)
        st.rerun()
