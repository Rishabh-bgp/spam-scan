"""Transparent, rule-based red flags for common scam patterns (India-focused).

These rules are hand-written and kept SEPARATE from the machine-learning score.
Each rule has a name, a plain-language explanation and returns the exact text
it matched, so the user can see why it fired. They are deliberately tolerant
of common misspellings and Hinglish/Hindi wording.

A rule fires only when ALL of its pattern groups match somewhere in the message
(e.g. "KYC/SIM" AND "block/expire" AND "link/call"), which keeps legitimate
look-alikes (bank OTPs, genuine KYC reminders, courier tracking) from firing.
"""
import re

import domains as _dom

URL = r"(?:https?://\S+|www\.\S+|\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com|net|org|info|biz|ly|in|co|io|xyz|top|club|online|site|me|us|uk|ru|cn|link|live|shop|sbi|app|icu|vip|buzz|store|click|support|help|cfd|sbs|cyou)\b(?:/\S*)?)"
PHONE = r"(?:\+?\d[\dXx\s-]{8,}\d)"  # X = masked placeholder digits
CALL_OR_LINK = rf"(?:{URL}|{PHONE}|\bclick|\bclik|\blink\b|\bcall\b|\bcal\b|\bpress \d|\bdial\b|लिंक|कॉल|क्लिक)"
MONEY = r"(?:rs\.?\s?\d|₹\s?\d|inr\s?\d|\$\s?\d|£\s?\d|\b\d[\d,]*\s?(?:rs|rupees|dollars?|dolars?|pounds?|k|lakh|lac|crore|hazar|thousand)\b|\b(?:lakh|lac|crore|hazar|million|milion|paise|paisa|money|funds|amount|cash)\b|रुपये|लाख|करोड़|पैसे)"

