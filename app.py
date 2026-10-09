import io
import json
import pandas as pd
import plotly.express as px
import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
from collections import Counter
from itertools import combinations
from wordcloud import WordCloud

from rparser.pipeline import parse_resume
from rparser import db, matcher
from rparser.extras import anonymize, github_enrich, find_duplicates
from rparser.llm_parser import llm_parse, compare
from rparser.report import build_report_pdf

st.set_page_config(page_title="ResuMate", layout="wide", page_icon="📄")
@st.cache_resource
def _clear_once():
    db.clear_all()
    return True

_clear_once()
db_rows = db.all_candidates()

# ---------- sidebar ----------
st.sidebar.title("📄 ResuMate")
role = st.sidebar.radio("View as", ["Recruiter", "Candidate"])
blind = st.sidebar.toggle("Blind screening (hide personal info)", value=False)

def display_name(c):
    return f"Candidate #{c['id']}" if blind else (c.get("name") or c["filename"])

def _set(cid, status):
    db.set_status(cid, status)
    st.toast(f"Marked as {status}")

# =====================================================================
# CANDIDATE VIEW
# =====================================================================
if role == "Candidate":
    st.title("Check your resume")
    f = st.file_uploader("Upload your resume", type=["pdf", "docx", "txt", "png", "jpg"])
    jd = st.text_area("Paste a target job description (optional)")
    if f:
        r = parse_resume(f.read(), f.name)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("ATS score", f"{r['ats']['ats_score']}/100")
        c2.metric("Experience", f"{r['total_years']} yrs")
        c3.metric("Level", r["seniority"])
        c4.metric("Domain", r["domain"].split(" / ")[0])
        st.caption(f"Full domain: {r['domain']}")
        
        st.subheader("Issues & suggestions")
        for i in r["ats"]["issues"]:
            st.warning(i)
        for t in r["ats"]["tips"]:
            st.info(t)
        if r["ats"]["weak_bullets"]:
            st.write("**Weak bullets**")
            st.dataframe(pd.DataFrame(r["ats"]["weak_bullets"]), use_container_width=True)
        if r["ats"]["possible_typos"]:
            st.caption("Possible typos: " + ", ".join(r["ats"]["possible_typos"]))

        cats = {k: len(v) for k, v in r["skill_categories"].items()}
        if cats:
            fig = px.line_polar(pd.DataFrame({"cat": list(cats), "n": list(cats.values())}),
                                r="n", theta="cat", line_close=True, title="Skill radar")
            fig.update_traces(fill="toself")
            st.plotly_chart(fig, use_container_width=True)

        if r["experience"]:
            st.subheader("Career timeline")
            tl = pd.DataFrame(r["experience"])
            fig = px.timeline(tl, x_start="start", x_end="end", y="title_company",
                              color="title_company")
            fig.update_yaxes(autorange="reversed", title="")
            fig.update_layout(showlegend=False, height=120 + 70 * len(tl))
            st.plotly_chart(fig, use_container_width=True)

        if jd:
            m = matcher.match(r, jd)
            st.subheader(f"Job match: {m['score']}%")
            st.success("Matched: " + (", ".join(m["matched"]) or "none"))
            st.error("Missing: " + (", ".join(m["missing"]) or "none"))
        st.subheader("Estimated salary band")
        st.write(f"{r['salary']['min_lpa']} - {r['salary']['max_lpa']} LPA (rough heuristic)")

        st.download_button("⬇ Download report (PDF)", build_report_pdf(r, m if jd else None),
                           "resume_report.pdf", "application/pdf")
    st.stop()

# =====================================================================
# RECRUITER VIEW
# =====================================================================
tabs = st.tabs(["⬆ Upload", "👥 Candidates", "🎯 Match & Rank", "⚖ Compare",
                "📊 Analytics", "🤖 LLM vs Rule-based", "🔎 Tools"])

# ---- Upload ----
with tabs[0]:
    files = st.file_uploader("Drag & drop resumes", accept_multiple_files=True,
                             type=["pdf", "docx", "txt", "png", "jpg"])
    if files and st.button("Parse all"):
        bar = st.progress(0.0)
        for i, f in enumerate(files):
            try:
                db.save(f.name, parse_resume(f.read(), f.name))
            except Exception as e:
                st.error(f"{f.name}: {e}")
            bar.progress((i + 1) / len(files))
        st.success("Done")
        st.rerun()

