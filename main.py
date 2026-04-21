import streamlit as st
import pandas as pd
import random
import re

# --- 1. 画面設定（サイドバー：水色 / メイン：極淡ピンク） ---
st.set_page_config(page_title="文系科目は、ゆずれない", layout="centered")

st.markdown("""
    <style>
    /* メイン背景：さらに淡いサクラ色 */
    .stApp {
        background-color: #FFF9FB !important;
    }
    
    /* サイドバー：爽やかな水色 */
    [data-testid="stSidebar"], 
    [data-testid="stSidebarContent"],
    [data-testid="stSidebarNav"] {
        background-color: #E0F7FA !important; /* パステル水色 */
        background: #E0F7FA !important;
    }

    /* テキストはすべて「黒」 */
    .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp span, .stApp div, .stApp label,
    [data-testid="stSidebar"] * {
        color: #000000 !important;
    }

    /* 問題文ボックス */
    .sentence-box {
        background-color: #FFFFFF !important; 
        color: #000000 !important;
        padding: 22px;
        border-radius: 12px;
        margin-bottom: 20px;
        border: 1px solid #E0E0E0;
        border-left: 10px solid;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.05);
    }

    /* 選択肢ボタン */
    .stButton button {
        color: #000000 !important;
        background-color: #FFFFFF !important;
        border: 2px solid #000000 !important;
        font-weight: bold !important;
    }
    
    /* 日本史解答ボタン */
    button[kind="primaryFormSubmit"] {
        background-color: #00796B !important; /* 水色に合う深緑 */
        color: #FFFFFF !important;
        border: none !important;
    }

    /* ハイライト（font-weightを最大化し、!importantで強制適用） */
    .hl-red { color: #D32F2F !important; font-weight: 900 !important; text-decoration: underline !important; }
    .hl-green { color: #1B5E20 !important; font-weight: 900 !important; border-bottom: 3px solid #1B5E20 !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔥 文系科目は、ゆずれない")

# --- 2. データ読み込み ---
@st.cache_data
def load_raw_data(subject):
    files = {"英単語": "final_tango_list.csv", "古文単語": "kobun350.csv", "日本史一問一答": "nihonshi.csv"}
    try:
        if subject == "英単語":
            return pd.read_csv(files[subject], encoding='utf-8-sig')
        else:
            df = pd.read_csv(files[subject], encoding='utf-8-sig', header=None)
            if "単語" in str(df.iloc[0,0]) or "question" in str(df.iloc[0,0]):
                df = df.iloc[1:].reset_index(drop=True)
            return df
    except: return None

selected_subject = st.sidebar.selectbox("学習する科目を選択", ["選択してください", "英単語", "古文単語", "日本史一問一答"])

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
            sub_color = "#00796B"

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
            else:
                if selected_subject == "英単語":
                    word = str(row['question']).strip()
                    correct = str(row['all_answers']).strip()
                    dummy_raw, sentence, trans = str(row['dummy_pool']), str(row['sentence']), str(row['translation'])
                    hl_class = "hl-red"
                    sel_correct = random.choice([c.strip() for c in correct.split(',') if c.strip()])
                else:
                    word = str(row.iloc[0]).strip()
                    correct = str(row.iloc[1]).strip()
                    dummy_raw = str(row.iloc[2])
                    sentence, trans = str(row.iloc[3]), str(row.iloc[4])
                    hl_class = "hl-green"
                    # 先頭の意味を正解に
                    sel_correct = [c.strip() for c in correct.split(',') if c.strip()][0]

                # --- ハイライトロジックの改善 ---
                if not sentence or sentence.lower() in ["nan", "sentence", ""]:
                    disp = f"この単語の意味は？： <span class='{hl_class}'>{word}</span>"
                else:
                    # 1. まず単語そのものを置換
                    disp = re.sub(re.escape(word), f'<span class="{hl_class}">{word}</span>', sentence, flags=re.IGNORECASE)
                    # 2. もし置換されなかった場合（活用形など）、単語の頭数文字で再トライ
                    if f'class="{hl_class}"' not in disp and len(word) > 1:
                        short_word = word[:-1] # 最後の1文字（送り仮名）を削って検索
                        disp = re.sub(re.escape(short_word), f'<span class="{hl_class}">{short_word}</span>', sentence, flags=re.IGNORECASE)

                st.markdown(f'<div class="sentence-box" style="border-left-color:{sub_color};"><p style="font-size:22px;">{disp}</p></div>', unsafe_allow_html=True)

                if 'choices' not in st.session_state or st.session_state.get('last_idx') != st.session_state.idx:
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
                    st.info(f"💡 意味一覧: {correct}\n\n📖 訳: {trans}")
                    if st.button("次へ 👉"):
                        st.session_state.idx += 1
                        st.session_state.answered = False
                        st.rerun()
        else:
            st.balloons()
            if st.button("全問終了！最初から"):
                st.session_state.idx = 0
                st.rerun()
