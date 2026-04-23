import streamlit as st
import pandas as pd
import random
import re

# ==================================================
# 基本設定
# ==================================================
st.set_page_config(page_title="文系科目は、ゆずれない", layout="centered")

# ==================================================
# CSS
# ==================================================
st.markdown("""
<style>
.stApp { background:#f7f8fc; }
.block-container { max-width:720px; padding-top:1.5rem; } 
.main-title { text-align:center; font-size:2rem; font-weight:900; margin-bottom:0.2rem; }
.sub-title { text-align:center; color:#666; font-size:0.9rem; margin-bottom:1.5rem; }
.card { background:white; padding:22px; border-radius:18px; box-shadow:0 8px 20px rgba(0,0,0,0.06); margin-bottom:1rem; }
.orange-card { border-left: 8px solid #ff9800; }
.pink-card { border-left: 8px solid #e91e63; }
.cyan-card { border-left: 8px solid #00bcd4; }
.exp-card { background: #fff9db; padding: 18px; border-radius: 14px; border: 1px dashed #fab005; margin-top: 10px; }
.stButton button { width: 100%; border-radius: 16px; font-size: 1.1rem; font-weight: 800; }
/* 科目別ボタン色 */
.tango-btn button { background-color: #fff4e6 !important; color: #ff9800 !important; border: 2px solid #ff9800 !important; }
.nihonshi-btn button { background-color: #fce4ec !important; color: #e91e63 !important; border: 2px solid #e91e63 !important; }
.sekaishi-btn button { background-color: #e3f9fb !important; color: #00bcd4 !important; border: 2px solid #00bcd4 !important; }
button:has(div:contains("⭕️")) { background-color: #e7f3ff !important; color: #1877f2 !important; border: 2px solid #1877f2 !important; }
button:has(div:contains("❌")) { background-color: #fff5f5 !important; color: #ff4b4b !important; border: 2px solid #ff4b4b !important; }
</style>
""", unsafe_allow_html=True)

# ==================================================
# 状態管理：クイズに関わる全変数を一括クリア
# ==================================================
def reset_quiz_engine():
    keys_to_delete = ["df", "idx", "answered", "choices", "correct", "selected", "user_choice"]
    for k in keys_to_delete:
        if k in st.session_state:
            del st.session_state[k]

# ==================================================
# メイン表示
# ==================================================
st.markdown('<div class="main-title">🚀 文系科目は、ゆずれない</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">英語・地歴 統合学習ツール</div>', unsafe_allow_html=True)

subject = st.selectbox("学習する科目を選択", ["選択してください", "英単語", "日本史一問一答", "日本史正誤問題攻略", "世界史一問一答"])

if subject == "選択してください":
    st.info("科目を選択してください")
    st.stop()

@st.cache_data
def load_csv(name):
    files = {"英単語":"final_tango_list.csv", "日本史一問一答":"jhcheck.csv", "日本史正誤問題攻略":"seigo_check.csv", "世界史一問一答":"whcheck.csv"}
    try:
        return pd.read_csv(files[name], encoding="utf-8-sig").dropna(how='all')
    except:
        return pd.DataFrame()

raw_df = load_csv(subject)

# ==================================================
# フィルタリング（サイドバー）
# ==================================================
current_filter = "All"
if subject == "英単語" and not raw_df.empty:
    st.sidebar.header("📏 レベル選択")
    level_map = {"All":"All", "Fundamental(1-600)":"Fundamental", "Essential(601-1200)":"Essential", "Advanced(1201-1700)":"Advanced", "Final(1701-2027)":"Final"}
    sel_level = st.sidebar.radio("学習レベル", list(level_map.keys()))
    current_filter = level_map[sel_level]
    
    if current_filter == "All":
        df = raw_df
    else:
        # 文字列の前後空白を除去して一致判定を行う（確実性を高める）
        df = raw_df[raw_df["level"].astype(str).str.strip().str.contains(current_filter, case=False, na=False)]

elif "chapter" in raw_df.columns and not raw_df.empty:
    st.sidebar.header("🎯 範囲選択")
    raw_chaps = raw_df["chapter"].dropna().unique().tolist()
    sorted_chaps = sorted(raw_chaps, key=lambda x: int(re.search(r'\d+', str(x)).group()) if re.search(r'\d+', str(x)) else 999)
    titles = {"第1章": "日本文化のあけぼの", "第2章": "古墳とヤマト政権", "第3章": "律令国家の形成", "第4章": "貴族政治の展開"}
    options = ["すべてを表示"] + [f"{c} {titles.get(c, '')}".strip() if subject == "日本史正誤問題攻略" else str(c) for c in sorted_chaps]
    sel_chap = st.sidebar.radio("範囲", options)
    current_filter = sel_chap.split(" ")[0] if sel_chap != "すべてを表示" else "すべて"
    df = raw_df if current_filter == "すべて" else raw_df[raw_df["chapter"].astype(str).str.strip() == current_filter]
