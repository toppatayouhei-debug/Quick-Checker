import streamlit as st
import pandas as pd
import random
import re

# --- 1. 画面設定（すべての黒塗りを排除し、白地・黒文字を強制） ---
st.set_page_config(page_title="文系科目は、ゆずれない", layout="centered")

st.markdown("""
    <style>
    /* 1. メインエリアを強制的に白背景・黒文字にする */
    .stApp {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    
    /* 2. サイドバーの黒塗りを完全に排除し、白背景にする */
    [data-testid="stSidebar"], 
    [data-testid="stSidebar"] > div:first-child,
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
    }

    /* 3. サイドバー内のすべてのテキスト・ラベルを漆黒にする */
    [data-testid="stSidebar"] .stSelectbox label p,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] .stMarkdown {
        color: #000000 !important;
        font-weight: 600 !important;
    }

    /* 4. 入力フォームやセレクトボックスの背景が沈まないように調整 */
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #CCCCCC !important;
    }

    /* 5. 問題文ボックス */
    .sentence-box {
        background-color: #F0F2F6 !important;
        color: #000000 !important;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        border: 1px solid #DDDDDD;
        border-left: 10px solid;
    }

    /* 6. ボタン：黒枠で白背景、文字は黒 */
    .stButton button {
        color: #000000 !important;
        background-color: #FFFFFF !important;
        border: 2px solid #000000 !important;
        font-weight: bold !important;
    }
    
    /* 7. 日本史の解答ボタン（ここだけは緑で目立たせる） */
    button[kind="primaryFormSubmit"] {
        background-color: #2E7D32 !important;
        color: #FFFFFF !important;
        border: none !important;
    }

    /* 8. ハイライト */
    .hl-red { color: #D32F2F !important; font-weight: bold; text-decoration: underline; }
    .hl-green { color: #2E7D32 !important; font-weight: bold; border-bottom: 2px solid #2E7D32; }
    
    /* 9. すべての見出し・テキストを黒に */
    h1, h2, h3, p, span, div, label { color: #000000 !important; }
    </style>
    """, unsafe_allow_html=True)

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
            df = pd.read_csv(files[subject], encoding='utf-8-sig', header=None)
            # 見出し行飛ばし
            if "単語" in str(df.iloc[0,0]) or "question" in str(df.iloc[0,0]):
                df = df.iloc[1:].reset_index(drop=True)
            return df
    except: return None

# --- 3. メインロジック ---
if selected_subject != "選択してください":
    raw_df = load_raw_data(selected_subject)
    if raw_df is not None:
        if selected_subject == "英単語":
            levels = ["All"] + sorted(raw_df['level'].unique().tolist(), key=lambda x: int(x) if str(x).isdigit() else 999)
            sel_level = st.sidebar.selectbox("レベルを選択", levels)
            current_df = raw_df if sel_level == "All" else raw_df[raw_df['level'] == sel_level]
            sub_color = "#D32F2F"
        else:
            current_df, sel_level = raw_df, None
            sub_color = "#2E7D32"

        # 科目/レベル変更時のリセット
        if st.session_state.get('active_sub') != selected_subject or st.session_state.get('active_level') != sel_level:
            st.session_state.active_sub = selected_subject
            st.session_state.active_level = sel_level
            st.session_state.idx = 0
            st.session_state.answered = False
            st.session_state.q_df = current_df.sample(frac=1).reset_index(drop=True)
            if 'choices' in st.session_state: del st.session_state.choices

        df = st.session_state.q_df
        if st.session_state.idx < len(df):
            row = df.iloc[st.session_state.idx]
            st.subheader(f"【{selected_subject}】 第 {st.session_state.idx + 1} 問")

            # --- 日本史 ---
            if selected_subject == "日本史一問一答":
                q, ans = str(row.iloc[0]), str(row.iloc[1]).strip()
                st.markdown(f'<div class="sentence-box" style="border-left-color:{sub_color};"><h3>問題：{q}</h3></div>', unsafe_allow_html=True)
                with st.form(key='hist_form'):
                    u_in = st.text_input("答えを入力（漢字）")
                    if st.form_submit_button("解答する", type="primary"):
                        st.session_state.answered, st.session_state.u_ans = True, u_in.strip()
                if st.session_state.answered:
                    if st.session_state.u_ans == ans: st.success(f"✨ 正解！ 「{ans}」")
                    else: st.error(f"❌ 正解は 「{ans}」")
                    if st.button("次へ 👉"):
                        st.session_state.idx += 1
                        st.session_state.answered = False
                        st.rerun()

            # --- 英語・古文 ---
            else:
                if selected_subject == "英単語":
                    word, correct = str(row['question']), str(row['all_answers'])
                    dummy_raw, sentence, trans = str(row['dummy_pool']), str(row['sentence']), str(row['translation'])
                    hl_class = "hl-red"
                else:
                    word, correct, dummy_raw = str(row.iloc[0]), str(row.iloc[1]), str(row.iloc[2])
                    sentence = str(row.iloc[3]) if len(row) > 3 else ""
                    trans = str(row.iloc[4]) if len(row) > 4 else ""
                    hl_class = "hl-green"

                if not sentence or sentence.lower() in ["nan", "sentence", ""]:
                    disp = f"この単語の意味は？： <span class='{hl_class}'>{word}</span>"
                else:
                    disp = re.sub(re.escape(word), f'<span class="{hl_class}">{word}</span>', sentence, flags=re.IGNORECASE)

                st.markdown(f'<div class="sentence-box" style="border-left-color:{sub_color};"><p style="font-size:22px;">{disp}</p></div>', unsafe_allow_html=True)

                if 'choices' not in st.session_state or st.session_state.get('last_idx') != st.session_state.idx:
                    c_list = [c.strip() for c in correct.split(',') if c.strip()]
                    sel_correct = random.choice(c_list)
                    dummies = [d.strip() for d in str(dummy_raw).split(',') if d.strip()]
                    pool = [sel_correct] + random.sample(dummies, min(len(dummies), 3))
                    random.shuffle(pool)
                    st.session_state.choices, st.session_state.ans_val, st.session_state.last_idx = pool, sel_correct, st.session_state.idx

                for c in st.session_state.choices:
                    if st.button(c, use_container_width=True, disabled=st.session_state.answered):
                        st.session_state.answered, st.session_state.is_cor = True, (c == st.session_state.ans_val)
                        st.rerun()

                if st.session_state.answered:
                    if st.session_state.is_cor: st.success("✨ 正解！")
                    else: st.error(f"❌ 正解は 「{st.session_state.ans_val}」")
                    st.info(f"💡 意味: {correct}\n\n📖 訳: {trans}")
                    if st.button("次へ 👉"):
                        st.session_state.idx += 1
                        st.session_state.answered = False
                        st.rerun()
        else:
            st.balloons()
            if st.button("最初から"):
                st.session_state.idx = 0
                st.rerun()
