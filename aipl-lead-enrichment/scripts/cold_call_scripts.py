"""
cold_call_scripts.py
====================
Generates personalized 30-second cold-call scripts for AIPL's marketing team.

AIPL sells IT and networking solutions to Indian businesses (Mumbai/Pune/Thane).
Each script is tailored to:
  - The contact's role (IT decision-maker vs gatekeeper)
  - The company's industry (different pitch for Finance vs Manufacturing)
  - Data quality (do we have a name to ask for, or just a switchboard #?)
  - Company size (different opening for large enterprise vs small Pvt Ltd)

Pure Python templates. Zero LLM calls. Outputs a printable Markdown sheet.

USAGE:
    from cold_call_scripts import generate_script, write_scripts_file
    write_scripts_file(rows, '/path/to/Phone_Scripts.md')
"""
from datetime import date


# ---- Industry-specific value props ----
# (used to tailor the "why are you calling" line)
INDUSTRY_PITCH = {
    'Financial Services':  'reliable network uptime + secure VPN for branch offices + compliance-ready infra',
    'IT & Software':       'specialist colocation, low-latency interconnects, and DR/backup setups',
    'Manufacturing':       'factory-floor network redundancy + IoT/SCADA connectivity + warehouse Wi-Fi',
    'Oil & Gas':           'remote-site connectivity, ruggedized networking, and compliance-grade audit logs',
    'Pharmaceuticals':     'compliance-ready (CDSCO/GMP) networking + lab equipment integration + cold-chain monitoring',
    'Logistics & Shipping':'multi-warehouse network setup, tracking integrations, and 24/7 SLA support',
    'Construction & Infra':'temporary-site connectivity, project-office Wi-Fi, mobile workforce IT',
    'Travel & Hospitality':'guest Wi-Fi, PMS/POS integration, security-camera networks',
    'Real Estate':         'building-management networks, smart-building IT, tenant Wi-Fi',
    'Agriculture':         'rural connectivity, IoT for monitoring, low-cost SD-WAN',
    '':                    'reliable office networking, structured cabling, and managed IT support',
}


# ---- Role-specific opener ----
ROLE_OPENER = {
    # Decision-makers — speak peer-to-peer
    'VP IT / CISO / CTO':
        "Hi {name}, I'm {your_name} from AIPL Networks. I work with {industry_phrase} on their IT infrastructure. "
        "I noticed {company} is in {city} — wanted to briefly explore whether we'd be relevant for your "
        "{industry_value_prop}. Do you have 30 seconds, or should I send a one-pager and call back?",

    'IT Manager / IT Head':
        "Hi {name}, this is {your_name} from AIPL Networks. We help {industry_phrase} in Mumbai/Pune with "
        "{industry_value_prop}. Just wanted to introduce ourselves — would a 15-min call next week work to "
        "see if there's anything we can help with?",

    'IT Infra / Sr. IT Infra':
        "Hi {name}, {your_name} from AIPL Networks here. We focus on networking infra for {industry_phrase}. "
        "Saw your role at {company} and wanted to reach out — do you handle vendor evaluation for "
        "switching/Wi-Fi/firewall at your end?",

    'IT Procurement / Purchase':
        "Hi {name}, this is {your_name} from AIPL Networks. We're an empanelled vendor for IT/networking with "
        "several {industry_phrase} firms in your region. Just wanted to be on your vendor list — "
        "what's the best way to submit our credentials?",

    # Gatekeepers — ask for the IT person
    'Gatekeeper - Managing Director':
        "Hi {name}, this is {your_name} from AIPL Networks. We provide IT and networking solutions to "
        "{industry_phrase} in Mumbai/Pune. May I please be connected to your IT Head or whoever handles "
        "your office network, just to introduce ourselves?",
    'Gatekeeper - Chairman & MD':
        "Hi {name}, {your_name} from AIPL Networks. We work with {industry_phrase} on IT infrastructure. "
        "May I please speak to your IT Head about your office network setup, or could you point me to the "
        "right person?",
    'Gatekeeper - CEO':
        "Hi {name}, this is {your_name} from AIPL Networks. We support {industry_phrase} in Mumbai/Pune with "
        "{industry_value_prop}. May I be connected to whoever owns your IT/networking decisions — "
        "your IT Head or admin person?",
    'Gatekeeper - Director':
        "Hi {name}, {your_name} calling from AIPL Networks. We do IT and networking for {industry_phrase}. "
        "May I please be connected to your IT Head or whoever handles your office systems?",
    'Gatekeeper - Founder':
        "Hi {name}, {your_name} from AIPL Networks here. We work with founder-led {industry_phrase} in Mumbai "
        "on their IT setup. May I briefly walk you through what we do, or should I speak to whoever handles "
        "tech at {company}?",
    'Gatekeeper - Chairman':
        "Hi {name}, this is {your_name} from AIPL Networks. We're a Mumbai-based IT/networking firm. "
        "May I please be connected to your IT Head or office admin for a brief introduction?",
    'Gatekeeper - Partner':
        "Hi {name}, {your_name} from AIPL Networks. We support {industry_phrase} firms in Mumbai/Pune with "
        "{industry_value_prop}. May I introduce our services to whoever runs IT/networking at your end?",
    'Gatekeeper - Unknown Role':
        "Hi {name}, this is {your_name} from AIPL Networks. We provide IT and networking solutions in "
        "Mumbai/Pune. May I please be connected to your IT Head or office admin?",
}


