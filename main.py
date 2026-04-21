import streamlit as st
import pandas as pd
import random
import re

# ==================================================
# 基本設定（スマホ / iPad対応）
# ==================================================
st.set_page_config(
    page_title="文系科目は、ゆずれない",
    page_icon="🔥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==================================================
# CSS（レスポンシブ対応）
# ==================================================
st.markdown("""
<style>

/* 全体 */
.stApp{
    background:#f7f8fc;
}

/* 横幅 */
.block-container{
    max-width:700px;
    padding-top:1rem;
    padding-bottom:3rem;
    padding-left:1rem;
    padding-right:1rem;
}

/* タイトル */
.main-title{
    text-align:center;
    font-size:2.1rem;
    font-weight:900;
    margin-bottom:0.2rem;
}

.sub-title{
    text-align:center;
    color:#666;
    font-size:0.95rem;
    margin-bottom:1.2rem;
}

/* カード */
.card{
    background:white;
    padding:22px;
    border-radius:18px;
    box-shadow:0 8px 20px rgba(0,0,0,0.06);
    margin-bottom:1rem;
    line-height:1.7;
    font-size:1.08rem;
    color:#111;
}

.red{border-left:8px solid #e53935;}
.green{border-left:8px solid #2e7d32;}
.blue{border-left:8px solid #1565c0;}

/* ボタン */
.stButton button{
    width:100%;
    border-radius:14px;
    padding:0.8rem;
    font-size:1rem;
    font-weight:700;
}

/* 入力欄 */
.stTextInput input{
    font-size:1rem;
}

/* スマホ */
@media (max-width: 768px){

.main-title{
    font-size:1.6rem;
}

.sub-title{
    font-size:0.82rem;
}

.card{
    padding:16px;
    font-size:1rem;
}

.stButton button{
    padding:0.75rem;
    font-size:0.95rem;
}

}

</style>
""", unsafe_allow_html=True)

# ==================================================
# タイトル
# ==================================================
st.markdown('<div class="main-title">🔥 文系科目は、ゆずれない</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">スマホ・iPad対応 学習ツール</div>', unsafe_allow_html=True)

# ==================================================
# データ読込
# ==================================================
@st.cache_data
def load_csv(subject):
    files = {
        "英単語": "final_tango_list.csv",
        "古文単語": "kobun350.csv",
        "日本史一問一答": "nihonshi.csv"
    }

    try:
        if subject == "英単語":
            return pd.read_csv(files[subject], encoding="utf-8-sig")
        else:
            return pd.read_csv(files[subject], encoding="utf-8-sig", header=None)
    except Exception as e:
        st.error(f"CSV読み込み失敗: {e}")
        return None

# ==================================================
# 状態管理
# ==================================================
def clear_state():
    for key in list(st.session_state.keys()):
        del st.session_state[key]

def start_subject(df, subject):
    st.session_state.subject = subject
    st.session_state.df = df.sample(frac=1).reset_index(drop=True)
    st.session_state.idx = 0
    st.session_state.answered = False

def next_q():
    st.session_state.idx += 1
    st.session_state.answered = False

    for key in ["choices", "correct", "selected"]:
        if key in st.session_state:
            del st.session_state[key]

# ==================================================
# 科目選択
# ==================================================
subject = st.selectbox(
    "学習する科目を選択",
    ["選択してください", "英単語", "古文単語", "日本史一問一答"]
)

if subject == "選択してください":
    st.info("科目を選んでください。")
    st.stop()

df = load_csv(subject)

if df is None:
    st.stop()

# 科目変更
if "subject" not in st.session_state or st.session_state.subject != subject:
    clear_state()
    start_subject(df, subject)

df = st.session_state.df
idx = st.session_state.idx

# 終了
if idx >= len(df):
    st.balloons()
    st.success("全問終了！")

    if st.button("もう一度やる"):
        clear_state()
        start_subject(df, subject)
        st.rerun()

    st.stop()

row = df.iloc[idx]

# 進捗
st.progress((idx + 1) / len(df))
st.caption(f"{idx+1} / {len(df)} 問")

# ==================================================
# 英単語
# ==================================================
if subject == "英単語":

    word = str(row["question"])
    answer = str(row["all_answers"])
    dummy = str(row["dummy_pool"])
    sentence = str(row["sentence"])
    trans = str(row["translation"])

    sentence = re.sub(
        re.escape(word),
        f"<span style='color:#e53935;font-weight:bold'>{word}</span>",
        sentence,
        flags=re.IGNORECASE
    )

    st.markdown(f'<div class="card red">{sentence}</div>', unsafe_allow_html=True)

    if "choices" not in st.session_state:
        correct = random.choice([x.strip() for x in answer.split(",")])
        dummies = [x.strip() for x in dummy.split(",") if x.strip()]
        choices = [correct] + random.sample(dummies, min(3, len(dummies)))
        random.shuffle(choices)

        st.session_state.choices = choices
        st.session_state.correct = correct

    for c in st.session_state.choices:
        if st.button(c, disabled=st.session_state.answered):
            st.session_state.selected = c
            st.session_state.answered = True
            st.rerun()

    if st.session_state.answered:

        if st.session_state.selected == st.session_state.correct:
            st.success("✨ 正解！")
        else:
            st.error(f"❌ 正解：{st.session_state.correct}")

        st.info(f"意味一覧：{answer}\n\n訳：{trans}")

        if st.button("次の問題へ"):
            next_q()
            st.rerun()

# ==================================================
# 古文
# ==================================================
elif subject == "古文単語":

    word = str(row.iloc[0])
    answer = str(row.iloc[1])
    dummy = str(row.iloc[2])
    sentence = str(row.iloc[3])
    trans = str(row.iloc[4])

    sentence = sentence.replace(
        word,
        f"<span style='color:#2e7d32;font-weight:bold'>{word}</span>"
    )

    st.markdown(f'<div class="card green">{sentence}</div>', unsafe_allow_html=True)

    if "choices" not in st.session_state:
        dummies = [x.strip() for x in dummy.split(",") if x.strip()]
        choices = [answer] + random.sample(dummies, min(3, len(dummies)))
        random.shuffle(choices)

        st.session_state.choices = choices
        st.session_state.correct = answer

    for c in st.session_state.choices:
        if st.button(c, disabled=st.session_state.answered):
            st.session_state.selected = c
            st.session_state.answered = True
            st.rerun()

    if st.session_state.answered:

        if st.session_state.selected == st.session_state.correct:
            st.success("✨ 正解！")
        else:
            st.error(f"❌ 正解：{st.session_state.correct}")

        st.info(f"訳：{trans}")

        if st.button("次の問題へ"):
            next_q()
            st.rerun()

# ==================================================
# 日本史
# ==================================================
else:

    q = str(row.iloc[0])
    ans = str(row.iloc[1]).strip()

    era = ""
    if len(row) >= 3:
        era = str(row.iloc[2])

    st.markdown(f'<div class="card blue"><b>{q}</b></div>', unsafe_allow_html=True)

    if era:
        st.caption(f"時代：{era}")

    user = st.text_input("答えを入力（漢字）")

    if st.button("解答する"):

        user_clean = user.replace(" ", "").replace("　", "")
        ans_clean = ans.replace(" ", "").replace("　", "")

        if user_clean == ans_clean:
            st.success("✨ 正解！")
        else:
            st.error(f"❌ 正解：{ans}")

        st.session_state.answered = True

    if st.session_state.answered:
        if st.button("次の問題へ"):
            next_q()
            st.rerun()
