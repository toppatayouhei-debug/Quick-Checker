import streamlit as st
import pandas as pd
import random
import re

# --- 1. 画面設定（絶対視認性） ---
st.set_page_config(page_title="文系科目は、ゆずれない", layout="centered")

st.markdown("""
    <style>
    /* どんな環境でも白背景・黒文字を死守 */
    .stApp { background-color: white !important; color: black !important; }
    [data-testid="stSidebar"] { background-color: #f8f9fa !important; }
    [data-testid="stSidebar"] * { color: black !important; }
    
    .sentence-box {
        background-color: #f0f2f6 !important;
        color: black !important;
        padding: 25px;
        border-radius: 12px;
        margin-bottom: 25px;
        border-left: 10px solid;
    }
    
    /* ボタンの文字色 */
    .stButton button {
        color: black !important;
        background-color: white !important;
        border: 2px solid #ccc !important;
    }
    
    /* 日本史解答ボタンを緑に */
    button[kind="primaryFormSubmit"] {
        background-color: #2e7d32 !important;
        color: white !important;
        border: none !important;
    }
    
    /* ハイライト */
    .hl-red { color: #d32f2f !important; font-weight: bold; text-decoration: underline; }
    .hl-green { color: #2e7d32 !important; font-weight: bold; border-bottom: 2px solid #2e7d32; }
    
    h1, h2, h3, p, span, div { color: black !important; }
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
            df = pd.read_csv(files[subject], encoding='utf-8-sig')
        else:
            # 1行目が「単語,意味...」という見出しならheader=0, なければNone
            df = pd.read_csv(files[subject], encoding='utf-8-sig', header=None)
            # もし1行目が文字（見出し）なら飛ばす
            if "単語" in str(df.iloc[0,0]) or "question" in str(df.iloc[0,0]):
                df = df.iloc[1:].reset_index(drop=True)
        return df
    except:
        return None

# --- 3. メインロジック ---
if selected_subject != "選択してください":
    raw_df = load_raw_data(selected_subject)
    if raw_df is not None:
        if selected_subject == "英単語":
            levels = ["All"] + sorted(raw_df['level'].unique().tolist(), key=lambda x: int(x) if str(x).isdigit() else 999)
            sel_level = st.sidebar.selectbox("レベルを選択", levels)
            current_df = raw_df if sel_level == "All" else raw_df[raw_df['level'] == sel_level]
            sub_color = "#d32f2f"
        else:
            current_df, sel_level = raw_df, None
            sub_color = "#2e7d32"

        # 科目変更時に選択肢を完全にクリア
        if st.session_state.get('active_sub') != selected_subject:
            st.session_state.active_sub = selected_subject
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
                if len(row) > 2: st.info(f"時代：{row.iloc[2]}")
                st.markdown(f'<div class="sentence-box" style="border-left-color:{sub_color};"><h3>問題：{q}</h3></div>', unsafe_allow_html=True)
                with st.form(key='hist_form'):
                    u_in = st.text_input("答え（漢字）")
                    if st.form_submit_button("解答する", type="primary"):
                        st.session_state.answered, st.session_state.u_ans = True, u_in.strip()
                if st.session_state.answered:
                    if st.session_state.u_ans == ans: st.success(f"✨ 正解！ 「{ans}」")
                    else: st.error(f"❌ 正解は 「{ans}」")
                    if st.button("次へ 👉"):
                        st.session_state.idx += 1
                        st.session_state.answered = False
                        st.rerun()

            # --- 英単語・古文 ---
            else:
                if selected_subject == "英単語":
                    word, correct = str(row['question']), str(row['all_answers'])
                    dummy_raw, sentence, trans = str(row['dummy_pool']), str(row['sentence']), str(row['translation'])
                    hl_class = "hl-red"
                else:
                    # 0:単語, 1:意味, 2:ダミー, 3:例文, 4:現代語訳
                    word, correct, dummy_raw = str(row.iloc[0]), str(row.iloc[1]), str(row.iloc[2])
                    sentence = str(row.iloc[3]) if len(row) > 3 else ""
                    trans = str(row.iloc[4]) if len(row) > 4 else ""
                    hl_class = "hl-green"

                # 例文が「sentence」や空の場合は単語のみ表示
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
            st.success("終了！")
            if st.button("最初から"):
                st.session_state.idx = 0
                st.rerun()
