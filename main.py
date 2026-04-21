import streamlit as st
import pandas as pd
import random
import re

# --- 1. データの読み込み関数 ---
def load_data(file_name, subject):
    try:
        # UTF-8 (BOM付き) で読み込み
        df = pd.read_csv(file_name, engine='python', encoding='utf-8-sig')
        return df
    except Exception:
        # ヘッダーがない古い形式などの場合
        try:
            return pd.read_csv(file_name, engine='python', encoding='utf-8-sig', header=None)
        except:
            return None

# --- 2. 画面設定とCSS ---
st.set_page_config(page_title="文系科目は、ゆずらない", layout="centered")
st.markdown("""
    <style>
    .main { background-color: #fdfaf5; }
    .highlight-target { color: #2e7d32; font-weight: bold; border-bottom: 2px solid #2e7d32; }
    .sentence-box { background-color: #f0f4f0; padding: 25px; border-radius: 10px; border-left: 8px solid #2e7d32; margin-bottom: 20px; }
    .stButton button { font-size: 16px !important; min-height: 3.5em; }
    </style>
    """, unsafe_allow_html=True)

st.title("🔥 文系科目は、ゆずらない")

# --- 3. サイドバー：科目選択 ---
selected_subject = st.sidebar.selectbox(
    "学習する科目を選択",
    ["選択してください", "英単語", "古文単語", "日本史一問一答"]
)

subject_map = {
    "古文単語": "kobun350.csv",
    "英単語": "final_tango_list.csv",
    "日本史一問一答": "nihonshi.csv"
}

if selected_subject == "選択してください":
    st.info("サイドバーから科目を選択して開始してください。")
    st.stop()

# --- 4. 科目別データロードとフィルタリング ---
# 初回読み込み or 科目変更時
if 'last_sub' not in st.session_state or st.session_state.last_sub != selected_subject:
    st.session_state.last_sub = selected_subject
    st.session_state.raw_df = load_data(subject_map[selected_subject], selected_subject)
    st.session_state.idx = 0
    st.session_state.score = 0
    st.session_state.answered = False
    st.session_state.new_ques = True

df = st.session_state.raw_df
if df is None:
    st.error(f"⚠️ '{subject_map[selected_subject]}' が見つかりません。")
    st.stop()

# --- 【英単語専用】レベル選択機能の復活 ---
current_df = df
if selected_subject == "英単語":
    st.sidebar.header("⚙️ 英単語設定")
    if 'level' in df.columns:
        unique_levels = df['level'].unique().tolist()
        level_options = ["All (1-2027)"] + unique_levels
        level_sel = st.sidebar.selectbox("レベルを選択", level_options)
        
        if 'last_level' not in st.session_state or st.session_state.last_level != level_sel:
            st.session_state.last_level = level_sel
            filtered_df = df if level_sel == "All (1-2027)" else df[df['level'] == level_sel]
            st.session_state.questions = filtered_df.sample(frac=1).reset_index(drop=True)
            st.session_state.idx = 0
            st.session_state.score = 0
    else:
        if 'questions' not in st.session_state:
            st.session_state.questions = df.sample(frac=1).reset_index(drop=True)
else:
    # 古文・日本史のシャッフル
    if 'questions' not in st.session_state or st.session_state.last_sub != selected_subject:
        st.session_state.questions = df.sample(frac=1).reset_index(drop=True)