# name -> (title, explanation, severity, [pattern groups that must ALL match])
RULES = [
    ("upi_pin_receive", "UPI PIN to receive money",
     "You never need to enter a UPI PIN to RECEIVE money. A PIN is only for paying; this is the classic collect-request scam.",
     "high",
     [r"\bupi\s*pin\b|\bupi\s*-?\s*pin\b|\bpin\b.{0,40}\bupi\b|upi.{0,40}\bpin\b|यूपीआई पिन",
      r"receiv|recieve|\bget\b|\bgot\b|credit|cashback|reward|rewrd|refund|collect|colect|paise|milega|mila|advance|prize|paaye|free|जीतने|पाने"]),
    ("kyc_block", "KYC / account / SIM block threat",
     "Threatens to block or suspend your bank account, wallet or SIM and demands a KYC / PAN / Aadhaar update. "
     "HIGH if it also gives a link or phone number (banks and telcos don't do KYC over SMS links or calls); "
     "MEDIUM if there is no link or number (a block threat + KYC demand is still a typical scam opener). "
     "It does not fire on notices that say your KYC is verified/complete, or that only ask you to visit your branch "
     "(a branch/visit mention switches off the no-link MEDIUM form).",
     "high/medium",
     None),  # custom logic below (_kyc_block)
    ("parcel_fee", "Parcel / courier fee or seizure",
     "Says a parcel is held, undeliverable or seized and asks for a small fee, customs duty or a call. Real couriers don't ask for fees via random links.",
     "high",
     [r"parcel|packa?ge|packge|shipment|courier|deliver|consignment|पार्सल",
      r"\bfee\b|charge|\bduty\b|\bpay\b|bharne|clearance|seized|held|illegal|ilegal|custom",
      CALL_OR_LINK]),
    ("arrest_payment", "Police / CBI / arrest threat with payment",
     "Impersonates police, CBI, customs, TRAI or courts and threatens arrest or legal action unless you pay or cooperate. Government agencies never demand money over phone/SMS ('digital arrest' scam).",
     "high",
     [r"arrest|arest|\bcbi\b|police|cyber cell|customs|\bfir\b|warrant|narcotic|drugs|money laundering|\btrai\b|\bjail\b|court|गिरफ्तार|पुलिस",
      r"transfer|\bpay\b|fine|deposit|bhej|\bsend\b|google pay|gpay|press \d|talk to (?:the|our) officer|video ca?l|disconnect|"+MONEY]),
    ("fake_customer_care", "Unofficial customer-care number asking for OTP/app",
     "Gives a 'customer care / helpline' phone number and asks you to share an OTP, card details or install a remote-access app. Official support never asks for these.",
     "high",
     [r"customer care|customer support|helpline|help line|support team|executive|care number",
      PHONE,
      r"\botp\b|anydesk|teamviewer|quick ?support|install|downlo?a?d|card det|refund|refnd|suspend"]),
    ("urgent_wire_transfer", "Urgent wire transfer / gift cards / changed bank details",
     "Asks for an urgent or confidential payment, gift-card codes or payment to 'new' bank details, often pretending to be a boss or vendor (CEO fraud / BEC). Always verify by calling the person on a known number.",
     "high",
     [r"wire transfer|bank transfer|\bremit|gift ?cards?|new vendor|new (?:bank )?acc?ount|bank details|account has changed|change of bank",
      r"urgent|asap|immediately|today|confidential|keep this|can'?t talk|board meeting|\bceo\b|\bmd\b|director|frozen|reimburse"]),
    ("job_fee", "Job offer that asks you to pay",
     "A job / work-from-home / 'selected candidate' message that asks for a registration fee, deposit or training charge. Genuine employers do not charge candidates.",
     "high",
     [r"\bjob\b|hiring|selected|shortlisted|work from home|part[ -]time|salary|salry|offer let|interview|intervew|ghar baithe|kamaye|earn\b|candidate|नौकरी",
      r"registration|\bfee\b|deposit|training kit|refundable|securi?ty|bhejein|\bpay\b|charges?"]),
    ("emergency_money", "Emergency money request",
     "An urgent request for money citing an accident, hospital, police or a 'new number'. Call the person on their known number before sending anything.",
     "high",
     [r"accident|hospital|emergency|trouble|trubble|police station|lost my phone|new number|\bjail\b|\bturant\b|urgent|urjent|दुर्घटना|अस्पताल",
      r"\bsend\b|bhejo|bhej\b|bhejein|transfer|google pay|\bgpay|paytm|upi id|"+MONEY]),
    ("utility_disconnect", "Electricity / gas disconnection threat",
     "Threatens to cut your electricity, gas or water tonight and asks you to call a personal number or click a link. Utilities send formal notices, not last-minute SMS from mobile numbers.",
     "high",
     [r"elec\w*city|elecricity|bijli|power|powr|\bgas\b|water connection|बिजली",
      r"disconn?ect|kaat|cut\b|band\b|बंद|काट",
      CALL_OR_LINK]),
    ("extortion_threat", "Kidnap / blackmail threat with a money demand",
     "Threatens harm to a family member (\"your son is with us\") or to leak a private video/photos, and demands money. "
     "This is extortion: don't pay, call the person directly on their known number, and report it on 1930 / cybercrime.gov.in.",
     "high",
     [r"kidnap\w*|\b(?:son|daughter|dauter|beti|beta|bachcha|child|wife|husband)\b[^.!?\n]{0,30}(?:is with us|hamare paas|in our custody|kabze)"
      r"|never see (?:him|her)|wil?l be hurt|pays the price|(?:recorded|watching|hacked)[^.!?\n]{0,40}webcam|webcam[^.!?\n]{0,40}record|morphed (?:photo|pic)\w*"
      r"|video[^.!?\n]{0,25}record|record\w*[^.!?\n]{0,40}video"
      r"|(?:video|photos?|pics?)[^.!?\n]{0,40}(?:contacts|family|friends)",
      r"bitcoin|\bbtc\b|"+MONEY,
      r"\bor\b|warna|otherwise|never see|hurt|police|polic\b|secret|don'?t (?:inform|tell|call)|"
      r"within \d+ ?(?:hours|hrs|minutes)|\d+ ?(?:ghante|ghanta)|watching|leak|viral|price"]),
    ("prize_claim", "Prize / lottery / 'you won' claim",
     "Claims you won a lottery, lucky draw, prize or large sum of money. You cannot win a contest you didn't enter.",
     "high",
     None),  # custom logic below
    ("otp_request", "Asks you to share an OTP/PIN",
     "Asks you to tell or share a one-time password or PIN. Nobody legitimate needs your OTP.",
     "high",
     [r"(?<!not )(?<!never )(?<!n't )(?<!mat )\b(?:share|tell|give|batao|bataye|bataen|send)\b[^.!?\n]{0,25}\b(?:otp|pin|cvv)\b|\b(?:otp|cvv)\b[^.!?\n]{0,20}\b(?:batao|bataye|बताएं|share karo|bhejo)|ओटीपी बताएं|OTP बताएं"]),
    ("lookalike_domain", "Look-alike / fake brand web address",
     "The link uses the name of a bank, payment app, telecom, courier or government service (or a misspelling / "
     "digit-swap of it, like hdfcbnk, sbii, 1cici, paypa1) but is NOT that organisation's official domain. Only the end "
     "of the address decides who owns it: hdfcbank.com.verify.xyz belongs to verify.xyz, and in "
     "http://onlinesbi.sbi@evil.xyz everything before '@' is decoration. Real banks and services only link to their own "
     "official domains (e.g. hdfcbank.com, onlinesbi.sbi, any *.bank.in or *.gov.in).",
     "high",
     None),  # custom logic below (_lookalike)
    ("brand_link_mismatch", "Names a brand, but the link goes somewhere else",
     "The message names a bank, payment app, telecom, courier or government service and asks you to act (verify, update, "
     "claim, pay, track, log in...), but its link goes to an unrelated "
     "website or a URL shortener (bit.ly, tinyurl...) instead of that organisation's official domain. Genuine "
     "organisations link to their own domain.",
     "medium",
     None),  # custom logic below (_brand_mismatch)
    ("suspicious_link", "Shortened or look-alike link",
     "Contains a URL shortener (hides the real destination), a domain mixing words like kyc/verify/secure/update/login, "
     "or a cheap throw-away domain ending (.xyz, .top, .shop...). Links to official domains are ignored here.",
     "medium",
     [r"\b(?:bit\.ly|tinyurl\.com|goo\.gl|t\.co|cutt\.ly|is\.gd|rb\.gy|ow\.ly|shorturl\.at|tiny\.cc|1kx\.in)/\S*"
      r"|\b[a-z0-9]+-[a-z0-9-]*(?:kyc|verify|verfy|secure|update|updat|login|reward|refund|billing|track|support|redeliver|fee)[a-z0-9-]*\.[a-z]{2,6}\b"
      r"|\b[a-z0-9-]*(?:kyc|verify|verfy|secure|update|login|reward|refund|billing|redeliver)[a-z0-9-]*-[a-z0-9-]+\.[a-z]{2,6}\b"
      r"|\b[a-z0-9-]+\.(?:xyz|top|club|online|site|live|shop)\b"]),
]

