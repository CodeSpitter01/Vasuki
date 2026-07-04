# 🐍 Vasuki – Terminal OSINT Tool

[![Python](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

**Vasuki** is a powerful, free, and open‑source terminal OSINT tool that automates the discovery of publicly available information about a target using platform scanning, exact username matching, and deep recursive dorking. It reduces manual reconnaissance efforts and delivers actionable results in under **2 minutes** – all from your terminal.

> 🛡️ **Ethical Use Only** – This tool is designed for security research, penetration testing, and educational purposes. **Do not** use it without explicit written permission from the target. Unauthorised use may violate privacy laws and lead to legal consequences.

---

## 📦 Features

- 🔎 **Scans 50+ platforms** – Social, professional, tech, gaming, creative, forums, support, blogging, and more.
- ✅ **Exact username matches** – Quickly verify if a username exists on popular sites.
- 🕸️ **Deep dorking** – Uses DuckDuckGo to search for PDFs, court cases, college records, custom sites, and more.
- 🎯 **Categorised output** – Results are grouped by subcategories (social, college, professional, court, etc.) for clarity.
- ⚡ **Fast & efficient** – Multi‑threaded scanning returns results in seconds.
- 💾 **JSON export** – Save all findings to a structured JSON file for later analysis.
- 🔁 **Recursive enrichment** – If an email, location, or company is found, Vasuki will search further.
- 🧹 **Clean, terminal‑friendly output** – Uses rich formatting (fallback to plain text if unavailable).
- 🎓 **Targeted subcategories** – Choose from: `soc` (social), `case` (court/legal), `pro` (professional), `file` (docs/PDFs), `col` (college/university), `cus` (custom), `all`.

---

## 🚀 Installation

### Prerequisites
- Python 3.6 or higher
- `pip` and `virtualenv` (recommended)

### Steps
```bash
# Clone the repository
git clone https://github.com/CodeSpitter01/Vasuki.git
cd Vasuki

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# Install in editable mode (creates the `vasuki` command)
pip install -e .

📝 Usage
vasuki -cat {st,em,any} -subcat {soc,case,pro,file,col,cus,all} -n "Full Name" -u "username" -k "keyword" --deep

Required arguments
-n, --name – Target full name (compulsory).

Optional arguments
Argument	Description
-u, --username	Target username (if known).
-e, --email	Known email address.
-k, --keywords	Extra keywords (can be used multiple times).
-cat, --category	Category of target: st (student), em (employee), any (anyone).
-subcat, --subcategories	Space‑separated subcategories: soc, case, pro, file, col, cus, all.
--deep	Enable deep recursive dorking (DuckDuckGo).
--max-depth	Recursion depth for enrichment (default: 2).
--workers	Number of threads (default: 25).
-o, --output	Custom JSON report filename.

Examples
vasuki -cat st -subcat soc col pro -n "Vivek Sharma" -u "vivek_21" --deep
vasuki -cat em -subcat all -n "Priya Patel" -k "python" -k "hackerrank" --deep
vasuki -cat any -subcat soc case -n "Amit Kumar" --deep

⚠️ Input sensitivity – Vasuki relies on the exactness of the name/username you provide. If results are inaccurate, try tweaking the name (e.g., add initials, use a different spelling) or add relevant keywords. It doesn't guarantee 100% accuracy but aims to give you the best publicly available links quickly.

📂 Output
The tool displays only category headings in the terminal (to keep the output clean), but saves full details (titles, URLs, snippets) into a JSON file like:
osint_username_20260704_153022.json

The JSON is structured as:
{
  "target_name": "...",
  "target_username": "...",
  "category": "...",
  "subcategories": [...],
  "username_matches": [...],
  "deep_results": {
    "social_sites": [...],
    "college_details": [...],
    ...
  },
  "_meta": { ... }
}

⚖️ Legal & Ethical Disclaimer
Vasuki is intended solely for educational purposes, authorised security testing, and personal research.

🔒 You must obtain explicit, written permission from the individual or organisation you are investigating before using this tool.

🚫 Do not use Vasuki to:

Stalk, harass, or intimidate anyone.

Gain unauthorised access to systems or private information.

Violate any applicable laws, including but not limited to:

GDPR (General Data Protection Regulation – EU)

CCPA (California Consumer Privacy Act – USA)

IT Act 2000 (India)

Computer Fraud and Abuse Act (USA)

Any other local privacy and data protection regulations.

👁️ The tool only accesses publicly available information; it does not breach any security measures.

📛 The author (Preet Kapoor) is not responsible for any misuse, damage, or legal consequences arising from the use of this tool. By using Vasuki, you accept full responsibility for your actions.

✅ I adhere to all privacy principles and ethical guidelines. Please use this tool responsibly.

📄 License
This project is licensed under the MIT License – see the LICENSE file for details.

📚 Acknowledgements
DuckDuckGo Search for dorking capabilities.

Rich for beautiful terminal output.

All the open‑source platforms that make OSINT possible.
