import streamlit as st
import pandas as pd
import random
import re
import urllib.parse

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

/* 解説カード */
.exp-card { background: #fff9db; padding: 18px; border-radius: 14px; border: 1px dashed #fab005; margin-top: 10px; font-size: 0.95rem; }

/* ボタンデザイン */
.stButton button { width: 100%; border-radius: 16px; font-size: 1.1rem; font-weight: 800; min-height: 55px; transition: 0.2s; }
.tango-btn button { background-color: #fff4e6 !important; color: #ff9800 !important; border: 2px solid #ff9800 !important; }
.nihonshi-btn button { background-color: #fce4ec !important; color: #e91e63 !important; border: 2px solid #e91e63 !important; }
.shiryo-btn button { background-color: #f3e5f5 !important; color: #9c27b0 !important; border: 2px solid #9c27b0 !important; }
.sekaishi-btn button { background-color: #e3f9fb !important; color: #00bcd4 !important; border: 2px solid #00bcd4 !important; }

/* 注意書き */
.guide-text { color: #222222 !important; font-size: 0.88rem; font-weight: 600; margin-bottom: 0.4rem; }
</style>
""", unsafe_allow_html=True)

# 状態リセット
def reset_quiz_engine():
    keys = ["df", "idx", "answered", "choices", "correct", "selected", "user_choice", "quiz_filter", "quiz_subject", "study_mode"]
    for k in keys:
        if k in st.session_state:
            del st.session_state[k]

# テキストクリーニング
def clean_text(t):
    return re.sub(r'[「」『』・=＝\s　.,?!]', '', str(t))

# ==================================================
# 3. メイン画面ヘッダー
# ==================================================
st.markdown('<div class="main-title">🚀 文系科目は、ゆずれない</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">英語・地歴 統合学習ツール</div>', unsafe_allow_html=True)

subject = st.selectbox("学習する科目を選択", [
    "選択してください", 
    "システム英単語", 
    "暗唱例文集",
    "日本史一問一答", 
    "日本史正誤問題攻略", 
    "日本史史料問題攻略", 
    "世界史一問一答"
])

if subject == "選択してください":
    st.info("**【学習の進め方】**\n1. 科目を選択してください。\n2. サイドバーで範囲を絞り込めます。")
    st.stop()

# ==================================================
# 4. データ読み込み
# ==================================================
@st.cache_data
def load_csv(name):
    files = {
        "システム英単語":"final_tango_list.csv", 
        "暗唱例文集":"english_sent.csv",
        "日本史一問一答":"jhcheck.csv", 
        "日本史正誤問題攻略":"seigo_check.csv", 
        "日本史史料問題攻略":"shiryo_check.csv",
        "世界史一問一答":"whcheck.csv"
    }
    try:
        df = pd.read_csv(files[name], encoding="utf-8-sig")
        return df.dropna(how='all')
    except Exception as e:
        st.error(f"ファイル読み込みエラー: {e}")
        return pd.DataFrame()

raw_df = load_csv(subject)
if raw_df.empty:
    st.warning("データがありません。")
    st.stop()

# ==================================================
# 5. サイドバー・フィルタリング
# ==================================================
current_filter = "All"

if subject == "システム英単語":
    st.sidebar.header("📏 レベル選択")
    level_map = {"All":"All", "Fundamental(1-600)":"Fundamental", "Essential(601-1200)":"Essential", "Advanced(1201-1700)":"Advanced", "Final(1701-2027)":"Final"}
    sel_level = st.sidebar.radio("学習レベル", list(level_map.keys()))
    current_filter = level_map[sel_level]
    df = raw_df if current_filter == "All" else raw_df[raw_df["level"].astype(str).str.contains(current_filter, case=False, na=False)]

elif (subject == "暗唱例文集" or "chapter" in raw_df.columns):
    st.sidebar.header("🎯 章・時代選択")
    raw_chaps = [str(x).strip() for x in raw_df["chapter"].dropna().unique().tolist()]
    try:
        sorted_chaps = sorted(raw_chaps, key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 999)
    except:
        sorted_chaps = sorted(raw_chaps)
    options = ["すべてを表示"] + sorted_chaps
    sel_chap = st.sidebar.radio("範囲を選択", options)
    current_filter = sel_chap if sel_chap != "すべてを表示" else "すべて"
    df = raw_df if current_filter == "すべて" else raw_df[raw_df["chapter"].astype(str).str.strip() == current_filter]

elif subject == "世界史一問一答" and "area" in raw_df.columns:
    st.sidebar.header("🗺️ 地域選択")
    existing_areas = [str(x).strip() for x in raw_df["area"].fillna("未分類").unique()]
    options = ["すべてを表示"] + sorted(existing_areas)
    sel_area = st.sidebar.radio("地域", options)
    current_filter = sel_area if sel_area != "すべてを表示" else "すべて"
    df = raw_df if current_filter == "すべて" else raw_df[raw_df["area"].astype(str).str.strip() == current_filter]
else:
    df = raw_df

# ==================================================
# 6. クイズエンジン制御
# ==================================================
if st.session_state.get("quiz_subject") != subject or st.session_state.get("quiz_filter") != current_filter:
    reset_quiz_engine()
    st.session_state.quiz_subject = subject
    st.session_state.quiz_filter = current_filter
    st.session_state.df = df.sample(frac=1).reset_index(drop=True) if not df.empty else pd.DataFrame()
    st.session_state.idx = 0
    st.session_state.answered = False
    # デフォルトを「全文暗唱」に設定
    st.session_state.study_mode = "全文暗唱"

active_df = st.session_state.get("df", pd.DataFrame())
idx = st.session_state.get("idx", 0)

if active_df.empty:
    st.stop()

if idx >= len(active_df):
    st.balloons(); st.success("🎉 全問終了！")
    if st.button("リセット"): reset_quiz_engine(); st.rerun()
    st.stop()

row = active_df.iloc[idx]
st.progress((idx + 1) / len(active_df))

btn_class = "nihonshi-btn"
if "史料" in subject: btn_class = "shiryo-btn"
elif "世界史" in subject: btn_class = "sekaishi-btn"
elif "英" in subject: btn_class = "tango-btn"

# ==================================================
# 7. クイズUI
# ==================================================

# --- 暗唱例文集 ---
if subject == "暗唱例文集":
    ja_text = str(row["japanese"])
    en_raw = str(row["English"])

    # モード切り替えボタン
    c_m1, c_m2 = st.columns(2)
    with c_m1:
        if st.button("🔴 全文暗唱"): st.session_state.study_mode = "全文暗唱"; st.rerun()
    with c_m2:
        if st.button("🔵 ヒントはここ"): st.session_state.study_mode = "空欄補充"; st.rerun()

    # 表示テキストの制御
    if st.session_state.study_mode == "空欄補充":
        display_text = re.sub(r'\*\*(.*?)\*\*', "[ ____ ]", en_raw)
    else:
        display_text = "（英文を思い出してください）"

    st.markdown(f'''
        <div class="card orange-card">
            <div style="font-size:0.85rem; color:#888;">【日本語】</div>
            <div style="font-weight:bold; font-size:1.2rem; margin-bottom:15px;">{ja_text}</div>
            <div style="border-top:1px dashed #ddd; margin-bottom:15px;"></div>
            <div style="font-size:0.85rem; color:#888;">【英文ヒント】</div>
            <div style="font-size:1.2rem; font-family:serif;">{display_text}</div>
        </div>
    ''', unsafe_allow_html=True)

    if not st.session_state.get("answered"):
        if st.button("答えを確認する", key=f"show_ans_{idx}"):
            st.session_state.answered = True; st.rerun()
    else:
        ans_highlight = re.sub(r'\*\*(.*?)\*\*', r'<span style="color:#e91e63; font-weight:800; border-bottom:2px solid;">\1</span>', en_raw)
        st.markdown(f'''
            <div class="exp-card" style="border: 2px solid #e91e63;">
                <div style="font-size:0.85rem; color:#e91e63; font-weight:bold;">【正解】</div>
                <div style="font-size:1.4rem; font-family:serif;">{ans_highlight}</div>
            </div>
        ''', unsafe_allow_html=True)
        
        # 音声再生（GitHub/ブラウザ互換性を高めた安定版URL）
        clean_en = en_raw.replace("**", "")
        q_param = urllib.parse.quote(clean_en)
        tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={q_param}&tl=en&client=tw-ob"
        st.markdown(f'<audio src="{tts_url}" autoplay controls style="width:100%; margin-top:10px;"></audio>', unsafe_allow_html=True)
        
        st.write("---")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ 言えた！"): st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
        with c2:
            if st.button("❌ 復習が必要"): st.session_state.answered = False; st.rerun()

# --- 他の科目 ---
elif subject == "システム英単語":
    word = str(row["question"])
    sentence = re.sub(re.escape(word), f"<span style='color:#ff9800;font-weight:bold'>{word}</span>", str(row["sentence"]), flags=re.IGNORECASE)
    st.markdown(f'<div class="card orange-card">{sentence}</div>', unsafe_allow_html=True)
    if "choices" not in st.session_state:
        ans_list = [x.strip() for x in re.split(r'[,、;]', str(row["all_answers"])) if x.strip()]
        correct = ans_list[0]
        dummies = [x.strip() for x in re.split(r'[,、;]', str(row["dummy_pool"])) if x.strip() and x.strip() != correct]
        choices = [correct] + random.sample(dummies, min(3, len(dummies)))
        random.shuffle(choices)
        st.session_state.choices, st.session_state.correct = choices, correct
    st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    for i, val in enumerate(st.session_state.get("choices", [])):
        with (c1 if i % 2 == 0 else c2):
            if st.button(val, key=f"btn_{idx}_{i}"):
                st.session_state.selected, st.session_state.answered = val, True; st.rerun()
    if st.session_state.get("answered"):
        if st.session_state.selected == st.session_state.correct: st.success("✨ 正解！")
        else: st.error(f"❌ 正解：{st.session_state.correct}")
        if st.button("次の問題へ"):
            if "choices" in st.session_state: del st.session_state.choices
            st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

else:
    q, ans_raw = str(row["question"]), str(row["answer"])
    card_type = "pink-card" if "日本史" in subject else "cyan-card"
    st.markdown(f'<div class="card {card_type}"><b>{q}</b></div>', unsafe_allow_html=True)
    u_in = st.text_input("答えを入力", key=f"in_{idx}")
    st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
    if st.button("解答する", key=f"ans_btn_{idx}"):
        st.session_state.answered = True; st.rerun()
    if st.session_state.get("answered"):
        oks = [clean_text(a) for a in ans_raw.split("/")]
        if clean_text(u_in) in oks: st.success(f"✨ 正解！ ({ans_raw})")
        else: st.error(f"❌ 正解：{ans_raw}")
        if st.button("次の問題へ"): st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