else:
    df = raw_df

# 科目やフィルタが変わったらリセット
if st.session_state.get("quiz_subject") != subject or st.session_state.get("quiz_filter") != current_filter:
    reset_quiz_engine()
    st.session_state.quiz_subject = subject
    st.session_state.quiz_filter = current_filter
    st.session_state.df = df.sample(frac=1).reset_index(drop=True)
    st.session_state.idx = 0
    st.session_state.answered = False

# ==================================================
# 実行エンジン
# ==================================================
active_df = st.session_state.get("df", pd.DataFrame())
idx = st.session_state.get("idx", 0)

if active_df.empty:
    st.warning(f"データがありません。選択した範囲（{current_filter}）が正しいか、CSVファイルの内容を確認してください。")
    st.stop()

if idx >= len(active_df):
    st.balloons(); st.success("全問終了！")
    if st.button("もう一度解く"): reset_quiz_engine(); st.rerun()
    st.stop()

row = active_df.iloc[idx]
st.progress((idx + 1) / len(active_df))
st.caption(f"{idx+1} / {len(active_df)} 問目")

btn_class = "nihonshi-btn"
if subject == "英単語": btn_class = "tango-btn"
elif subject == "世界史一問一答": btn_class = "sekaishi-btn"

# --- クイズ表示：英単語 ---
if subject == "英単語":
    word = str(row["question"])
    sentence = re.sub(re.escape(word), f"<span style='color:#ff9800;font-weight:bold'>{word}</span>", str(row["sentence"]), flags=re.IGNORECASE)
    st.markdown(f'<div class="card orange-card">{sentence}</div>', unsafe_allow_html=True)
    
    # 解答前なら選択肢を生成・保持
    if "choices" not in st.session_state:
        ans_list = [x.strip() for x in re.split(r'[,、;]', str(row["all_answers"])) if x.strip()]
        correct = ans_list[0]
        dummies = [x.strip() for x in re.split(r'[,、;]', str(row["dummy_pool"])) if x.strip() and x.strip() != correct]
        choices = [correct] + random.sample(dummies, min(3, len(dummies)))
        random.shuffle(choices)
        st.session_state.choices = choices
        st.session_state.correct = correct

    st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    for i, c in enumerate(st.session_state.get("choices", [])):
        with (c1 if i % 2 == 0 else c2):
            if st.button(c, key=f"btn_{idx}_{i}", disabled=st.session_state.get("answered", False)):
                st.session_state.selected = c
                st.session_state.answered = True
                st.rerun()
    
    if st.session_state.get("answered"):
        if st.session_state.selected == st.session_state.correct: st.success("正解！")
        else: st.error(f"不正解... 正解：{st.session_state.correct}")
        st.info(f"意味：{row['all_answers']}\n訳：{row['translation']}")
        if st.button("次の問題へ"):
            # 次へ行くときに現在の問題の選択肢系を消去
            if "choices" in st.session_state: del st.session_state.choices
            if "correct" in st.session_state: del st.session_state.correct
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- クイズ表示：その他 ---
else:
    if subject == "日本史正誤問題攻略":
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
            if st.session_state.user_choice == ans: st.success("正解！")
            else: st.error(f"不正解... 正解は【 {ans} 】")
            if "explanation" in row and pd.notna(row["explanation"]): st.markdown(f'<div class="exp-card">{row["explanation"]}</div>', unsafe_allow_html=True)
            if st.button("次の問題へ"): st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
    else:
        q, ans_raw = str(row["question"]), str(row["answer"])
        st.markdown(f'<div class="card {"pink-card" if "日本史" in subject else "cyan-card"}"><b>{q}</b></div>', unsafe_allow_html=True)
        u_in = st.text_input("答えを入力", key=f"in_{idx}")
        st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
        if st.button("解答する", disabled=st.session_state.get("answered", False)): st.session_state.answered = True; st.rerun()
        if st.session_state.get("answered"):
            u_c = u_in.replace(" ","").replace("　","")
            oks = [a.strip().replace(" ","").replace("　","") for a in ans_raw.split("/")]
            if u_c in oks: st.success("正解！")
            else: st.error(f"不正解... 正解：{ans_raw}")
            if "explanation" in row and pd.notna(row["explanation"]): st.markdown(f'<div class="exp-card">{row["explanation"]}</div>', unsafe_allow_html=True)
            if st.button("次の問題へ"): st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