# ---- Candidates ----
with tabs[1]:
    if not db_rows:
        st.info("Upload resumes first.")
    else:
        all_sk = sorted({s for c in db_rows for s in c["skills"]})
        c1, c2, c3, c4 = st.columns(4)
        sk = c1.multiselect("Skills (all required)", all_sk)
        min_y = c2.slider("Min experience (yrs)", 0.0, 20.0, 0.0)
        lvl = c3.multiselect("Seniority", ["Fresher", "Junior", "Mid-level", "Senior"])
        q = c4.text_input("Search name / text")

        def keep(c):
            return (all(s in c["skills"] for s in sk) and c["total_years"] >= min_y
                    and (not lvl or c["seniority"] in lvl)
                    and (not q or q.lower() in c["raw_text"].lower()))
        rows = [c for c in db_rows if keep(c)]
        df = pd.DataFrame([{
            "ID": c["id"], "Name": display_name(c),
            "Email": "hidden" if blind else c["email"],
            "Years": c["total_years"], "Level": c["seniority"], "Domain": c["domain"],
            "ATS": c["ats"]["ats_score"], "Skills": ", ".join(c["skills"][:6]),
            "Status": c["status"]} for c in rows])
        st.dataframe(df.sort_values("ATS", ascending=False) if len(df) else df, use_container_width=True)
        if len(df):
            buf = io.BytesIO()
            df.to_excel(buf, index=False)
            st.download_button("Export to Excel", buf.getvalue(), "candidates.xlsx")

        st.divider()
        pick = st.selectbox("Open candidate", [c["id"] for c in rows], format_func=lambda i: next(
            display_name(c) for c in rows if c["id"] == i)) if rows else None
        if pick:
            c = next(x for x in rows if x["id"] == pick)
            left, right = st.columns(2)
            with left:
                st.subheader("Resume text" + (" (anonymized)" if blind else ""))
                st.text_area("", anonymize(c["raw_text"], c) if blind else c["raw_text"], height=450)
            with right:
                st.subheader("Extracted data")
                st.write(c["summary"])
                st.json({k: c[k] for k in ["name", "email", "phone", "location", "skills", "education",
                                           "experience", "projects", "certifications"]} if not blind else
                        {k: c[k] for k in ["skills", "education", "experience", "projects"]})
                st.write("**Salary band:**", f"{c['salary']['min_lpa']}-{c['salary']['max_lpa']} LPA")
                if c["unverified_skills"]:
                    st.warning("Skills claimed but not evidenced: " + ", ".join(c["unverified_skills"]))
                if c["career"]["gaps"]:
                    st.warning(f"Career gaps: {c['career']['gaps']}")
                if c["career"]["job_hopping"]:
                    st.warning("Possible job hopping")
                with st.expander("Interview questions"):
                    for qn in c["interview_questions"]:
                        st.write("•", qn)
                if c.get("github") and st.button("Enrich from GitHub"):
                    st.json(github_enrich(c["github"]))
                s1, s2, s3 = st.columns(3)
                st.download_button("⬇ Download candidate report (PDF)",
                                   build_report_pdf(c, anonymous=blind),
                                   f"candidate_{pick}_report.pdf", "application/pdf")
                st.write("**Current status:**", c["status"])
                if s1.button("✅ Shortlist"):
                    db.set_status(pick, "shortlisted"); st.rerun()
                if s2.button("❌ Reject"):
                    db.set_status(pick, "rejected"); st.rerun()
                if s3.button("🗑 Delete"):
                    db.delete(pick); st.rerun()

# ---- Match & Rank ----
with tabs[2]:
    jd = st.text_area("Job description", height=180)
    if jd and db_rows and st.button("Rank candidates"):
        lb = pd.DataFrame(matcher.rank(db_rows, jd))
        if blind:
            lb["name"] = lb["id"].map(lambda i: f"Candidate #{i}")
        st.dataframe(lb, use_container_width=True)
        st.plotly_chart(px.bar(lb, x="name", y="score", title="Match leaderboard"), use_container_width=True)
    st.divider()
    query = st.text_input("Semantic search (e.g. 'ML engineer with NLP experience')")
    if query and db_rows:
        st.dataframe(pd.DataFrame(matcher.semantic_search(db_rows, query)), use_container_width=True)

