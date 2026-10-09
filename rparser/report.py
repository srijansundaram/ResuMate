from fpdf import FPDF


def _t(s) -> str:
    """fpdf core fonts are latin-1 only, so swap common symbols."""
    s = str(s or "")
    for a, b in {"–": "-", "—": "-", "•": "-", "’": "'", "‘": "'", "“": '"', "”": '"', "·": "|"}.items():
        s = s.replace(a, b)
    return s.encode("latin-1", "replace").decode("latin-1")


def build_report_pdf(r: dict, match: dict | None = None, anonymous: bool = False) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    def h(text):
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, _t(text), new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(180, 180, 180)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(2)

    def p(text, bold=False):
        pdf.set_font("Helvetica", "B" if bold else "", 10)
        pdf.multi_cell(0, 6, _t(text), new_x="LMARGIN", new_y="NEXT")

    def bullets(items):
        for i in items or ["None"]:
            p(f"- {i}")

    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 10, _t("Candidate" if anonymous else (r.get("name") or "Unknown")),
             new_x="LMARGIN", new_y="NEXT")
    if not anonymous:
        p(f"{r.get('email') or ''} | {r.get('phone') or ''}")
    p(r["summary"])
    p(f"ATS: {r['ats']['ats_score']}/100   Experience: {r['total_years']} yrs   "
      f"Level: {r['seniority']}   Domain: {r['domain']}", bold=True)

    if match:
        h(f"Job match: {match['score']}%")
        p("Matched: " + ", ".join(match["matched"]))
        p("Missing: " + ", ".join(match["missing"]))

    h("Skills")
    for k, v in r["skill_categories"].items():
        p(f"{k}: {', '.join(v)}")
    h("Experience")
    bullets([f"{j['title_company']} ({j['start']} to {j['end']})" for j in r["experience"]])
    h("Education")
    bullets([e["line"] for e in r["education"]])
    h("Issues")
    bullets(r["ats"]["issues"])
    h("Suggestions")
    bullets(r["ats"]["tips"])
    h("Estimated salary band")
    p(f"{r['salary']['min_lpa']} - {r['salary']['max_lpa']} LPA (heuristic)")
    h("Interview questions")
    bullets(r["interview_questions"])
    return bytes(pdf.output())