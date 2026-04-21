import streamlit as st
import pandas as pd
import random
import re

# --- 1. 画面設定（視認性と色の統一） ---
st.set_page_config(page_title="文系科目は、ゆずれない", layout="centered")

st.markdown("""
    <style>
    /* 全体背景 */
    .stApp { background-color: white !important; color: black !important; }
    [data-testid="stSidebar"] { background-color: #f8f9fa !important; }
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p { color: black !important; }
    
    /* 共通の問題枠スタイル */
    .sentence-box {
        background-color: #f0f2f6 !important;
        color: black !important;
        padding: 25px;
        border-radius: 12px;
        margin-bottom: 25px;
        line-height: 1.6;
        border-left: 10px solid; /* 色は各科目で指定 */
    }
    
    /* ボタンが黒く潰れるのを防ぐ（枠線と文字をハッキリさせる） */
    .stButton button {
        color: black !important;
        background-color: white !important;
        border: 2px solid #ccc !important;
        font-weight: bold !important;
    }

    /* 【解決】日本史の「解答する」ボタンが潰れないように強制上書き */
    button[kind="primaryFormSubmit"] {
        background-color: #2e7d32 !important; /* 日本史は緑 */
        color: white !important;
        border: none !important;
        opacity: 1 !important;
    }
    
    /* ハイライト用 */
    .hl-red { color: #d32f2f !important; font-weight: bold; text-decoration: underline; }
    .hl-green { color: #2e7d32 !important; font-weight: bold; border-bottom: 2px solid #2e7d32; }
    
    h1, h2, h3, p, span { color: black !important; }
    </style>
    """, unsafe_allow_html=True)

# タイトル修正：ゆずらない → ゆずれない
st.title("🔥 文系科目は、ゆずれない")

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
        # レベル選択
        if selected_subject == "英単語":
            levels = ["All"] + sorted(raw_df['level'].unique().tolist(), key=lambda x: int(x) if str(x).isdigit() else 999)
            sel_level = st.sidebar.selectbox("レベルを選択", levels)
            current_df = raw_df if sel_level == "All" else raw_df[raw_df['level'] == sel_level]
            subject_color = "#d32f2f" # 英語は赤
        else:
            current_df, sel_level = raw_df, None
            subject_color = "#2e7d32" # 古文・日本史は緑

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

            # --- 日本史モード ---
            if selected_subject == "日本史一問一答":
                q_text, ans_text = str(row.iloc[0]), str(row.iloc[1]).strip()
                if len(row) > 2: st.info(f"時代：{row.iloc[2]}")
                st.markdown(f'<div class="sentence-box" style="border-left-color:{subject_color};"><h3>問題：{q_text}</h3></div>', unsafe_allow_html=True)
                with st.form(key='history_form'):
                    user_input = st.text_input("答えを入力（漢字）")
                    # primaryを指定してCSSを適用
                    if st.form_submit_button("解答する", type="primary"):
                        st.session_state.answered = True
                        st.session_state.user_ans = user_input.strip()
                
                if st.session_state.answered:
                    if st.session_state.user_ans == ans_text: st.success(f"✨ 正解！！ 「{ans_text}」")
                    else: st.error(f"❌ 不正解... 正解は 「{ans_text}」")
                    if st.button("次の問題へ 👉"):
                        st.session_state.idx += 1
                        st.session_state.answered = False
                        st.rerun()

            # --- 英単語・古文モード ---
            else:
                if selected_subject == "英単語":
                    word, correct = str(row['question']), str(row['all_answers'])
                    dummy_raw, sentence, trans = str(row['dummy_pool']), str(row['sentence']), str(row['translation'])
                    highlighted = re.sub(re.escape(word), f'<span class="hl-red">{word}</span>', sentence, flags=re.IGNORECASE) if (sentence and sentence != "nan") else f"単語：<span class=\"hl-red\">{word}</span>"
                else: # 古文
                    word, correct, dummy_raw = str(row.iloc[0]), str(row.iloc[1]), str(row.iloc[2])
                    sentence, trans = str(row.iloc[3]), str(row.iloc[4])
                    highlighted = sentence.replace(word, f'<span class="hl-green">{word}</span>') if (sentence and sentence != "nan") else f"古語：<span class=\"hl-green\">{word}</span>"

                st.markdown(f'<div class="sentence-box" style="border-left-color:{subject_color};"><p style="font-size:22px;">{highlighted}</p></div>', unsafe_allow_html=True)

                if 'choices' not in st.session_state or st.session_state.get('last_idx') != st.session_state.idx:
                    # 正解が長い場合の対策：カンマ区切りならランダムに1つ選ぶ
                    correct_list = [c.strip() for c in correct.split(',') if c.strip()]
                    display_correct = random.choice(correct_list)
                    dummies = [d.strip() for d in dummy_raw.split(',') if d.strip()]
                    pool = [display_correct] + random.sample(dummies, min(len(dummies), 3))
                    random.shuffle(pool)
                    st.session_state.choices, st.session_state.correct_answer, st.session_state.last_idx = pool, display_correct, st.session_state.idx

                for c in st.session_state.choices:
                    if st.button(c, use_container_width=True, disabled=st.session_state.answered):
                        st.session_state.answered, st.session_state.is_correct = True, (c == st.session_state.correct_answer)
                        st.rerun()

                if st.session_state.answered:
                    if st.session_state.is_correct: st.success("✨ 正解！")
                    else: st.error(f"❌ 正解は 「{st.session_state.correct_answer}」")
                    # 解説では全ての意味(correct)を表示
                    st.info(f"💡 意味一覧: {correct}\n\n📖 訳: {trans}")
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
