import streamlit as st
import pandas as pd
import random
import re

# ==================================================
# 基本設定
# ==================================================
st.set_page_config(
    page_title="文系科目は、ゆずれない",
    page_icon="🔥",
    layout="centered"
)

# ==================================================
# CSS（神デザイン版）
# ==================================================
st.markdown("""
<style>
.stApp{
    background: #f8f9fc;
}

h1,h2,h3,p,label,span{
    color:#111 !important;
}

.main-title{
    text-align:center;
    font-size:42px;
    font-weight:900;
    margin-bottom:10px;
}

.sub-title{
    text-align:center;
    color:#666;
    margin-bottom:25px;
}

.card{
    background:white;
    padding:28px;
    border-radius:20px;
    box-shadow:0 8px 20px rgba(0,0,0,0.07);
    margin-bottom:20px;
}

.red-left{
    border-left:10px solid #e53935;
}

.green-left{
    border-left:10px solid #2e7d32;
}

.blue-left{
    border-left:10px solid #1565c0;
}

.stButton button{
    width:100%;
    border-radius:12px;
    padding:14px;
    font-size:18px;
    font-weight:bold;
}

.correct{
    color:#2e7d32;
    font-weight:800;
    font-size:22px;
}

.wrong{
    color:#e53935;
    font-weight:800;
    font-size:22px;
}

.small{
    color:#666;
    font-size:14px;
}
</style>
""", unsafe_allow_html=True)

# ==================================================
# タイトル
# ==================================================
st.markdown('<div class="main-title">🔥 文系科目は、ゆずれない</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">英語・古文・日本史を制する者が受験を制す。</div>', unsafe_allow_html=True)

# ==================================================
# CSV読み込み
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
        st.error(f"CSV読み込みエラー: {e}")
        return None

# ==================================================
# 状態初期化
# ==================================================
def reset_state():
    for key in list(st.session_state.keys()):
        del st.session_state[key]

# ==================================================
# 問題初期化
# ==================================================
def setup_questions(df, subject):
    st.session_state.subject = subject
    st.session_state.df = df.sample(frac=1).reset_index(drop=True)
    st.session_state.idx = 0
    st.session_state.answered = False

# ==================================================
# 次へ
# ==================================================
def next_question():
    st.session_state.idx += 1
    st.session_state.answered = False

    for key in [
        "choices",
        "correct",
        "selected"
    ]:
        if key in st.session_state:
            del st.session_state[key]

# ==================================================
# サイドバー
# ==================================================
subject = st.sidebar.selectbox(
    "科目を選択",
    ["選択してください", "英単語", "古文単語", "日本史一問一答"]
)

# ==================================================
# メイン
# ==================================================
if subject == "選択してください":
    st.info("左のサイドバーから科目を選んでください。")
    st.stop()

df = load_csv(subject)

if df is None:
    st.stop()

# 初回 or 科目変更
if "subject" not in st.session_state or st.session_state.subject != subject:
    reset_state()
    setup_questions(df, subject)

df = st.session_state.df
idx = st.session_state.idx

# 終了判定
if idx >= len(df):
    st.balloons()
    st.success("全問終了！おつかれさま！")

    if st.button("もう一度最初から"):
        reset_state()
        setup_questions(df, subject)
        st.rerun()

    st.stop()

row = df.iloc[idx]

# 進捗バー
progress = (idx + 1) / len(df)
st.progress(progress)

st.markdown(f"### 第 {idx+1} 問 / {len(df)}")

# ==================================================
# 英単語
# ==================================================
if subject == "英単語":

    word = str(row["question"])
    answer = str(row["all_answers"])
    dummy = str(row["dummy_pool"])
    sentence = str(row["sentence"])
    trans = str(row["translation"])

    text = re.sub(
        re.escape(word),
        f"<span style='color:#e53935;font-weight:bold'>{word}</span>",
        sentence,
        flags=re.IGNORECASE
    )

    st.markdown(f'<div class="card red-left">{text}</div>', unsafe_allow_html=True)

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
            next_question()
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

    text = sentence.replace(
        word,
        f"<span style='color:#2e7d32;font-weight:bold'>{word}</span>"
    )

    st.markdown(f'<div class="card green-left">{text}</div>', unsafe_allow_html=True)

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
            next_question()
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

    st.markdown(f'<div class="card blue-left"><h3>{q}</h3></div>', unsafe_allow_html=True)

    if era:
        st.caption(f"時代：{era}")

    user = st.text_input("答えを入力（漢字）")

    if st.button("解答する"):

        user_clean = user.replace(" ", "").replace("　", "")
        ans_clean = ans.replace(" ", "").replace("　", "")

        if user_clean == ans_clean:
            st.success(f"✨ 正解！ {ans}")
        else:
            st.error(f"❌ 不正解　正解：{ans}")

        st.session_state.answered = True

    if st.session_state.answered:
        if st.button("次の問題へ"):
            next_question()
            st.rerun()