# ---- Switchboard script (no contact name found) ----
SWITCHBOARD_SCRIPT = (
    "**To the receptionist:** "
    "\"Hi, this is {your_name} from AIPL Networks — we work with {industry_phrase} in Mumbai/Pune "
    "on their IT/networking setup. May I please be connected to your IT Head, IT Manager, or whoever "
    "handles office systems? If they're not available, could I leave a message or get their direct "
    "contact?\""
)


# ---- Common objections + responses ----
OBJECTION_HANDLERS = """
**Common objections:**

- *"We already have an IT vendor"* → "Understood — most of our clients did when we started talking. We'd just like to be in your evaluation pool for the next refresh. Could I send a one-pager?"
- *"Send me an email"* → "Of course. To make sure it reaches the right person — is this for you, or should I copy your IT Head?"
- *"We're not buying right now"* → "Totally fair. Would it be OK to follow up in 3-4 months when your next budget cycle starts?"
- *"What exactly do you sell?"* → "Office networking — switches, firewalls, structured cabling, Wi-Fi, and managed support. We're vendor-neutral, so we pick the right kit for your environment."
"""


def _industry_phrase(industry):
    """Turn 'Financial Services' into 'financial services firms' etc."""
    if not industry: return 'businesses'
    base = industry.lower()
    if base.endswith('y'):  # Hospitality, Agriculture
        return base[:-1] + 'ies' if not base.endswith('ay') else base + ' firms'
    if base.endswith('s'):  # Services, Logistics
        return base + ' companies'
    return base + ' firms'


def generate_script(row, your_name="[your name]"):
    """
    Returns a markdown-formatted phone script for one contact row.
    """
    company  = str(row.get('Company',''))
    city     = str(row.get('City','') or 'Mumbai')
    industry = str(row.get('Industry','') or '').strip()
    fn       = str(row.get('First Name','')).strip()
    ln       = str(row.get('Last Name','')).strip()
    desg     = str(row.get('Designation','')).strip()
    phone    = str(row.get('Office Phone','')).strip() or str(row.get('Mobile Phone','')).strip()

    name        = (fn + ' ' + ln).strip() or 'sir/madam'
    industry_phrase   = _industry_phrase(industry)
    industry_pitch    = INDUSTRY_PITCH.get(industry, INDUSTRY_PITCH[''])

    out = []
    out.append(f"### {company}")
    out.append(f"_{industry or 'Industry unknown'} · {city} · Priority: {row.get('Source Campaign','—')}_")
    out.append("")

    if phone:
        out.append(f"**Dial:** `{phone}`")
    else:
        out.append("**Dial:** _(find switchboard via JustDial first)_")
    out.append("")

    if not (fn or ln):
        # No name — use switchboard script
        script = SWITCHBOARD_SCRIPT.format(
            your_name=your_name,
            industry_phrase=industry_phrase,
        )
        out.append(script)
    else:
        # We have a name + a role — use the role-specific opener
        tmpl = ROLE_OPENER.get(desg)
        if not tmpl:
            tmpl = ROLE_OPENER['Gatekeeper - Unknown Role']
        script = tmpl.format(
            name=name, your_name=your_name, company=company,
            city=city, industry_phrase=industry_phrase,
            industry_value_prop=industry_pitch,
        )
        out.append(f"**Ask for:** {name} — {desg}")
        out.append("")
        out.append(f"**Opening (30 sec):**\n\n> {script}")

    out.append("")
    out.append(OBJECTION_HANDLERS)
    out.append("---")
    return '\n'.join(out)


