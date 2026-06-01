"""
lead_brief.py
=============
Generates a 1-page Markdown brief for each Hot/Warm lead — basically a
sales-execution kit per company. The team prints these out and walks into
the meeting with everything pre-loaded.

Output: Hygienic_Leads_Lead_Briefs.md (concatenated Markdown — one section
per company; can be exported to PDF in any markdown viewer).

For each lead the brief includes:
- Company overview (name, industry, city, size signals)
- Verified contact + role + confidence
- Phone script (from cold_call_scripts)
- Email template (from email_templates)
- Suggested approach (call vs email vs LinkedIn)
- Sources cited

Pure Python. No LLM calls. Runs per row in <10ms.
"""
from datetime import date


def _suggested_channel(row):
    """Pick best outreach channel based on what data we have."""
    has_email = bool(str(row.get('Primary Email','')).strip())
    has_phone = bool(str(row.get('Office Phone','')).strip()
                     or str(row.get('Mobile Phone','')).strip())
    has_linkedin = 'LinkedIn:' in str(row.get('Additional Details',''))
    desg = str(row.get('Designation','')).strip()

    if desg.startswith('Gatekeeper') and has_phone:
        return 'Phone (call gatekeeper, ask for IT Head)'
    if has_phone and has_email:
        return 'Email first, then phone follow-up if no response in 3 days'
    if has_phone:
        return 'Phone (no email available)'
    if has_email:
        return 'Email (no phone available)'
    if has_linkedin:
        return 'LinkedIn DM (no email/phone yet)'
    return 'Cold-call switchboard via JustDial (no contact info)'


def _company_size_hint(company_name):
    """
    Structural company-size hint from the legal form — for the team's context.
    Uses ONLY generalizable legal-entity + sector markers (no specific company
    names), so it reads correctly for any company on any file.
    """
    up = (company_name or '').upper()
    if any(k in up for k in ['GOVERNMENT OF', 'GOVT OF', 'MUNICIPAL',
                             'AUTHORITY', 'COMMISSION', 'PUBLIC SECTOR']):
        return 'Government / PSU / authority — large'
    if any(k in up for k in ['CORPORATION LIMITED', 'CORPORATION LTD',
                             'CORPN LIMITED']):
        return 'Corporation (typically large enterprise)'
    if any(k in up for k in ['BANK LIMITED', 'BANK LTD', ' BANK ', 'INSURANCE',
                             'SECURITIES LIMITED', 'ASSET MANAGEMENT',
                             'MUTUAL FUND', 'FINANCE LIMITED', 'CAPITAL LIMITED']):
        return 'Bank / financial institution (large IT spender)'
    if 'PRIVATE LIMITED' in up or 'PVT LTD' in up or 'PVT. LTD' in up or 'PVT LIMITED' in up:
        return 'Private limited (small/mid)'
    if 'LLP' in up or 'LIMITED LIABILITY PARTNERSHIP' in up:
        return 'Limited Liability Partnership (small)'
    if 'OPC' in up or 'ONE PERSON COMPANY' in up:
        return 'One Person Company (micro)'
    if 'LIMITED' in up or up.endswith(' LTD') or up.endswith(' LTD.'):
        return 'Public limited company (listed/mid-size+)'
    return 'Type unknown'


def _extract_source_urls(additional_details):
    """Pull verification source URLs from Additional Details."""
    import re
    if not additional_details: return []
    urls = re.findall(r'https?://[^\s|<>]+', str(additional_details))
    # Dedupe + cap
    seen, out = set(), []
    for u in urls:
        u = u.rstrip('.,;)')
        if u not in seen:
            seen.add(u); out.append(u)
        if len(out) >= 4: break
    return out


