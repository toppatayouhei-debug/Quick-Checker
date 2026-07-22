import streamlit as st
import pandas as pd
import random
import re

# --- ページ設定 ---
st.set_page_config(page_title="共通テスト・漢字・古文・漢文 学習アプリ", layout="centered")

# カスタムCSS（カードデザインなど）
st.markdown("""
<style>
.card {
    padding: 20px;
    border-radius: 10px;
    margin-bottom: 20px;
    font-size: 1.1rem;
    line-height: 1.6;
}
.red-card {
    background-color: #ffebee;
    border-left: 5px solid #ef5350;
    color: #b71c1c;
}
.exp-card {
    background-color: #f1f8e9;
    border-left: 5px solid #81c784;
    padding: 15px;
    border-radius: 8px;
    margin-top: 15px;
    color: #1b5e20;
}
</style>
""", unsafe_allow_html=True)

st.title("📚 国語・英語・共通テストWeb学習アプリ")

# --- セッション状態の初期化 ---
if "answered" not in st.session_state:
    st.session_state.answered = False
if "idx" not in st.session_state:
    st.session_state.idx = 0
if "shuffled_df" not in st.session_state:
    st.session_state.shuffled_df = None
if "current_subject" not in st.session_state:
    st.session_state.current_subject = ""

# --- CSV読み込み関数 ---
@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_csv(file_path)
        # 列名の空白除去＆小文字化（揺らぎを防止）
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        return None

# --- サイドバー（科目選択） ---
subject = st.sidebar.selectbox(
    "科目を選択してください",
    [
        "選択してください",
        "共通テスト現代文（漢字）",
        "古文単語",
        "漢文句法",
        "英単語"
    ]
)

# 科目が変更されたら状態をリセット
if subject != st.session_state.current_subject:
    st.session_state.current_subject = subject
    st.session_state.idx = 0
    st.session_state.answered = False
    st.session_state.shuffled_df = None

# --- 未選択時 ---
if subject == "選択してください":
    st.info("👈 左側のサイドバーから学習したい科目を選択してください。")
    st.stop()

# --- ファイルパスの設定 ---
file_map = {
    "共通テスト現代文（漢字）": "kokugo_kanji.csv",
    "古文単語": "kobun_words.csv",
    "漢文句法": "kanbun_syntax.csv",
    "英単語": "english_words.csv"
}

csv_file = file_map.get(subject)
df = load_data(csv_file)

if df is None or df.empty:
    st.error(f"⚠️ ファイル `{csv_file}` の読み込みに失敗したか、データが空です。ファイルが存在するか確認してください。")
    st.stop()

# --- シャッフル処理 ---
if st.session_state.shuffled_df is None:
    st.session_state.shuffled_df = df.sample(frac=1).reset_index(drop=True)

shuffled_df = st.session_state.shuffled_df
total_questions = len(shuffled_df)

# 全問終了チェック
if st.session_state.idx >= total_questions:
    st.balloons()
    st.success("🎉 全ての問題が終了しました！お疲れ様でした。")
    if st.button("🔄 もう一度最初から解く"):
        st.session_state.shuffled_df = df.sample(frac=1).reset_index(drop=True)
        st.session_state.idx = 0
        st.session_state.answered = False
        st.rerun()
    st.stop()

# 現在の問題データ
idx = st.session_state.idx
row = shuffled_df.iloc[idx]

# 進捗表示
st.caption(f"問題 {idx + 1} / {total_questions}")

# ==========================================
# 1. 共通テスト現代文（漢字）
# ==========================================
if subject == "共通テスト現代文（漢字）":
    st.info("💡 カタカナ部分と同じ漢字を含む選択肢を選んでください。")

    # 問題文表示
    q_text = row.get("question", "")
    st.markdown(f'<div class="card red-card"><b>{q_text}</b></div>', unsafe_allow_html=True)

    # option a, option b, option c, option d 列から選択肢リストを作成
    options = []
    for opt_key in ["option a", "option b", "option c", "option d"]:
        if opt_key in row and pd.notna(row[opt_key]) and str(row[opt_key]).strip():
            options.append(str(row[opt_key]).strip())

    # 選択肢が見つからない場合の警告
    if not options:
        st.warning("⚠️ 選択肢データが見つかりませんでした。CSVの列名（option A, option B...）をご確認ください。")

    # 選択肢ボタンを表示
    for opt in options:
        if st.button(opt, disabled=st.session_state.answered, key=f"kanji_opt_{idx}_{opt}"):
            st.session_state.user_choice = opt
            st.session_state.answered = True
            st.rerun()

    # 解答後のフィードバック表示
    if st.session_state.answered:
        user_ans = st.session_state.get("user_choice", "")
        correct_ans = str(row.get("answer", "")).strip()

        # 正誤判定 (正解テキストが選択肢に含まれているか、または完全一致)
        if correct_ans and (correct_ans in user_ans):
            st.success("正解！")
        else:
            st.error(f"不正解... 正解は 【 {correct_ans} 】 です。")

        # 解説の表示
        if pd.notna(row.get("explanation")):
            st.markdown(f'<div class="exp-card"><b>【解説】</b><br>{row["explanation"]}</div>', unsafe_allow_html=True)

        st.write("---")
        c1, c2 = st.columns(2)
        if c1.button("✅ 次へ", key="next_btn"):
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()
        if c2.button("🔄 もう一度", key="retry_btn"):
            st.session_state.answered = False
            st.rerun()

# ==========================================
# 2. その他の科目（単語カード形式など）
# ==========================================
else:
    # 古文単語・漢文句法・英単語用の汎用表示
    q_text = row.get("question", row.get("word", ""))
    st.markdown(f'<div class="card red-card"><b>{q_text}</b></div>', unsafe_allow_html=True)

    if not st.session_state.answered:
        if st.button("答えを見る"):
            st.session_state.answered = True
            st.rerun()
    else:
        ans_text = row.get("answer", row.get("meaning", ""))
        st.success(f"**正解:** {ans_text}")

        if pd.notna(row.get("explanation")):
            st.markdown(f'<div class="exp-card"><b>【解説】</b><br>{row["explanation"]}</div>', unsafe_allow_html=True)

        st.write("---")
        c1, c2 = st.columns(2)
        if c1.button("✅ 次へ", key="next_btn_gen"):
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()
        if c2.button("🔄 もう一度", key="retry_btn_gen"):
            st.session_state.answered = False
            st.rerun()