# --- 5. クイズ本編 ---
q_df = st.session_state.questions
if st.session_state.idx < len(q_df):
    row = q_df.iloc[st.session_state.idx]
    st.sidebar.write(f"進捗: {st.session_state.idx + 1} / {len(q_df)}")
    st.progress((st.session_state.idx + 1) / len(q_df))

    # --- A. 日本史：記述入力モード ---
    if selected_subject == "日本史一問一答":
        # 提示された日本史コードの仕様: 0列目が問題、1列目が答え、2列目が時代
        q_text = str(row.iloc[0])
        correct_answer = str(row.iloc[1]).strip()
        
        if len(row) >= 3 and pd.notna(row.iloc[2]):
            st.info(f"時代：{row.iloc[2]}")

        st.markdown(f'<div class="sentence-box"><p style="font-size:20px;"><b>問題：</b>{q_text}</p></div>', unsafe_allow_html=True)

        with st.form(key='nihonshi_form', clear_on_submit=True):
            user_input = st.text_input("答えを漢字で入力してください", key="jp_input")
            submit_button = st.form_submit_button(label='解答する')

        if submit_button:
            st.session_state.answered = True
            if user_input.strip() == correct_answer:
                st.session_state.last_res = "correct"
                st.session_state.score += 1
            else:
                st.session_state.last_res = "incorrect"
        
        if st.session_state.answered:
            if st.session_state.last_res == "correct":
                st.success(f"✨ 正解！！ 「{correct_answer}」")
            else:
                st.error(f"❌ ぶー！ 正解は 「{correct_answer}」 でした。")
            
            if st.button("次の問題へ 👉"):
                st.session_state.idx += 1
                st.session_state.answered = False
                st.rerun()

    # --- B. 英単語・古文単語：選択肢モード ---
    else:
        # 列の割り当て（英単語はカラム名、古文はインデックスで取得）
        if selected_subject == "英単語":
            target = str(row['question']).strip()
            correct_ans = str(row['all_answers']).strip()
            dummies_raw = str(row['dummy_pool']).strip()
            sentence = str(row['sentence']).strip() if pd.notna(row['sentence']) else ""
            translation = str(row['translation']).strip() if pd.notna(row['translation']) else ""
        else: # 古文
            target = str(row.iloc[0]).strip()
            correct_ans = str(row.iloc[1]).strip()
            dummies_raw = str(row.iloc[2]).strip()
            sentence = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ""
            translation = str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else ""

        if st.session_state.new_ques:
            # 選択肢の作成
            correct_list = [c.strip() for c in correct_ans.split(',')]
            dummy_list = [d.strip() for d in dummies_raw.split(',') if d.strip()]
            display_correct = random.choice(correct_list)
            display_dummies = random.sample(dummy_list, min(len(dummy_list), 3))
            choices = list(set([display_correct] + display_dummies))
            random.shuffle(choices)
            st.session_state.shuffled_choices = choices
            st.session_state.new_ques = False

        # 問題文表示
        if selected_subject == "英単語":
            pattern = re.compile(re.escape(target), re.IGNORECASE)
            highlighted = pattern.sub(f'<span style="color:red; font-weight:bold; border-bottom:2px solid red;">{target}</span>', sentence)
            st.markdown(f'<div class="sentence-box"><p style="font-size:22px;">{highlighted}</p></div>', unsafe_allow_html=True)
        else: # 古文
            h_target = f'<span class="highlight-target">{target}</span>'
            display_text = sentence.replace(target, h_target) if target in sentence else f"{sentence}<br>({h_target})"
            st.markdown(f'<div class="sentence-box"><p style="font-size:22px;">{display_text}</p></div>', unsafe_allow_html=True)

        # 選択肢ボタン
        for choice in st.session_state.shuffled_choices:
            if st.button(choice, use_container_width=True, disabled=st.session_state.answered):
                st.session_state.answered = True
                st.session_state.last_res = "correct" if choice in correct_ans.split(',') else "incorrect"
                if st.session_state.last_res == "correct": st.session_state.score += 1
                st.rerun()

        if st.session_state.answered:
            if st.session_state.last_res == "correct":
                st.success("✨ 正解！")
            else:
                st.error(f"❌ 不正解... 正解は 「{correct_ans}」")
            
            # 解説・現代語訳の表示
            if translation:
                with st.expander("📖 現代語訳・詳細を見る", expanded=True):
                    st.write(translation)

            if st.button("次の問題へ 👉", type="primary"):
                st.session_state.idx += 1
                st.session_state.answered = False
                st.session_state.new_ques = True
                st.rerun()
else:
    st.balloons()
    st.write(f"## 🎉 {selected_subject} 全問終了！")
    st.write(f"スコア: {st.session_state.score} / {len(q_df)}")
    if st.button("もう一度挑戦"):
        st.session_state.idx = 0
        st.session_state.score = 0
        st.session_state.questions = q_df.sample(frac=1).reset_index(drop=True)
        st.rerun()