_PRIZE_STRONG = r"lottery|lotery|lottry|lucky draw|jackpot|लॉटरी|लकी ड्रा"
_PRIZE_WIN = (r"\b(?:won|w[o0]n|wo|win|winner|winer|wnr|jeet\w*|jeeta|jeete|jeeti|jita|जीत\w*|selected|slected|badhai)\b")
_PRIZE_WHAT = (r"million|milion|billion|lakh|crore|cash|prize|prise|inaam|inam|reward|voucher|iphone|iphon|"
               r"claim|clame|claime|colect|dollars?|dolars?|pounds?|\$\s?\d|£\s?\d|₹\s?\d|rs\.?\s?\d|लाख|करोड़|इनाम|पुरस्कार")


def _search(pattern, text):
    m = re.search(pattern, text, re.I | re.S)
    return m.group(0).strip() if m else None


# --- kyc_block ---------------------------------------------------------------
# (a) original HIGH form: KYC/PAN/Aadhaar/SIM AND block/expire/pending AND a link/call/number
_KYC_ENTITY = r"\bkyc\b|\bpan\b|aadhaa?r|\bsim\b|yono|केवाईसी|खाता|सिम"
_KYC_BLOCKISH = r"block|blok|suspend|suspnd|deactivat|expir|expird|band\b|बंद|disconnect|frozen|freeze|lock|pending|incomplet"
# (b) widened form, no link needed: a block/suspension THREAT AND a KYC/PAN/Aadhaar update DEMAND
_BLK = r"(?:block|blok|blck|suspend|suspnd|deactivat|disabl|frozen|freez|clos|band|bandh|बंद|ब्लॉक)\w*"
_KYC_THREAT = (
    rf"\b(?:will|wil|wl|shall|would|may|to|going to)\s+(?:be|b|get|gets)\s+(?:temporarily\s+|permanently\s+|soon\s+)?{_BLK}"
    rf"|\b(?:block|blok|band|bandh|suspend|deactivate|freeze|close)\w*\s+(?:ho|kar|kr)\s*(?:jayega|jaega|jayegi|jaegi|jaayega|diya jayega|diya jaega|di jayegi|denge|dia jayega)"
    rf"|\b(?:account|acount|acc|a/c|sim|wallet|khata|card|number|yono)\s+(?:is|has been|has|hs|was|got|is being|ho gaya|ho gya)?\s*(?:now\s+)?(?:blocked|blokd|blockd|blocked|suspended|suspnded|suspendd|deactivated|frozen|on hold|band)\b"
    rf"|\b(?:blocked|blokd|blockd|suspended|suspnded|deactivated)\s+(?:today|tonight|within|in\s+\d|from|after|by)\b"
    rf"|\bkyc\s+(?:is\s+|has\s+|hs\s+)?(?:been\s+)?(?:expired|expird|expird|expire ho)"
    rf"|बंद (?:कर दिया जाएगा|हो जाएगा)|ब्लॉक (?:कर दिया जाएगा|हो जाएगा)"
)
_KYC_DEMAND = (
    r"(?:\bre-?kyc\b)"
    r"|\b(?:update|updte|updat|upd8|complete|complet|verify|verfy|link|submit|renew)\w*\s+(?:\w+\s+){0,2}?(?:kyc|pan|aadhaa?r|e-?kyc)\b"
    r"|\b(?:kyc|pan|aadhaa?r|e-?kyc)\b(?:\s*/\s*\w+)?[\s,.:;-]+(?:\w+[\s,.:;-]+){0,2}?(?:update|updte|updat|upd8|complete|verify|verfy|link|submit|karein|karo|kare|kariye|kijiye|kar do|kara lo|करें|अपडेट)"
    r"|(?:केवाईसी|kyc)\s*(?:तुरंत\s*)?अपडेट"
)
_KYC_LINK_OR_NUMBER = rf"(?:{URL}|{PHONE})"
_KYC_BRANCH = r"\bbranch\b|\bvisit\b|शाखा"


