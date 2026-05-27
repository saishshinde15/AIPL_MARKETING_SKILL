"""
email_templates.py
==================
Personalized cold email templates for AIPL outreach.

For every contact with a verified email + name, generates a 4-line cold email
tailored to industry + role. Pure Python, no LLM calls.

Output format: a Markdown file the team can copy-paste from.

USAGE:
    from email_templates import write_emails_file
    write_emails_file(rows, '/path/to/Email_Templates.md')
"""
from datetime import date


# ---- Per-industry value prop (one short sentence each) ----
INDUSTRY_VALUE = {
    'Financial Services':  ("we help banks, NBFCs, and brokerages keep branch-office networks "
                           "rock-solid (uptime SLA, secure VPN, compliance-ready audit logs)"),
    'IT & Software':       ("we provide specialist co-location, low-latency interconnects, "
                           "and disaster-recovery setups to tech firms"),
    'Manufacturing':       ("we set up reliable factory-floor networks, IoT/SCADA connectivity, "
                           "and warehouse Wi-Fi for industrial firms"),
    'Oil & Gas':           ("we deliver remote-site connectivity, ruggedized networking gear, "
                           "and compliance-grade audit infrastructure"),
    'Pharmaceuticals':     ("we build compliance-ready (CDSCO/GMP) networks, integrate lab "
                           "equipment, and provide cold-chain monitoring"),
    'Logistics & Shipping':("we connect multi-warehouse networks, integrate fleet/cargo tracking, "
                           "and offer 24/7 SLA support"),
    'Construction & Infra':("we provide temporary-site connectivity, project-office Wi-Fi, "
                           "and mobile-workforce IT for construction firms"),
    'Travel & Hospitality':("we set up guest Wi-Fi, PMS/POS integrations, and security-camera "
                           "networks for hotels and travel firms"),
    'Real Estate':         ("we provide building-management networks, smart-building IT, "
                           "and tenant Wi-Fi infrastructure"),
    'Agriculture':         ("we offer rural connectivity, IoT for crop/livestock monitoring, "
                           "and low-cost SD-WAN solutions"),
    '':                    ("we provide office networking, structured cabling, and managed IT "
                           "support to Mumbai/Pune businesses"),
}


# ---- Per-role opening line (matches the contact's seniority) ----
ROLE_OPENING = {
    'VP IT / CISO / CTO':
        "I've been working with CIOs at {industry_short} firms in Mumbai and thought it was worth a quick intro.",
    'IT Manager / IT Head':
        "I've been working with IT Heads at {industry_short} firms in Mumbai and wanted to briefly introduce ourselves.",
    'IT Infra / Sr. IT Infra':
        "I work with infrastructure leads at {industry_short} firms in Mumbai/Pune and wanted to introduce AIPL Networks.",
    'IT Procurement / Purchase':
        "Wanted to be on your IT-vendor list — we work with {industry_short} firms across Mumbai/Pune.",
    'Gatekeeper - Managing Director':
        "Apologies for the direct email — I wasn't sure who handles IT at {company_short}. Could you point me to your IT Head?",
    'Gatekeeper - Chairman & MD':
        "Apologies for the direct outreach — I'm trying to identify the right person for an IT-infrastructure conversation at {company_short}.",
    'Gatekeeper - CEO':
        "Quick intro — I work with {industry_short} firms in Mumbai/Pune. Could you point me to whoever handles IT/networking decisions?",
    'Gatekeeper - Director':
        "Apologies for emailing you directly — could you point me to whoever handles IT/networking at {company_short}?",
    'Gatekeeper - Founder':
        "I work with founder-led {industry_short} businesses in Mumbai/Pune. Wanted to briefly introduce AIPL Networks.",
    'Gatekeeper - Chairman':
        "Apologies for the direct email — I'm trying to reach whoever handles IT/networking at {company_short}.",
    'Gatekeeper - Partner':
        "I work with {industry_short} firms in Mumbai/Pune on their IT setup. Could you direct this to your IT lead?",
    'Gatekeeper - Unknown Role':
        "Apologies — I wasn't sure who at {company_short} handles IT/networking. Could you forward this to the right person?",
}


# ---- Subject lines per role ----
SUBJECT_LINE = {
    'VP IT / CISO / CTO':         "Networking partner for {company_short}",
    'IT Manager / IT Head':       "Quick intro — IT/networking support for {company_short}",
    'IT Infra / Sr. IT Infra':    "Networking + infra for {company_short}",
    'IT Procurement / Purchase':  "Vendor empanelment — AIPL Networks",
    'Gatekeeper - Managing Director': "Quick IT-related question for {company_short}",
    'Gatekeeper - Chairman & MD':     "Brief intro — IT/networking partner",
    'Gatekeeper - CEO':               "IT/networking partner for {company_short}",
    'Gatekeeper - Director':          "IT-vendor intro for {company_short}",
    'Gatekeeper - Founder':           "Quick intro — AIPL Networks",
    'Gatekeeper - Chairman':          "IT-related intro for {company_short}",
    'Gatekeeper - Partner':           "Networking partner for {company_short}",
    'Gatekeeper - Unknown Role':      "IT/networking for {company_short}",
}


