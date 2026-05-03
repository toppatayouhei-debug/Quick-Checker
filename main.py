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
.orange-card { border-left: 8px solid #ff9800; } /* 英語系 */
.pink-card   { border-left: 8px solid #e91e63; } /* 日本史 */
.violet-card { border-left: 8px solid #9c27b0; } /* 史料 */
.cyan-card   { border-left: 8px solid #00bcd4; } /* 世界史 */

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

# 表記ゆれクリーニング関数
def clean_text(t):
    return re.sub(r'[「」『』・=＝\s　.,?!]', '', str(t))

# 状態リセット関数
def reset_quiz_engine():
    keys = ["df", "idx", "answered", "choices", "correct", "selected", "user_choice", "quiz_filter", "quiz_subject", "study_mode"]
    for k in keys:
        if k in st.session_state:
            del st.session_state[k]

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
    st.warning("データがありません。CSVファイル名が正しいか確認してください。")
    st.stop()

# ==================================================
# 5. サイドバー・フィルタリング（既存ロジック）
# ==================================================
current_filter = "All"
# (英単語レベル、日本史章、世界史地域などのフィルタは以前のコードと同様のため省略可ですが、構造は維持)
if subject == "システム英単語" and "level" in raw_df.columns:
    st.sidebar.header("📏 レベル選択")
    level_map = {"All":"All", "Fundamental(1-600)":"Fundamental", "Essential(601-1200)":"Essential", "Advanced(1201-1700)":"Advanced", "Final(1701-2027)":"Final"}
    sel_level = st.sidebar.radio("学習レベル", list(level_map.keys()))
    current_filter = level_map[sel_level]
    df = raw_df if current_filter == "All" else raw_df[raw_df["level"].astype(str).str.contains(current_filter, case=False, na=False)]
elif subject in ["日本史正誤問題攻略", "日本史史料問題攻略"] and "chapter" in raw_df.columns:
    st.sidebar.header("🎯 時代・章選択")
    raw_chaps = [str(x).strip() for x in raw_df["chapter"].dropna().unique().tolist()]
    sorted_chaps = sorted(raw_chaps, key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 999)
    options = ["すべてを表示"] + sorted_chaps
    sel_chap = st.sidebar.radio("章を選択", options)
    current_filter = sel_chap if sel_chap != "すべてを表示" else "すべて"
    df = raw_df if current_filter == "すべて" else raw_df[raw_df["chapter"].astype(str).str.strip() == current_filter]
else:
    df = raw_df

# ==================================================
# 6. クイズエンジン制御
# ==================================================
if st.session_state.get("quiz_subject") != subject or st.session_state.get("quiz_filter") != current_filter:
    reset_quiz_engine()
    st.session_state.quiz_subject = subject
    st.session_state.quiz_filter = current_filter
    st.session_state.df = df.sample(frac=1).reset_index(drop=True)
    st.session_state.idx = 0
    st.session_state.answered = False

active_df = st.session_state.get("df", pd.DataFrame())
idx = st.session_state.get("idx", 0)

if idx >= len(active_df):
    st.balloons(); st.success("🎉 この範囲の全問終了！")
    if st.button("最初から解き直す"): reset_quiz_engine(); st.rerun()
    st.stop()

row = active_df.iloc[idx]
st.progress((idx + 1) / len(active_df))
st.caption(f"{idx+1} / {len(active_df)} 問目")

# ==================================================
# 7. 各科目のUI実装
# ==================================================

# --- A. システム英単語 (音声機能追加版) ---
if subject == "システム英単語":
    st.warning("⚠️ シス単本体をメインに。ミニマルフレーズを意識しましょう。")
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

    c1, c2 = st.columns(2)
    for i, val in enumerate(st.session_state.get("choices", [])):
        with (c1 if i % 2 == 0 else c2):
            if st.button(val, key=f"btn_{idx}_{i}", disabled=st.session_state.get("answered", False)):
                st.session_state.selected, st.session_state.answered = val, True; st.rerun()
    
    if st.session_state.get("answered"):
        if st.session_state.selected == st.session_state.correct: st.success("✨ 正解！")
        else: st.error(f"❌ 不正解... 正解：{st.session_state.correct}")
        st.info(f"意味：{row['all_answers']}\n訳：{row['translation']}")
        
        # 音声再生 (単語 + 例文)
        speech_text = f"{row['question']}. {row['sentence']}"
        q_param = urllib.parse.quote(speech_text)
        tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={q_param}&tl=en&client=tw-ob"
        st.markdown(f'<audio src="{tts_url}" autoplay controls style="width:100%; height:40px;"></audio>', unsafe_allow_html=True)
        
        if st.button("次の問題へ"):
            if "choices" in st.session_state: del st.session_state.choices
            st.session_state.idx += 1; st.session_state.answered = False; st.rerun()

# --- B. 暗唱例文集 (太字判別・自己申告・音声) ---
elif subject == "暗唱例文集":
    ja_text = str(row["question"])
    en_raw = str(row["answer"])
    
    if "study_mode" not in st.session_state: st.session_state.study_mode = "空欄補充"
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        if st.button("🔵 空欄補充"): st.session_state.study_mode = "空欄補充"; st.rerun()
    with col_m2:
        if st.button("🔴 全文暗唱"): st.session_state.study_mode = "全文暗唱"; st.rerun()

    display_text = re.sub(r'\*\*(.*?)\*\*', "[ ____ ]", en_raw) if st.session_state.study_mode == "空欄補充" else "（日本語から英文を再生）"
    st.markdown(f'<div class="card orange-card"><b>【和文】</b><br>{ja_text}<br><hr><b>【英文】</b><br>{display_text}</div>', unsafe_allow_html=True)

    if not st.session_state.get("answered"):
        if st.button("答えを確認する"): st.session_state.answered = True; st.rerun()
    else:
        ans_highlight = re.sub(r'\*\*(.*?)\*\*', r'<span style="color:#e91e63; font-weight:800;">\1</span>', en_raw)
        st.markdown(f'<div class="exp-card" style="border:2px solid #e91e63;">{ans_highlight}</div>', unsafe_allow_html=True)
        
        q_param = urllib.parse.quote(en_raw.replace("**", ""))
        tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={q_param}&tl=en&client=tw-ob"
        st.markdown(f'<audio src="{tts_url}" autoplay controls style="width:100%;"></audio>', unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ できた！"): st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
        with c2:
            if st.button("❌ まだダメ"): st.session_state.answered = False; st.rerun()

# --- C. 日本史正誤問題攻略 ---
elif subject == "日本史正誤問題攻略":
    q, ans = str(row["question"]), str(row["answer"]).strip()
    st.markdown(f'<div class="card pink-card"><b>{q}</b></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("⭕️ 正しい", key=f"o_{idx}", disabled=st.session_state.get("answered", False)):
            st.session_state.user_choice, st.session_state.answered = "◯", True; st.rerun()
    with c2:
        if st.button("❌ 誤り", key=f"x_{idx}", disabled=st.session_state.get("answered", False)):
            st.session_state.user_choice, st.session_state.answered = "×", True; st.rerun()
    if st.session_state.get("answered"):
        if st.session_state.user_choice == ans: st.success("✨ 正解！")
        else: st.error(f"❌ 不正解... 正解は【 {ans} 】")
        if "explanation" in row and pd.notna(row["explanation"]):
            st.markdown(f'<div class="exp-card">{row["explanation"]}</div>', unsafe_allow_html=True)
        if st.button("次の問題へ"): st.session_state.idx += 1; st.session_state.answered = False; st.rerun()

# --- D. 日本史史料問題攻略 ---
elif subject == "日本史史料問題攻略":
    q, ans_raw = str(row["question"]), str(row["answer"])
    st.markdown(f'<div class="card violet-card"><b>【史料文】</b><br>{q}</div>', unsafe_allow_html=True)
    correct_list = [a.strip() for a in ans_raw.split("/") if a.strip()]
    user_inputs = [st.text_input(f"空欄 {chr(65+i)}", key=f"s_{idx}_{i}") for i in range(len(correct_list))]
    if st.button("解答する", disabled=st.session_state.get("answered", False)):
        st.session_state.answered = True; st.rerun()
    if st.session_state.get("answered"):
        for i, (u, c) in enumerate(zip(user_inputs, correct_list)):
            if clean_text(u) == clean_text(c): st.success(f"{chr(65+i)}: 正解! ({c})")
            else: st.error(f"{chr(65+i)}: 不解. 正解: {c}")
        if "explanation" in row and pd.notna(row["explanation"]):
            st.markdown(f'<div class="exp-card">{row["explanation"]}</div>', unsafe_allow_html=True)
        if st.button("次の問題へ"): st.session_state.idx += 1; st.session_state.answered = False; st.rerun()

# --- E. 一問一答（日本史・世界史） ---
else:
    q, ans_raw = str(row["question"]), str(row["answer"])
    card_type = "pink-card" if "日本史" in subject else "cyan-card"
    st.markdown(f'<div class="card {card_type}"><b>{q}</b></div>', unsafe_allow_html=True)
    u_in = st.text_input("答えを入力", key=f"in_{idx}")
    if st.button("解答する", disabled=st.session_state.get("answered", False)):
        st.session_state.answered = True; st.rerun()
    if st.session_state.get("answered"):
        oks = [clean_text(a) for a in ans_raw.split("/")]
        if clean_text(u_in) in oks: st.success(f"✨ 正解！ ({ans_raw})")
        else: st.error(f"❌ 不正解... 正解：{ans_raw}")
        if "explanation" in row and pd.notna(row["explanation"]):
            st.markdown(f'<div class="exp-card">{row["explanation"]}</div>', unsafe_allow_html=True)
        if st.button("次の問題へ"): st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
