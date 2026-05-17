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

/* 解説カード */
.exp-card { background: #fff9db; padding: 18px; border-radius: 14px; border: 1px dashed #fab005; margin-top: 10px; font-size: 0.95rem; color: #333; }

/* ボタンデザイン */
.stButton button { width: 100%; border-radius: 16px; font-size: 1.1rem; font-weight: 800; min-height: 55px; transition: 0.2s; }
.tango-btn button { background-color: #fff4e6 !important; color: #ff9800 !important; border: 2px solid #ff9800 !important; }
.nihonshi-btn button { background-color: #fce4ec !important; color: #e91e63 !important; border: 2px solid #e91e63 !important; }

/* 正誤問題用の特殊ボタン（⭕️/❌） */
button:has(div:contains("⭕️")) { background-color: #e7f3ff !important; color: #1877f2 !important; border: 2px solid #1877f2 !important; }
button:has(div:contains("❌")) { background-color: #fff5f5 !important; color: #ff4b4b !important; border: 2px solid #ff4b4b !important; }

.guide-text { color: #555555 !important; font-size: 0.82rem; font-weight: 600; margin-bottom: 0.4rem; }

/* === 再生ボタンのスタイル === */
.audio-container {
    background-color: #f8f9fa;
    border-radius: 15px;
    padding: 10px;
    margin-top: 10px;
    display: flex;
    align-items: center;
    border: 1px solid #ddd;
}
.audio-text {
    font-size: 0.85rem;
    color: #ff9800;
    font-weight: bold;
    margin-right: auto;
    padding-left: 5px;
}
audio::-webkit-media-controls-panel { background-color: #fff4e6; }
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
                <div class="audio-container">
                    <span class="audio-text">🎧 {label}</span>
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
    "選択してください", "システム英単語", "暗唱例文集", "頻出！英文法入試問題",
    "日本史一問一答", "日本史正誤問題攻略", "日本史史料問題攻略", 
    "世界史一問一答", "世界史正誤問題攻略", "生物一問一答"
])

if subject == "選択してください":
    st.info("1. 科目を選択してください。\n2. サイドバーでレベルや範囲を絞り込めます。")
    st.stop()

# ==================================================
# 4. データ読み込み（英文法だけキャッシュを完全無効化）
# ==================================================
def load_csv(name):
    files = {
        "システム英単語":"final_tango_list.csv", "暗唱例文集":"english_sent.csv",
        "頻出！英文法入試問題":"grammar.csv",
        "日本史一問一答":"jhcheck.csv", "日本史正誤問題攻略":"seigo_check.csv", 
        "日本史史料問題攻略":"shiryo_check.csv", "世界史一問一答":"whcheck.csv",
        "世界史正誤問題攻略":"wh_seigo.csv",
        "生物一問一答":"biology.csv"
    }
    try:
        # 英文法だけキャッシュを通さず、常に最新のCSVを直接読み込む
        if name == "頻出！英文法入試問題":
            df = pd.read_csv(files[name], encoding="utf-8-sig").dropna(how='all')
            df.columns = [c.lower().strip() for c in df.columns]
            return df
            
        # 他の科目は、既存の挙動（キャッシュ高速化）を壊さないよう別関数へパス
        return load_csv_with_cache(name)
    except:
        return pd.DataFrame()

# 他の科目のためのキャッシュ用隔離関数
@st.cache_data
def load_csv_with_cache(name):
    files = {
        "システム英単語":"final_tango_list.csv", "暗唱例文集":"english_sent.csv",
        "日本史一問一答":"jhcheck.csv", "日本史正誤問題攻略":"seigo_check.csv", 
        "日本史史料問題攻略":"shiryo_check.csv", "世界史一問一答":"whcheck.csv",
        "世界史正誤問題攻略":"wh_seigo.csv",
        "生物一問一答":"biology.csv"
    }
    df = pd.read_csv(files[name], encoding="utf-8-sig").dropna(how='all')
    df.columns = [c.lower().strip() for c in df.columns]
    return df

# 元の生データ（raw_df）をここで安全に定義してエラーを回避
raw_df = load_csv(subject)
if raw_df.empty:
    st.warning(f"データファイルが見つかりません。({subject})")
    st.stop()

# ==================================================
# 5. サイドバー（フィルタリング・範囲選択）
# ==================================================
current_filter = "All"
nihonshi_titles = {
    "第1章": "歴史のはじまり", "第2章": "飛鳥時代", "第3章": "奈良時代", "第4章": "平安時代",
    "第5章": "鎌倉時代", "第6章": "室町時代", "第7章": "戦国・安土桃山時代", 
    "第8章": "江戸時代", "第9章": "明治時代", "第10章": "幕藩体制の動揺",
    "第11章": "近世から近代へ", "第12章": "近代国家の成立", "第13章": "近代国家の展開", "第14章": "近代の産業と生活"
}

# --- フィルタリングロジック ---
if subject == "システム英単語":
    level_map = {"All":"All", "Fundamental(1-600)":"Fundamental", "Essential(601-1200)":"Essential", "Advanced(1201-1700)":"Advanced", "Final(1701-2027)":"Final"}
    sel_level = st.sidebar.radio("レベル選択", list(level_map.keys()))
    current_filter = level_map[sel_level]
    df = raw_df if current_filter == "All" else raw_df[raw_df["level"].astype(str).str.contains(current_filter, na=False)]

elif subject == "頻出！英文法入試問題":
    fields_set = set()
    if "field" in raw_df.columns:
        for f_val in raw_df["field"].dropna():
            for sub_f in str(f_val).split("/"):
                if sub_f.strip():
                    fields_set.add(sub_f.strip())
    
    sorted_fields = sorted(list(fields_set))
    grammar_options = ["ランダム（全問シャッフル）"] + sorted_fields
    sel_field = st.sidebar.radio("分野を選択", grammar_options)
    current_filter = sel_field

    if sel_field == "ランダム（全問シャッフル）":
        df = raw_df
    else:
        df = raw_df[raw_df["field"].astype(str).apply(lambda x: sel_field in [s.strip() for s in x.split("/")])]

elif "chapter" in raw_df.columns or "area" in raw_df.columns:
    col_name = "chapter" if "chapter" in raw_df.columns else "area"
    
    def get_sort_key(x):
        nums = re.findall(r'\d+', str(x).translate(str.maketrans('０１２３４５６７８９', '0123456789')))
        return int(nums[0]) if nums else 999

    raw_chaps = sorted([str(x).strip() for x in raw_df[col_name].dropna().unique().tolist()], key=get_sort_key)
    
    if "日本史" in subject:
        options = ["すべてを表示"] + [f"{c} {nihonshi_titles.get(c, '')}".strip() for c in raw_chaps]
    else:
        options = ["すべてを表示"] + raw_chaps
        
    sel_range = st.sidebar.radio("範囲を選択", options)
    
    if sel_range == "すべてを表示":
        current_filter = "すべて"
        df = raw_df
    else:
        target_chap = sel_range.split(" ")[0] if "日本史" in subject else sel_range
        current_filter = target_chap
        df = raw_df[raw_df[col_name].astype(str).str.strip() == current_filter]
else:
    df = raw_df

# セッションの初期化チェック
if st.session_state.get("quiz_subject") != subject or st.session_state.get("quiz_filter") != current_filter:
    reset_quiz_engine()
    st.session_state.quiz_subject = subject
    st.session_state.quiz_filter = current_filter
    st.session_state.df = df.sample(frac=1).reset_index(drop=True)
    st.session_state.idx = 0
    st.session_state.answered = False
    st.session_state.study_mode = "全文暗唱"

active_df = st.session_state.get("df", pd.DataFrame())
idx = st.session_state.get("idx", 0)

if active_df.empty: 
    st.info("選択された範囲に問題がありません。")
    st.stop()

if idx >= len(active_df):
    st.balloons(); st.success("全問終了！"); st.button("リセットして最初から", on_click=reset_quiz_engine); st.stop()

row = active_df.iloc[idx]
st.progress((idx + 1) / len(active_df))

# ==================================================
# 6. クイズUI
# ==================================================

# --- 1. 暗唱例文集 ---
if subject == "暗唱例文集":
    c_m1, c_m2 = st.columns(2)
    with c_m1:
        if st.button("🔴 全文暗唱"): st.session_state.study_mode = "全文暗唱"; st.rerun()
    with c_m2:
        if st.button("🔵 ヒントはここ"): st.session_state.study_mode = "空欄補充"; st.rerun()
    if st.session_state.study_mode == "空欄補充": st.info("💡 [　　]の中は１語とは限りません")
    disp = re.sub(r'\*\*(.*?)\*\*', "[ ____ ]", str(row["english"])) if st.session_state.study_mode == "空欄補充" else "（英文を思い出してください）"
    st.markdown(f'<div class="card orange-card">【日本語】<br><b>{row["japanese"]}</b><hr>【英文】<br>{disp}</div>', unsafe_allow_html=True)
    if not st.session_state.answered:
        if st.button("答えを確認する"): st.session_state.answered = True; st.rerun()
    else:
        ans_highlight = re.sub(r'\*\*(.*?)\*\*', r'<span style="color:#e91e63; font-weight:800; border-bottom:2px solid;">\1</span>', str(row["english"]))
        st.markdown(f'<div class="exp-card">【正解】<br><span style="font-size:1.3rem; font-family:serif;">{ans_highlight}</span></div>', unsafe_allow_html=True)
        play_voice(str(row["english"]).replace("**", ""), "音声を聴く")
        st.write("---")
        c1, c2 = st.columns(2)
        if c1.button("✅ 次へ"): st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
        if c2.button("🔄 もう一度"): st.session_state.answered = False; st.rerun()

# --- 2. システム英単語 ---
elif subject == "システム英単語":
    word = str(row["question"])
    sent = re.sub(re.escape(word), f"<span style='color:#ff9800;font-weight:bold'>{word}</span>", str(row["sentence"]), flags=re.IGNORECASE)
    st.markdown(f'<div class="card orange-card">{sent}</div>', unsafe_allow_html=True)
    st.warning("⚠️ シス単本体をメインにしましょう。情報量が全然違います。")
    if "choices" not in st.session_state:
        ans_list = [x.strip() for x in re.split(r'[,、;]', str(row["all_answers"]))]
        correct = ans_list[0]
        dummies = [x.strip() for x in re.split(r'[,、;]', str(row["dummy_pool"])) if x.strip() != correct]
        st.session_state.choices = random.sample([correct] + random.sample(dummies, 3), 4)
        random.shuffle(st.session_state.choices)
        st.session_state.correct = correct
    st.markdown('<div class="tango-btn">', unsafe_allow_html=True)
    cols = st.columns(2)
    for i, val in enumerate(st.session_state.choices):
        if cols[i%2].button(val, key=f"t_{i}", disabled=st.session_state.answered):
            st.session_state.selected, st.session_state.answered = val, True; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    if st.session_state.answered:
        if st.session_state.selected == st.session_state.correct: st.success("正解！")
        else: st.error(f"不正解... 正解：{st.session_state.correct}")
        st.info(f"意味：{row['all_answers']}\n訳：{row['translation']}")
        play_voice(str(row["question"]), "音声を聴く")
        st.write("---")
        c1, c2 = st.columns(2)
        if c1.button("✅ 次へ"): 
            if "choices" in st.session_state: del st.session_state.choices
            st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
        if c2.button("🔄 もう一度"): st.session_state.answered = False; st.rerun()

# --- 3. 頻出！英文法入試問題 ---
elif subject == "頻出！英文法入試問題":
    uni_suffix = f" （{row['university']}）" if pd.notna(row.get("university")) and str(row["university"]).strip() else ""
    full_question = f"{row['question']}{uni_suffix}"
    
    st.markdown(f'<div class="card orange-card"><b>{full_question}</b></div>', unsafe_allow_html=True)
    
    # 3つの指定注意書きの出力
    st.warning("⚠️ 目標は７割。そのために必要な知識量を演習で知りましょう")
    st.info("⚠️ 「理屈で解く問題」と「知識で解く」問題を区別しましょう")
    st.error("⚠️ 問題を、解いて解いて解きまくる。ニガテ意識よさようなら")
    
    if "choices" not in st.session_state:
        choice_list = [x.strip() for x in str(row["option"]).split("/") if x.strip()]
        st.session_state.choices = choice_list
        st.session_state.correct = str(row["answer"]).strip()

    st.markdown('<div class="tango-btn">', unsafe_allow_html=True)
    cols = st.columns(2)
    for i, val in enumerate(st.session_state.choices):
        if cols[i%2].button(val, key=f"g_{i}", disabled=st.session_state.answered):
            st.session_state.selected, st.session_state.answered = val, True; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.session_state.answered:
        if st.session_state.selected == st.session_state.correct: 
            st.success("正解！")
        else: 
            st.error(f"不正解... 正解：{st.session_state.correct}")
            
        st.markdown(f'<div class="exp-card">{row["explanation"]}</div>', unsafe_allow_html=True)
        
        voice_sentence = str(row["question"]).replace("(      )", st.session_state.correct)
        play_voice(voice_sentence, "英文を聴く")
        
        st.write("---")
        c1, c2 = st.columns(2)
        if c1.button("✅ 次へ"): 
            if "choices" in st.session_state: del st.session_state.choices
            st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
        if c2.button("🔄 もう一度"): st.session_state.answered = False; st.rerun()

# --- 4. 正誤問題 (日本史・世界史) ---
elif subject in ["日本史正誤問題攻略", "世界史正誤問題攻略"]:
    if subject == "日本史正誤問題攻略":
        st.warning("⚠️ 山川『日本史探究』（教科書）の文章を正誤問題にしてあります。共テ&私大に効果抜群。")
        card_class = "pink-card"
    else:
        st.warning("⚠️ 世界史の教科書文章をベースにした正誤問題です。知識の定着を確認しましょう。")
        card_class = "cyan-card"
        
    st.markdown(f'<div class="card {card_class}"><b>{row["question"]}</b></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    
    raw_ans = str(row["answer"]).strip().lower()
    if raw_ans in ["◯", "○", "正", "1", "true", "ok", "yes"]:
        ans = "◯"
    else:
        ans = "×"
    
    if c1.button("⭕️ 正しい", disabled=st.session_state.answered): st.session_state.user_choice, st.session_state.answered = "◯", True; st.rerun()
    if c2.button("❌ 誤り", disabled=st.session_state.answered): st.session_state.user_choice, st.session_state.answered = "×", True; st.rerun()
    
    if st.session_state.answered:
        if st.session_state.user_choice == ans: st.success("正解！")
        else: st.error(f"不正解... 正解は【 {ans} 】")
        if pd.notna(row.get("explanation")): st.markdown(f'<div class="exp-card">{row["explanation"]}</div>', unsafe_allow_html=True)
        st.write("---")
        c1, c2 = st.columns(2)
        if c1.button("✅ 次へ"): st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
        if c2.button("🔄 もう一度"): st.session_state.answered = False; st.rerun()

# --- 5. 日本史史料問題 ---
elif subject == "日本史史料問題攻略":
    st.warning("⚠️ 「史料集成」から重要史料を抜粋して空欄補充にしています。")
    st.markdown(f'<div class="card violet-card"><b>【史料文】</b><br>{row["question"]}</div>', unsafe_allow_html=True)
    st.markdown('<div class="guide-text">⚠️ 【　】は史料の出典を表しています。</div>', unsafe_allow_html=True)
    ans_raw = str(row["answer"])
    correct_list = [a.strip() for a in ans_raw.split("/") if a.strip()]
    user_inputs = []
    cols = st.columns(min(len(correct_list), 3))
    for i, corr in enumerate(correct_list):
        user_inputs.append(cols[i % len(cols)].text_input(f"空欄 {chr(65+i)}", key=f"s_{idx}_{i}"))
    if st.button("解答する", disabled=st.session_state.answered): st.session_state.answered = True; st.rerun()
    if st.session_state.answered:
        for i, (u, c) in enumerate(zip(user_inputs, correct_list)):
            if clean_text(u) == clean_text(c): st.success(f"{chr(65+i)}: 正解! ({c})")
            else: st.error(f"{chr(65+i)}: 不正解. 正解: {c}")
        if pd.notna(row.get("explanation")): st.markdown(f'<div class="exp-card">{row["explanation"]}</div>', unsafe_allow_html=True)
        st.write("---")
        c1, c2 = st.columns(2)
        if c1.button("✅ 次へ"): st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
        if c2.button("🔄 もう一度"): st.session_state.answered = False; st.rerun()

# --- 6. その他（一問一答・生物） ---
else:
    if subject == "生物一問一答": card_c = "green-card"
    elif "日本史" in subject: card_c = "pink-card"
    else: card_c = "cyan-card"
    
    st.markdown(f'<div class="card {card_c}"><b>{row["question"]}</b></div>', unsafe_allow_html=True)
    
    if subject == "生物一問一答":
        st.warning("⚠️理系用のものをそのまま移植しています。必要なところだけ使ってください。共通テストは用語を直接問われるわけではないので、「考える」訓練を忘れずに。")
        if not st.session_state.answered:
            if st.button("答えを確認する"): st.session_state.answered = True; st.rerun()
        else:
            ans_raw = str(row["answer"])
            exp_raw = str(row["explanation"]) if pd.notna(row.get("explanation")) else ""
            display_text = f"【正解】\n{ans_raw}"
            if exp_raw:
                display_text += f"\n\n【解説】\n{exp_raw}"
            
            st.success(display_text)
            st.markdown('<style>.stAlert div { font-family: serif !important; white-space: pre-wrap !important; }</style>', unsafe_allow_html=True)
            
            st.write("---")
            c1, c2 = st.columns(2)
            if c1.button("✅ 次へ"): st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
            if c2.button("🔄 もう一度"): st.session_state.answered = False; st.rerun()
    else:
        u_in = st.text_input("答えを入力", key=f"in_{idx}")
        if st.button("解答する", disabled=st.session_state.answered): st.session_state.answered = True; st.rerun()
        if st.session_state.answered:
            ans_raw = str(row["answer"])
            if clean_text(u_in) in [clean_text(a) for a in ans_raw.split("/")]: st.success(f"正解！ ({ans_raw})")
            else: st.error(f"不正解... 正解：{ans_raw}")
            if pd.notna(row.get("explanation")): st.markdown(f'<div class="exp-card">{row["explanation"]}</div>', unsafe_allow_html=True)
            st.write("---")
            c1, c2 = st.columns(2)
            if c1.button("✅ 次へ"): st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
            if c2.button("🔄 もう一度"): st.session_state.answered = False; st.rerun()