def generate_brief(row, your_name="[your name]", your_phone="[your phone]"):
    """Returns a Markdown 1-page brief for one company row."""
    company  = str(row.get('Company',''))
    industry = str(row.get('Industry','') or '—')
    city     = str(row.get('City','') or '—')
    state    = str(row.get('State','') or '—')
    pincode  = str(row.get('Postal Code','') or '—')
    fn       = str(row.get('First Name','')).strip()
    ln       = str(row.get('Last Name','')).strip()
    desg     = str(row.get('Designation','') or '—')
    email    = str(row.get('Primary Email','') or '—')
    phone    = str(row.get('Office Phone','')).strip() or str(row.get('Mobile Phone','')).strip() or '—'
    website  = str(row.get('Website','') or '—')
    tier     = str(row.get('Source Campaign','') or '—')
    ad       = str(row.get('Additional Details',''))

    name_str = (fn + ' ' + ln).strip() or 'No name yet'
    size_hint = _company_size_hint(company)
    channel = _suggested_channel(row)
    sources = _extract_source_urls(ad)

    # Try importing script/email generators for inline content
    try:
        from cold_call_scripts import generate_script
        script_md = generate_script(row, your_name=your_name)
    except ImportError:
        script_md = '_(phone script unavailable — cold_call_scripts.py missing)_'

    try:
        from email_templates import generate_email
        email_data = generate_email(row, your_name=your_name, your_phone=your_phone)
    except ImportError:
        email_data = None

    out = []
    out.append(f"# {company}")
    out.append(f"_{tier} lead · {industry} · {city}, {state} {pincode}_\n")

    out.append("## Company snapshot")
    out.append(f"- **Type:** {size_hint}")
    out.append(f"- **Industry:** {industry}")
    out.append(f"- **Location:** {city}, {state}" + (f" — PIN {pincode}" if pincode != '—' else ''))
    out.append(f"- **Website:** {website}")
    out.append("")

    out.append("## Best contact")
    out.append(f"- **Name:** {name_str}")
    out.append(f"- **Role:** {desg}")
    out.append(f"- **Email:** {email}")
    out.append(f"- **Phone:** {phone}")
    out.append("")

    out.append("## Recommended approach")
    out.append(f"**{channel}**\n")

    # Inline call script
    out.append("## Phone script (30 sec)")
    out.append(script_md.replace('### ' + company, '').strip())
    out.append("")

    # Inline email (if applicable)
    if email_data:
        out.append("## Email template")
        out.append(f"**To:** `{email_data['to']}`")
        out.append(f"**Subject:** {email_data['subject']}\n")
        out.append("**Body:**\n```\n" + email_data['body'] + "\n```\n")

    # Sources
    if sources:
        out.append("## Sources / verification")
        for s in sources:
            out.append(f"- {s}")
        out.append("")

    out.append("---\n")
    return '\n'.join(out)


def write_briefs_file(rows, path, top_n=20, your_name="[your name]",
                     your_phone="[your phone]"):
    """
    Write a single Markdown file with the top-N highest-priority lead briefs.

    Defaults to top 20. Sorted Hot → Warm → Cold, then by data completeness.
    """
    tier_order = {'Hot': 0, 'Warm': 1, 'Cold': 2, 'Skip': 9, '': 4}

    def sort_key(r):
        tier = str(r.get('Source Campaign','')).strip()
        # Bonus: more complete data = higher in tier
        complete = (bool(str(r.get('Primary Email','')).strip()) +
                    bool(str(r.get('Office Phone','')).strip()) +
                    bool(str(r.get('First Name','')).strip()))
        return (tier_order.get(tier, 4), -complete)

    sorted_rows = sorted(rows, key=sort_key)
    top = sorted_rows[:top_n]

    with open(path, 'w', encoding='utf-8') as f:
        f.write(f"# AIPL Top-{top_n} Lead Briefs\n")
        f.write(f"_Generated: {date.today().strftime('%d %b %Y')}_\n\n")
        f.write(f"**{len(top)} highest-priority leads** with full sales-execution kit per company: "
                f"company snapshot, best contact, recommended approach, phone script, "
                f"email template, verification sources.\n\n")
        f.write("**Before using:** replace `[your name]` and `[your phone]` with your contact info.\n\n")
        f.write("Open in any Markdown viewer (or paste into Notion/Google Docs/Word). "
                "Each brief is ~1 page when printed.\n\n")
        f.write("=" * 70 + "\n\n")
        for r in top:
            f.write(generate_brief(r, your_name=your_name, your_phone=your_phone))
    return path


if __name__ == '__main__':
    sample = {
        'Company':'Motilal Oswal Financial Services Ltd',
        'Industry':'Financial Services', 'City':'Mumbai', 'State':'Maharashtra',
        'Postal Code':'400025',
        'First Name':'Pankaj', 'Last Name':'Purohit',
        'Designation':'IT Manager / IT Head',
        'Primary Email':'pankaj.purohit@motilaloswal.com',
        'Office Phone':'+91-22-7193-4263', 'Mobile Phone':'',
        'Website':'https://www.motilaloswal.com',
        'Source Campaign':'Hot',
        'Additional Details':'Source: https://linkedin.com/in/pankaj-purohit | Confidence: High',
    }
    print(generate_brief(sample, your_name='Saish', your_phone='+91-XXXXX-XXXXX'))