def _official_link_only(text):
    """True if the message has links, ALL of them to official domains, and no phone number."""
    ls = _dom.analyse_links(text)
    return bool(ls) and all(l["kind"] == "official" for l in ls) and not _search(PHONE, text)


def _kyc_block(text):
    """Returns (matched snippets, severity) or (None, None).
    If the only 'link' is to the bank's official domain (and there is no phone number),
    the rule drops from HIGH to MEDIUM: still a warning, but real banks do send KYC
    reminders that point to their own website."""
    official_only = _official_link_only(text)
    a = [_search(g, text) for g in (_KYC_ENTITY, _KYC_BLOCKISH, CALL_OR_LINK)]
    if all(a):
        if official_only:
            return a + ["link is to an official domain, so medium not high"], "medium"
        return a, "high"
    threat, demand = _search(_KYC_THREAT, text), _search(_KYC_DEMAND, text)
    if threat and demand:
        link = _search(_KYC_LINK_OR_NUMBER, text)
        if link and official_only:
            return [threat, demand, "link is to an official domain, so medium not high"], "medium"
        if link:
            return [threat, demand, link], "high"
        if _search(_KYC_BRANCH, text):   # genuine banks send you to a branch, not to reply/act by SMS
            return None, None
        return [threat, demand], "medium"
    return None, None


def _lookalike(text):
    """Matched snippets for links that imitate a brand, or None."""
    out = []
    for l in _dom.analyse_links(text):
        if l["kind"] == "lookalike":
            out.append(l["host"] if not l["userinfo"] else l["raw"])
            out.append(f"imitates {l['brand']}")
            if l["owner"] != l["host"]:
                out.append(f"real owner: {l['owner']}")
    return out or None


