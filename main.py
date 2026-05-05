import streamlit as st
import pandas as pd
import random
import re
import urllib.parse
import base64
import requests

# ==================================================
# 1. 基本設定
# ==================================================
st.set_page_config(
    page_title="文系科目は、ゆずれない",
    page_icon="🚀",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ==================================================
# 2. CSS（デザイン・レイアウト）
# ==================================================
st.markdown("""
<style>
.stApp { background:#f7f8fc; }
.block-container { max-width:720px; padding-top: 4rem !important; } 
.main-title { text-align:center; font-size:1.8rem; font-weight:900; margin-bottom:0.2rem; }
.sub-title { text-align:center; color:#666; font-size:0.85rem; margin-bottom:1.5rem; }

/* 問題カード */
.card { background:white; padding:22px; border-radius:18px; box-shadow:0 8px 20px rgba(0,0,0,0.06); margin-bottom:1rem; line-height:1.7; font-size:1.05rem; color:#111; }
.orange-card { border-left: 8px solid #ff9800; } 
.pink-card   { border-left: 8px solid #e91e63; }
.violet-card { border-left: 8px solid #9c27b0; }
.cyan-card   { border-left: 8px solid #00bcd4; }
.green-card  { border-left: 8px solid #4caf50; } /* 生物用 */

/* 解説カード（通常科目用） */
.exp-card { background: #fff9db; padding: 18px; border-radius: 14px; border: 1px dashed #fab005; margin-top: 10px; font-size: 0.95rem; color: #333; }

/* ボタンデザイン */
.stButton button { width: 100%; border-radius: 16px; font-size: 1.1rem; font-weight: 800; min-height: 55px; transition: 0.2s; }
.tango-btn button { background-color: #fff4e6 !important; color: #ff9800 !important; border: 2px solid #ff9800 !important; }

/* 正誤問題用の特殊ボタン（⭕️/❌） */
button:has(div:contains("⭕️")) { background-color: #e7f3ff !important; color: #1877f2 !important; border: 2px solid #1877f2 !important; }
button:has(div:contains("❌")) { background-color: #fff5f5 !important; color: #ff4b4b !important; border: 2px solid #ff4b4b !important; }

/* 生物用のフォント強制指定（serif） */
.bio-result { font-family: serif !important; font-size: 1.05rem; line-height: 1.6; }

.guide-text { color: #555555 !important; font-size: 0.82rem; font-weight: 600; margin-bottom: 0.4rem; }
</style>
""", unsafe_allow_html=True)

# ユーティリティ関数
def play_voice(text, label="音声を聴く"):
    try:
        q = urllib.parse.quote(text)
        url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={q}&tl=en&client=tw-ob"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            b64 = base64.b64encode(res.content).decode()
            md = f'''
                <div style="background:#f8f9fa; border-radius:15px; padding:10px; margin-top:10px; display:flex; align-items:center; border:1px solid #ddd;">
                    <span style="font-size:0.85rem; color:#ff9800; font-weight:bold; margin-right:auto; padding-left:5px;">🎧 {label}</span>
                    <audio src="data:audio/mp3;base64,{b64}" controls style="height: 35px;"></audio>
                </div>
            '''
            st.markdown(md, unsafe_allow_html=True)
    except: pass

def reset_quiz_engine():
    keys = ["df", "idx", "answered", "choices", "correct", "selected", "user_choice", "quiz_filter", "quiz_subject", "study_mode"]
    for k in keys:
        if k in st.session_state: del st.session_state[k]

def clean_text(t):
    return re.sub(r'[「」『』・=＝\s　.,?!-]', '', str(t))

# ==================================================
# 3. メイン画面
# ==================================================
st.markdown('<div class="main-title">🚀 文系科目は、ゆずれない</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">英語・地歴・生物 統合学習ツール</div>', unsafe_allow_html=True)

subject = st.selectbox("学習する科目を選択", [
    "選択してください", "システム英単語", "暗唱例文集",
    "日本史一問一答", "日本史正誤問題攻略", "日本史史料問題攻略", 
    "世界史一問一答", "生物一問一答"
])

if subject == "選択してください":
    st.info("1. 科目を選択してください。")
    st.stop()

# データ読み込み
@st.cache_data
def load_csv(name):
    files = {
        "システム英単語":"final_tango_list.csv", "暗唱例文集":"english_sent.csv",
        "日本史一問一答":"jhcheck.csv", "日本史正誤問題攻略":"seigo_check.csv", 
        "日本史史料問題攻略":"shiryo_check.csv", "世界史一問一答":"whcheck.csv",
        "生物一問一答":"biology.csv"
    }
    try:
        df = pd.read_csv(files[name], encoding="utf-8-sig").dropna(how='all')
        df.columns = [c.lower().strip() for c in df.columns]
        return df
    except: return pd.DataFrame()

raw_df = load_csv(subject)
if raw_df.empty:
    st.warning("データが見つかりません。")
    st.stop()

# フィルタリング
current_filter = "All"
if "chapter" in raw_df.columns:
    raw_chaps = sorted([str(x).strip() for x in raw_df["chapter"].dropna().unique().tolist()])
    sel_range = st.sidebar.radio("範囲を選択", ["すべてを表示"] + raw_chaps)
    if sel_range == "すべてを表示":
        df = raw_df
    else:
        current_filter = sel_range
        df = raw_df[raw_df["chapter"].astype(str).str.strip() == current_filter]
else:
    df = raw_df

if st.session_state.get("quiz_subject") != subject or st.session_state.get("quiz_filter") != current_filter:
    reset_quiz_engine()
    st.session_state.quiz_subject, st.session_state.quiz_filter = subject, current_filter
    st.session_state.df = df.sample(frac=1).reset_index(drop=True)
    st.session_state.idx, st.session_state.answered = 0, False

active_df = st.session_state.get("df", pd.DataFrame())
idx = st.session_state.get("idx", 0)

if idx >= len(active_df):
    st.success("全問終了！"); st.button("リセット", on_click=reset_quiz_engine); st.stop()

row = active_df.iloc[idx]
st.progress((idx + 1) / len(active_df))

# ==================================================
# 6. クイズUI
# ==================================================

# --- 生物一問一答（特別な統合フォーマット） ---
if subject == "生物一問一答":
    st.markdown(f'<div class="card green-card"><b>{row["question"]}</b></div>', unsafe_allow_html=True)
    st.warning("⚠️理系用のものをそのまま移植しています。")
    
    if not st.session_state.answered:
        if st.button("答えを確認する"): st.session_state.answered = True; st.rerun()
    else:
        # 正解と解説を「同じ青い枠」の中に、同じフォーマットで並べて表示
        ans_text = str(row["answer"])
        exp_text = str(row["explanation"]) if pd.notna(row.get("explanation")) else ""
        
        full_content = f"【正解】\n{ans_text}"
        if exp_text:
            full_content += f"\n\n【解説】\n{exp_text}"
            
        # serifフォントを適用した青枠
        st.success(full_content)
        st.markdown('<style>.stAlert div { font-family: serif !important; white-space: pre-wrap; }</style>', unsafe_allow_html=True)

        st.write("---")
        c1, c2 = st.columns(2)
        if c1.button("✅ 次へ"): st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
        if c2.button("🔄 もう一度"): st.session_state.answered = False; st.rerun()

# --- それ以外の科目（既存仕様を維持） ---
else:
    card_c = "pink-card" if "日本史" in subject else "cyan-card"
    if subject == "暗唱例文集": card_c = "orange-card"
    
    st.markdown(f'<div class="card {card_c}"><b>{row.get("question", row.get("japanese", ""))}</b></div>', unsafe_allow_html=True)
    
    if not st.session_state.answered:
        if st.button("答えを確認する"): st.session_state.answered = True; st.rerun()
    else:
        ans = row.get("answer", row.get("english", ""))
        st.success(f"正解：{ans}")
        if pd.notna(row.get("explanation")):
            st.markdown(f'<div class="exp-card">{row["explanation"]}</div>', unsafe_allow_html=True)
        
        st.write("---")
        c1, c2 = st.columns(2)
        if c1.button("✅ 次へ"): st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
        if c2.button("🔄 もう一度"): st.session_state.answered = False; st.rerun()