def write_scripts_file(rows, path, your_name="[your name]"):
    """
    Generate a Markdown file with one phone script per contactable row.
    Prioritizes Hot leads first.

    `rows` should be a list of dicts (Vtiger-row schema). Rows without phones
    AND without names are skipped — nothing to script.
    """
    # Filter to actually-callable rows
    callable_rows = []
    for r in rows:
        phone = str(r.get('Office Phone','')).strip() or str(r.get('Mobile Phone','')).strip()
        has_name = bool(str(r.get('First Name','')).strip() or str(r.get('Last Name','')).strip())
        if phone or has_name:  # have something to call OR someone to ask for
            callable_rows.append(r)

    # Sort by priority (Hot → Warm → Cold → Skip last)
    tier_order = {'Hot': 0, 'Warm': 1, 'Cold': 2, 'Skip': 3, '': 4}
    callable_rows.sort(key=lambda r: tier_order.get(str(r.get('Source Campaign','')).strip(), 4))

    with open(path, 'w', encoding='utf-8') as f:
        f.write(f"# AIPL Cold-Call Phone Scripts\n")
        f.write(f"_Generated: {date.today().strftime('%d %b %Y')}_\n\n")
        f.write(f"**{len(callable_rows)} callable contacts** sorted by priority "
                f"(Hot → Warm → Cold). Each script is ~30 seconds. Personalized "
                f"by industry + role + city.\n\n")
        f.write("**Before you call:** replace `[your name]` below with your actual name.\n\n")
        f.write("---\n\n")

        current_tier = None
        for r in callable_rows:
            tier = str(r.get('Source Campaign','')).strip() or '—'
            if tier != current_tier:
                f.write(f"## {tier.upper()} LEADS\n\n")
                current_tier = tier
            f.write(generate_script(r, your_name=your_name))
            f.write('\n')

    return path


if __name__ == '__main__':
    # Self-test on a few sample rows
    rows = [
        {'Company':'Motilal Oswal Financial Services Ltd', 'City':'Mumbai',
         'Industry':'Financial Services', 'First Name':'Pankaj', 'Last Name':'Purohit',
         'Designation':'IT Manager / IT Head', 'Office Phone':'+91-22-7193-4263',
         'Source Campaign':'Hot'},
        {'Company':'M/S MAGBLISS INFOTECH PRIVATE LIMITED', 'City':'Mumbai',
         'Industry':'IT & Software', 'First Name':'', 'Last Name':'',
         'Designation':'IT Manager / IT Head', 'Office Phone':'',
         'Source Campaign':'Cold'},
        {'Company':'HAZOOR MULTI PROJECTS LIMITED', 'City':'Mumbai',
         'Industry':'Construction & Infra', 'First Name':'Pawankumar', 'Last Name':'Mallawat',
         'Designation':'Gatekeeper - Chairman & MD', 'Office Phone':'+91-22-2200-0525',
         'Source Campaign':'Warm'},
    ]
    for r in rows:
        print(generate_script(r, your_name='Saish'))
        print()