_ACTION = (r"verif|verfy|update|updat|claim|clai?me|click|clik|log ?in|sign ?in|\bpay\b|confirm|redeem|activat|"
           r"reschedul|track|unlock|unblock|\bkyc\b|refund|reward|cashback|download|install|submit|visit|"
           r"karein|karo|kijiye|bharein|dekhein")


def _brand_mismatch(text):
    """Brand named in the text, but a link goes to an unrelated site or a shortener."""
    ls = _dom.analyse_links(text)
    if any(l["kind"] == "lookalike" for l in ls):
        return None   # the HIGH look-alike rule already covers it
    bad, brands = [], []
    for l in ls:
        if l["kind"] not in ("shortener", "other"):
            continue
        # brand + call to action must be NEAR the link (same SMS / paragraph), so long
        # newsletters that mention Amazon somewhere and link elsewhere don't trigger it
        i = text.find(l["raw"])
        window = text[max(0, i - 200): i + len(l["raw"]) + 60] if i >= 0 else text
        b = _dom.brands_in_text(window)
        if b and _search(_ACTION, window):
            bad.append(l)
            brands += [x for x in b if x not in brands]
    if not bad:
        return None
    out = [f"mentions {b}" for b in brands[:2]]
    for l in bad[:2]:
        out.append(f"link goes to {l['host']}" + (" (URL shortener)" if l["kind"] == "shortener" else ""))
    return out


def check(text: str):
    """Return a list of triggered red flags: dicts with id, title, explanation,
    severity and matched (list of matched snippets)."""
    flags = []
    for rid, title, expl, sev, groups in RULES:
        severity = sev
        if rid == "kyc_block":
            matched, severity = _kyc_block(text)
        elif rid == "lookalike_domain":
            matched = _lookalike(text)
        elif rid == "brand_link_mismatch":
            matched = _brand_mismatch(text)
        elif rid == "suspicious_link":
            m = _search(groups[0], _dom.mask_official(text))
            matched = [m] if m else None
        elif rid == "prize_claim":
            strong = _search(_PRIZE_STRONG, text)
            win, what = _search(_PRIZE_WIN, text), _search(_PRIZE_WHAT, text)
            matched = [strong] if strong else ([win, what] if win and what else None)
        else:
            matched = []
            for g in groups:
                m = _search(g, text)
                if not m:
                    matched = None
                    break
                matched.append(m)
        if matched:
            uniq = []
            for m in matched:
                m = m[:60]
                if m.lower() not in [u.lower() for u in uniq]:
                    uniq.append(m)
            flags.append({"id": rid, "title": title, "explanation": expl,
                          "severity": severity, "matched": uniq})
    return flags


if __name__ == "__main__":
    import sys
    for f in check(" ".join(sys.argv[1:])):
        print(f"[{f['severity']}] {f['title']}: {f['matched']}")


# ---------------------------------------------------------------------------
# SAFE SIGNALS: "looks like a standard transactional alert"
# ---------------------------------------------------------------------------
# These recognise the FORMAT of common genuine alerts (bank debit/credit, UPI
# confirmations, OTPs, courier status, official e-challan, KYC-complete notices,
# expense approvals). Scammers can imitate these formats, so a safe signal is
# only applied when NONE of the blockers below fire (no red flags, no link to a
# non-official domain, no request for PIN/OTP/card details, no payment/fee
# request, no shortened link, no "call to avoid blocking").

OFFICIAL_DOMAINS = _dom.OFFICIAL_DOMAINS   # full allowlist with owners: domains.py