def _short_industry(industry):
    """Make 'Financial Services' → 'financial-services' (compact for inline use)."""
    if not industry: return 'mid-size'
    return industry.lower().replace(' & ', '/').replace(' ', '-')


def _short_company(company):
    """Strip 'M/S' + 'Private Limited' etc. so 'M/S Acme PRIVATE LIMITED' → 'Acme'."""
    import re
    n = re.sub(r'\bm/s\s+', '', str(company), flags=re.IGNORECASE)
    n = re.sub(r'\b(private\s+limited|pvt\.?\s*ltd\.?|pvt\.?\s*limited|limited|ltd\.?|llp|'
               r'liability\s+partnership)\b', '', n, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', n).strip(' ,.') or company


def generate_email(row, your_name="[your name]", your_phone="[your phone]"):
    """
    Returns dict: {subject, body} for one contact row.
    Returns None if row doesn't have an email (nothing to send).
    """
    email = str(row.get('Primary Email','')).strip()
    if not email:
        return None
    fn = str(row.get('First Name','')).strip()
    ln = str(row.get('Last Name','')).strip()
    name = fn or 'there'
    company = str(row.get('Company',''))
    company_short = _short_company(company)
    industry = str(row.get('Industry','') or '').strip()
    industry_short = _short_industry(industry)
    desg = str(row.get('Designation','')).strip()

    industry_value = INDUSTRY_VALUE.get(industry, INDUSTRY_VALUE[''])
    opening_tmpl = ROLE_OPENING.get(desg, ROLE_OPENING['Gatekeeper - Unknown Role'])
    opening = opening_tmpl.format(
        industry_short=industry_short, company_short=company_short)

    subject_tmpl = SUBJECT_LINE.get(desg, SUBJECT_LINE['Gatekeeper - Unknown Role'])
    subject = subject_tmpl.format(company_short=company_short)

    # Build the body (4-line cold email)
    body = (
        f"Hi {name},\n\n"
        f"{opening}\n\n"
        f"At AIPL Networks, {industry_value} — we're a Mumbai-based partner for several IT-services brands.\n\n"
        f"Would a 15-minute call next week work to see if we'd be useful to {company_short}? "
        f"Happy to send a one-pager first if that's easier.\n\n"
        f"Best,\n{your_name}\nAIPL Networks · {your_phone}"
    )
    return {'to': email, 'subject': subject, 'body': body}


def write_emails_file(rows, path, your_name="[your name]", your_phone="[your phone]"):
    """
    Generate a Markdown file with one ready-to-send email per row that has an
    email address. Sorted by priority (Hot → Warm → Cold).
    """
    emailable = []
    for r in rows:
        e = generate_email(r, your_name=your_name, your_phone=your_phone)
        if e:
            emailable.append((r, e))

    tier_order = {'Hot': 0, 'Warm': 1, 'Cold': 2, 'Skip': 3, '': 4}
    emailable.sort(key=lambda pair: tier_order.get(
        str(pair[0].get('Source Campaign','')).strip(), 4))

    with open(path, 'w', encoding='utf-8') as f:
        f.write(f"# AIPL Cold-Email Templates\n")
        f.write(f"_Generated: {date.today().strftime('%d %b %Y')}_\n\n")
        f.write(f"**{len(emailable)} contacts with verified emails.** Each template is personalized "
                f"by industry + role. Copy the subject + body, paste into your email client, send.\n\n")
        f.write(f"**Before sending:** replace `[your name]` and `[your phone]` with your actual contact info.\n\n")
        f.write("---\n\n")

        current_tier = None
        for r, e in emailable:
            tier = str(r.get('Source Campaign','')).strip() or '—'
            if tier != current_tier:
                f.write(f"\n## {tier.upper()} LEADS\n\n")
                current_tier = tier
            f.write(f"### {r.get('Company','')}\n")
            f.write(f"_{r.get('Industry','—')} · {r.get('Designation','—')}_\n\n")
            f.write(f"**To:** `{e['to']}`\n\n")
            f.write(f"**Subject:** {e['subject']}\n\n")
            f.write("**Body:**\n\n```\n")
            f.write(e['body'])
            f.write("\n```\n\n---\n\n")
    return path


if __name__ == '__main__':
    rows = [
        {'Company':'Motilal Oswal Financial Services Ltd', 'Industry':'Financial Services',
         'First Name':'Pankaj', 'Last Name':'Purohit',
         'Designation':'IT Manager / IT Head',
         'Primary Email':'pankaj.purohit@motilaloswal.com',
         'Source Campaign':'Hot'},
        {'Company':'M/S CHEMBOND BIOSCIENCES LIMITED', 'Industry':'Pharmaceuticals',
         'First Name':'Manoranjan', 'Last Name':'Mahapatra',
         'Designation':'IT Manager / IT Head',
         'Primary Email':'info@chembondindia.com',
         'Source Campaign':'Hot'},
    ]
    for r in rows:
        e = generate_email(r, your_name='Saish', your_phone='+91-XXXX-XXXXX')
        print(f"To: {e['to']}")
        print(f"Subject: {e['subject']}")
        print(f"---\n{e['body']}\n===\n")