# ---- Compare ----
with tabs[3]:
    if len(db_rows) >= 2:
        ids = st.multiselect("Pick 2-3 candidates", [c["id"] for c in db_rows], max_selections=3,
                             format_func=lambda i: display_name(next(c for c in db_rows if c["id"] == i)))
        if len(ids) >= 2:
            cols = st.columns(len(ids))
            for col, i in zip(cols, ids):
                c = next(x for x in db_rows if x["id"] == i)
                col.subheader(display_name(c))
                col.metric("Experience", f"{c['total_years']} yrs")
                col.metric("ATS", c["ats"]["ats_score"])
                col.write(f"**{c['seniority']} · {c['domain']}**")
                col.write(", ".join(c["skills"]))

# ---- Analytics ----
with tabs[4]:
    if db_rows:
        a, b = st.columns(2)
        counts = Counter(s for c in db_rows for s in c["skills"])
        top = pd.DataFrame(counts.most_common(15), columns=["skill", "count"])
        a.plotly_chart(px.bar(top, x="count", y="skill", orientation="h", title="Top skills"), use_container_width=True)
        wc = WordCloud(width=700, height=400, background_color="white").generate_from_frequencies(counts)
        fig, ax = plt.subplots(); ax.imshow(wc); ax.axis("off"); b.pyplot(fig)

        a, b, c_ = st.columns(3)
        a.plotly_chart(px.histogram(pd.DataFrame(db_rows), x="total_years", title="Experience distribution"),
                       use_container_width=True)
        deg = Counter((e["degree"].upper() for c in db_rows for e in c["education"][:1]))
        b.plotly_chart(px.pie(names=list(deg), values=list(deg.values()), title="Education"), use_container_width=True)
        dom = Counter(c["domain"] for c in db_rows)
        c_.plotly_chart(px.pie(names=list(dom), values=list(dom.values()), title="Domains"), use_container_width=True)

        st.subheader("Skill co-occurrence network")
        G = nx.Graph()
        for c in db_rows:
            for s1, s2 in combinations(sorted(c["skills"]), 2):
                w = G[s1][s2]["weight"] + 1 if G.has_edge(s1, s2) else 1
                G.add_edge(s1, s2, weight=w)
        if G.number_of_edges():
            fig, ax = plt.subplots(figsize=(8, 6))
            nx.draw_networkx(G, nx.spring_layout(G, seed=1), ax=ax, node_size=300, font_size=7,
                             width=[G[u][v]["weight"] * 0.5 for u, v in G.edges()])
            ax.axis("off"); st.pyplot(fig)

        locs = Counter(c["location"] for c in db_rows if c["location"])
        if locs:
            st.plotly_chart(px.bar(x=list(locs), y=list(locs.values()), title="Candidate locations"),
                            use_container_width=True)

# ---- LLM vs Rule-based ----
with tabs[5]:
    st.caption("Needs OPENROUTER_API_KEY in your .env file.")
    if db_rows:
        pick = st.selectbox("Resume", [c["id"] for c in db_rows], key="llm",
                            format_func=lambda i: display_name(next(c for c in db_rows if c["id"] == i)))
        if st.button("Run LLM parser"):
            c = next(x for x in db_rows if x["id"] == pick)
            try:
                res = llm_parse(c["raw_text"])
                a, b = st.columns(2)
                a.subheader("Rule-based / spaCy"); a.json({k: c[k] for k in ["name", "email", "skills", "total_years"]})
                b.subheader("LLM"); b.json(res)
                st.json(compare(c, res))
            except Exception as e:
                st.error(e)

# ---- Tools ----
with tabs[6]:
    st.subheader("Duplicate / plagiarism detection")
    thr = st.slider("Similarity threshold", 0.5, 1.0, 0.85)
    dups = find_duplicates(db_rows, thr)
    st.dataframe(pd.DataFrame(dups, columns=["Resume A", "Resume B", "Similarity"])) if dups else st.write("No duplicates found.")