SAFE_RULES = [
    ("official_link", "Link goes only to an official domain",
     "Every link in the message points to an official domain of an Indian bank, payment app, telecom, courier, shop or "
     "government service (exact domain or a real sub-domain, e.g. netbanking.hdfcbank.com, onlinesbi.sbi, any *.bank.in "
     "or *.gov.in; never hdfcbank.com.evil.xyz). On its own it counts like the alert formats below (Not spam, or only Unsure if the ML "
     "model is at least 95% sure) and it never overrides a red flag. Together with a standard alert format below it makes the message Not spam even when "
     "the ML model is very confident. Not applied if the message also gives a mobile number.",
     None, "official_link"),
    ("bank_txn_alert", "Standard bank debit/credit alert",
     "Reads like an automated bank alert: a masked account/card number (e.g. XX1234) with a debit/credit amount or balance.",
     [r"\b(?:a/?c|acct?|account|card)\b[^.\n]{0,25}(?:xx+|\*{2,}|x{2,})\d{2,}|(?:xx+|\*{2,})\d{3,}",
      r"debited|credited|spent|withdrawn|avl\.? ?bal|available balance|txn of"],
     None),
    ("upi_confirmation", "UPI payment confirmation with reference number",
     "Reads like a UPI sent/received confirmation that quotes a transaction reference number.",
     [r"\bupi\b",
      r"(?:ref(?:erence)?|utr|txn|transaction)\.?\s*(?:no\.?|number|id)?[:\s#.-]*\d{6,}",
      r"\b(?:sent|received|debited|credited|paid|successful(?:ly)?)\b"],
     None),
    ("otp_notice", "One-time password notice that warns not to share it",
     "Reads like a genuine OTP message: it contains a code and warns you NOT to share it, and has no link "
     "(except to the bank's own official domain, as in '@onlinesbi.sbi #123456').",
     [r"\b(?:otp|one[- ]time password|verification code|login code)\b",
      r"\b\d{4,8}\b",
      r"do not share|don'?t share|never share|not to share|never ask|mat bataye|share na kare|kisi ke saath share na"],
     "no_link"),
    ("delivery_update", "Courier / order status update",
     "Reads like a shipping status update (shipped / out for delivery / delivered) from a courier or shop, without asking for any fee.",
     [r"delhivery|blue ?dart|dtdc|ekart|xpressbees|shadowfax|ecom express|india post|amazon|flipkart|myntra|meesho|"
      r"\border\b|shipment|\bawb\b|tracking|consignment",
      r"has been shipped|\bshipped\b|out for delivery|\bdelivered\b|dispatched|in transit|will arrive|arriving|will be delivered"],
     None),
    ("echallan_official", "Traffic e-challan pointing to the official portal",
     "An e-challan notice whose only links go to the official government portal (parivahan.gov.in).",
     [r"e-?challan", r"parivahan\.gov\.in"],
     None),
    ("kyc_complete", "KYC completed / verified notice",
     "Says your KYC is already verified or complete, and does not ask you to do anything.",
     [r"\bkyc\b", r"(?:successfully|been|is)\s+(?:verified|completed|approved)|kyc (?:is )?(?:complete|verified)"],
     r"pending|expir|block|suspend|incomplete|update (?:now|your|immediately)|re-?kyc|click"),
    ("expense_approval", "Routine expense / payroll / PO approval",
     "Reads like a routine internal finance notice: an expense claim, reimbursement, payslip or PO that has been approved or processed.",
     [r"expense|reimburse|payslip|salary slip|purchase order|\bpo\b|claim\s*#",
      r"approved|processed|will be paid|has been paid|credited"],
     r"gift ?card|new (?:bank )?acc?ount|change of bank|wire transfer|confidential"),
]

_SHORTENER = r"\b(?:bit\.ly|tinyurl\.com|goo\.gl|t\.co|cutt\.ly|is\.gd|rb\.gy|ow\.ly|shorturl\.at|tiny\.cc|1kx\.in|u1\.mnge\.co)/?\S*"
_URL_HOST = re.compile(r"(?:https?://)?(?:www\.)?((?:[a-z0-9-]+\.)+[a-z]{2,})(?:[/:?#]\S*)?", re.I)
_NEG_BEFORE = re.compile(r"(?:not|never|n't|mat|na|nahi)\W+(?:\w+\W+){0,2}$", re.I)


def _hosts(text):
    return [l["host"] for l in _dom.links(text)]


def _official(host):
    return _dom.is_official(host)


_MOBILE = r"(?<!\d)(?:\+?91[\s-]?)?[6-9][\dXx]{4}[\s-]?[\dXx]{5}(?!\d)"


