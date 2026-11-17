import re
import pandas as pd
from pypdf import PdfReader
import streamlit as st

# Set up mobile viewport styling
st.set_page_config(
    page_title="Punters Formula Pro", page_icon="🏆", layout="centered"
)

st.title("🏆 Punters' Master Formula Engine")
st.write("---")

# Navigation Tabs for Mobile View
tab1, tab2, tab3 = st.tabs(
    ["📄 PDF Batch Scanner", "🔮 Manual Scratchpad", "📊 Performance Tracker"]
)

# ==========================================
# GLOBAL WEIGHTS SIDEBAR / EXPANDER
# ==========================================
with st.expander("⚙️ Adjust Master Formula Weights (Default Active)", expanded=False):
    st.caption(
        "Fine-tune weights based on track layout conditions. Must total 1.00."
    )
    col1, col2 = st.columns(2)
    with col1:
        speed_w = st.slider("🏎️ Speed / Sectionals %", 0.0, 1.0, 0.35, step=0.05)
        class_w = st.slider("👑 Class / Earnings %", 0.0, 1.0, 0.25, step=0.05)
        pace_w = st.slider("⚡ Pace & Energy %", 0.0, 1.0, 0.20, step=0.05)
    with col2:
        draw_w = st.slider("🚧 Draw / Barrier %", 0.0, 1.0, 0.10, step=0.05)
        rec_w = st.slider("📉 Recency / Form Decay %", 0.0, 1.0, 0.10, step=0.05)

    total_w = round(speed_w + class_w + pace_w + draw_w + rec_w, 2)
    if total_w != 1.0:
        st.warning(
            f"⚠️ Total weights equal {total_w}. Adjust sliders to equal 1.00."
        )

# ==========================================
# TAB 1: COMPUTAFORM PDF BATCH SCANNER
# ==========================================
with tab1:
    st.header("📄 Computaform PDF Auto-Ranker")
    st.write(
        "Upload your Computaform or Sportsbet PDF to extract fields and rank all runners instantly."
    )

    uploaded_file = st.file_uploader("Upload Racecard PDF", type=["pdf"])

    if uploaded_file is not None:
        reader = PdfReader(uploaded_file)
        total_pages = len(reader.pages)
        st.success(f"✅ PDF Loaded! ({total_pages} pages detected)")

        # Page selector so you can scan specific race pages
        selected_page = st.number_input(
            "Select Race Page Number to Scan",
            min_value=1,
            max_value=total_pages,
            value=min(10, total_pages),
        )

        if st.button("🚀 Extract & Rank Race Field"):
            page_text = reader.pages[selected_page - 1].extract_text()

            # Parse Computaform table rows: No | L3 | Name | R-1-2-3 | F3% ... Draw
            # Pattern looks for: Saddle No, Last 3 runs (or blank), Horse Name, Career stats, Earnings, Weight, Draw
            lines = page_text.split("\n")
            extracted_runners = []

            for line in lines:
                # Match standard Computaform runner index lines (e.g., "7 323 NANNIE GOLD 7-0-3-2 71% R86,475...")
                match = re.match(
                    r"^(\d{1,2})\s+([0-9xX▾▲\-]*)\s*([A-Z\s\(\)\'\-]+?)\s+(\d+-\d+-\d+-\d+)\s+(\d+%)",
                    line.strip(),
                )
                if match:
                    no = int(match.group(1))
                    l3 = match.group(2) if match.group(2) else "First Run"
                    name = match.group(3).strip()
                    f3_pct = int(match.group(5).replace("%", ""))

                    # Extract Draw & Merit Rating if visible on the line
                    numbers = re.findall(r"\b\d+\b", line)
                    draw = int(numbers[-2]) if len(numbers) >= 3 else no

                    # Calculate baseline algorithmic metrics (1-100 scale) from extracted Computaform stats
                    # Speed & Class derived from Place% (F3%) and recent form sequence
                    speed_est = min(100, max(35, f3_pct + 15))
                    class_est = min(100, max(40, f3_pct + 10))
                    pace_est = 75 if any(c in l3 for c in ["1", "2", "3"]) else 50
                    draw_est = max(30, 100 - (draw * 5))  # Favors lower draws
                    rec_est = 85 if l3.endswith(("1", "2", "3")) else 55

                    power_score = (
                        (speed_est * speed_w)
                        + (class_est * class_w)
                        + (pace_est * pace_w)
                        + (draw_est * draw_w)
                        + (rec_est * rec_w)
                    )

                    extracted_runners.append({
                        "No": no,
                        "Horse": name,
                        "L3 Form": l3,
                        "Place %": f"{f3_pct}%",
                        "Power Score": round(power_score, 1),
                    })

            if extracted_runners:
                df_results = pd.DataFrame(extracted_runners)
                df_results = df_results.sort_values(
                    by="Power Score", ascending=False
                ).reset_index(drop=True)

                st.subheader("🏆 Master Formula Race Rankings")
                st.dataframe(df_results, use_container_width=True)

                top_pick = df_results.iloc[0]
                st.success(
                    f"🔥 **Top Pick:** #{top_pick['No']} {top_pick['Horse']} ({top_pick['Power Score']} pts)"
                )
                if len(df_results) > 1:
                    next_best = df_results.iloc[1]
                    st.info(
                        f"🥈 **Next Best:** #{next_best['No']} {next_best['Horse']} ({next_best['Power Score']} pts)"
                    )
            else:
                st.warning(
                    "⚠️ No main racecard summary table detected on this page. Try selecting the main race overview page (e.g., Page 10, 15, 18, 22, 26, 30, 34, or 36 in Computaform)."
                )
                with st.expander("View Raw Extracted Text (Debug)"):
                    st.text(page_text[:1500])