def _asks_for_credentials(text):
    pat = re.compile(r"\b(?:enter|share|send|provide|give|tell|batao|bataye|type|confirm|update|submit|reply with)\b"
                     r"[^.!?\n]{0,30}\b(?:upi ?pin|pin|otp|password|passcode|cvv|card (?:number|details|no)|"
                     r"net ?banking|login details|mpin)\b", re.I)
    for m in pat.finditer(text):
        if not _NEG_BEFORE.search(text[max(0, m.start() - 25):m.start()]):
            return m.group(0)
    return None


def safe_signals(text, flags=None):
    """Return {"applies": bool, "signals": [...], "blocked_by": [...]}.

    signals: safe rules whose pattern matched (with matched text).
    blocked_by: plain-language reasons why the safe signal is NOT applied.
    """
    flags = check(text) if flags is None else flags
    signals = []
    links = _dom.analyse_links(text)
    for rid, title, expl, groups, extra in SAFE_RULES:
        if extra == "official_link":
            off = [l for l in links if l["kind"] == "official"]
            if not off or len(off) != len(links):
                continue
            sig = {"id": rid, "title": title, "explanation": expl,
                   "matched": [f"{l['host']} ({l['owner'].split(' (')[0]})" [:60] for l in off[:3]]}
            mob = _search(_MOBILE, text)
            if mob:
                sig["rule_specific_block"] = f"also gives a mobile number ('{mob}'); real alerts use toll-free/official numbers"
            signals.append(sig)
            continue
        matched = []
        for g in groups:
            m = _search(g, text)
            if not m:
                matched = None
                break
            matched.append(m[:60])
        if not matched:
            continue
        sig = {"id": rid, "title": title, "explanation": expl, "matched": matched}
        if extra == "no_link" and any(l["kind"] != "official" for l in links):
            sig["rule_specific_block"] = "OTP messages should not contain links (other than the bank's official domain), and this one does"
        elif extra and extra != "no_link":
            neg = _search(extra, text)
            if neg:
                sig["rule_specific_block"] = f"also contains '{neg}', which genuine notices of this type don't"
        signals.append(sig)

    blocked = []
    if not signals:
        return {"applies": False, "signals": [], "blocked_by": []}
    for f in flags:
        blocked.append(f"red flag fired: {f['title']}")
    bad_hosts = [h for h in _hosts(text) if not _official(h)]
    if bad_hosts:
        blocked.append(f"contains a link to a non-official domain ({', '.join(sorted(set(bad_hosts))[:3])})")
    if re.search(_SHORTENER, text, re.I):
        blocked.append("uses a shortened link that hides the real destination")
    cred = _asks_for_credentials(text)
    if cred:
        blocked.append(f"asks for a PIN/OTP/password/card details ('{cred[:50]}')")
    pay = _search(r"\bpay(?:\s+(?:(?:now|rs|inr|the|a|your)\b|₹|\d))|\bfee\b|\bcharges? of\b|\bdeposit\b|"
                  r"(?:transfer|send|bhejo|bhejein)\s+(?:rs\.?|inr|₹|\d)|\bpayment (?:of|due)\b|"
                  r"\b(?:send|transfer|pay|bhejo|bhejein)\b[^.\n]{0,40}(?:upi ?id|\bvpa\b|\b[\w.-]+@(?:ybl|ok\w+|paytm|upi|ibl|axl|apl)\b)",
                  text)
    if pay and not any(s["id"] in ("echallan_official",) for s in signals):
        blocked.append(f"asks for a payment or fee ('{pay}')")
    urge = _search(r"(?:call|contact|dial|whatsapp)\b[^.\n]{0,50}(?:block|suspend|deactivat|disconnect|band\b|avoid)|"
                   r"(?:block|suspend|deactivat|disconnect|band ho)[^.\n]{0,60}(?:call|contact|dial)\b", text)
    if urge:
        blocked.append(f"urges you to call a number to avoid blocking ('{urge[:50]}')")
    clean_signals = [s for s in signals if "rule_specific_block" not in s]
    for s in signals:
        if "rule_specific_block" in s:
            blocked.append(f"{s['title']}: {s['rule_specific_block']}")
    applies = bool(clean_signals) and not [b for b in blocked if not b.startswith(tuple(s["title"] for s in signals))]
    return {"applies": applies, "signals": signals, "blocked_by": blocked}