# ==========================================
# TAB 2: MANUAL SCRATCHPAD (1 RUNNER AT A TIME)
# ==========================================
with tab2:
    st.header("🔮 Manual Runner Scratchpad")
    st.caption(
        "Use this to manually override or test individual horses with custom ratings."
    )

    with st.form("ranking_form"):
        runner_name = st.text_input(
            "Runner Name / Number", placeholder="e.g., 7 Trip To Camelot"
        )

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            s_score = st.number_input("Speed", 1, 100, 50)
        with c2:
            c_score = st.number_input("Class", 1, 100, 50)
        with c3:
            p_score = st.number_input("Pace", 1, 100, 50)
        with c4:
            d_score = st.number_input("Draw", 1, 100, 50)
        with c5:
            r_score = st.number_input("Form", 1, 100, 50)

        submit_runner = st.form_submit_button("Calculate Power Score")

    if submit_runner:
        power_score = (
            (s_score * speed_w)
            + (c_score * class_w)
            + (p_score * pace_w)
            + (d_score * draw_w)
            + (r_score * rec_w)
        )
        st.metric(
            label=f"📊 {runner_name} Master Power Score",
            value=f"{round(power_score, 1)} pts",
        )

# ==========================================
# TAB 3: RESULTS & CONVERGENCE TAB
# ==========================================
with tab3:
    st.header("📊 Performance Logs & Results Audit")
    st.write("Log actual outcomes to track app deviation trends over time.")

    if "results_log" not in st.session_state:
        st.session_state.results_log = pd.DataFrame(
            columns=[
                "Meeting",
                "Race",
                "Predicted Winner",
                "Actual Winner",
                "App Accuracy Status",
            ]
        )

    with st.form("results_form"):
        rc_meeting = st.selectbox(
            "Meeting Circuit",
            ["Kenilworth", "Durbanville", "Sha Tin", "Turffontein", "UK Circuit"],
        )
        rc_num = st.number_input("Race Number", 1, 12, 1)
        pred_win = st.text_input("App Selection (Top Pick)")
        act_win = st.text_input("Actual Winner on Track")

        log_button = st.form_submit_button("Log Race Result")

    if log_button:
        status = (
            "🎯 STRIKE"
            if pred_win.lower().strip() == act_win.lower().strip()
            else "❌ DEVIATION"
        )
        new_row = pd.DataFrame([{
            "Meeting": rc_meeting,
            "Race": rc_num,
            "Predicted Winner": pred_win,
            "Actual Winner": act_win,
            "App Accuracy Status": status,
        }])
        st.session_state.results_log = pd.concat(
            [st.session_state.results_log, new_row], ignore_index=True
        )
        st.success("Race results tracked successfully!")

    st.subheader("Historical Challenge Session Logs")
    st.dataframe(st.session_state.results_log, use_container_width=True)

    if not st.session_state.results_log.empty:
        strikes = len(
            st.session_state.results_log[
                st.session_state.results_log["App Accuracy Status"] == "🎯 STRIKE"
            ]
        )
        total_logged = len(st.session_state.results_log)
        strike_rate = (strikes / total_logged) * 100
        st.metric("🎯 Ongoing Master Formula Win Rate", f"{round(strike_rate, 1)}%")
