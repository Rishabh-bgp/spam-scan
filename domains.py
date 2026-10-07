"""Official-domain allowlist and look-alike (impersonating) domain detection.

Real Indian banks, payment apps, telecoms, couriers and government services link
only to their OWN official domains. This module:

  * extracts the real host of every link in a message (handling www., ports,
    and the "http://onlinesbi.sbi@evil.xyz" trick where everything before "@" is
    decoration and the real site is evil.xyz),
  * checks the host against an allowlist. Only an exact match or a genuine
    sub-domain counts: netbanking.hdfcbank.com is official, but
    hdfcbank.com.evil.xyz (owned by evil.xyz) and hdfcbank-kyc.com are not,
  * flags hosts that use a brand name, or a typo / digit-swap of one
    (hdfcbnk, sbii, 1cici, paypa1), without being on the allowlist.

Everything here is a plain, readable rule. Nothing is learned from data.
"""
import re

# domain -> who owns it. Matching is "exact or real sub-domain".
# Only domains we are confident are genuine (checked Oct 2026).
OFFICIAL = {
    # restricted zones: only the named kind of organisation can register under these
    "gov.in": "Government of India (any *.gov.in)",
    "nic.in": "National Informatics Centre (any *.nic.in)",
    "bank.in": "RBI-regulated bank (any *.bank.in, RBI's bank-only domain)",
    "sbi": "State Bank of India (.sbi is SBI's own top-level domain)",
    # banks
    "sbi.co.in": "SBI", "onlinesbi.sbi": "SBI", "sbicard.com": "SBI Card", "sbilife.co.in": "SBI Life",
    "sbimf.com": "SBI Mutual Fund",
    "hdfcbank.com": "HDFC Bank", "hdfc.com": "HDFC", "hdfclife.com": "HDFC Life", "hdfcergo.com": "HDFC ERGO",
    "hdfcsec.com": "HDFC Securities", "hdfcfund.com": "HDFC Mutual Fund",
    "icicibank.com": "ICICI Bank", "icicidirect.com": "ICICI Direct", "icicilombard.com": "ICICI Lombard",
    "iciciprulife.com": "ICICI Prudential Life",
    "axisbank.com": "Axis Bank", "axisdirect.in": "Axis Direct", "axismf.com": "Axis Mutual Fund",
    "kotak.com": "Kotak Mahindra Bank", "kotaksecurities.com": "Kotak Securities",
    "pnbindia.in": "Punjab National Bank",
    "bankofbaroda.in": "Bank of Baroda", "bankofbaroda.com": "Bank of Baroda",
    "canarabank.com": "Canara Bank",
    "unionbankofindia.co.in": "Union Bank of India",
    "idfcfirstbank.com": "IDFC FIRST Bank",
    "yesbank.in": "Yes Bank",
    "indusind.com": "IndusInd Bank",
    "bankofindia.co.in": "Bank of India", "centralbankofindia.co.in": "Central Bank of India",
    "indianbank.in": "Indian Bank", "iob.in": "Indian Overseas Bank", "idbibank.in": "IDBI Bank",
    "federalbank.co.in": "Federal Bank", "rblbank.com": "RBL Bank", "aubank.in": "AU Small Finance Bank",
    "bandhanbank.com": "Bandhan Bank",
    # regulators / payment networks
    "rbi.org.in": "Reserve Bank of India", "npci.org.in": "NPCI (UPI / BHIM)", "bhimupi.org.in": "BHIM (NPCI)",
    # payment apps / fintech
    "paytm.com": "Paytm", "paytm.in": "Paytm", "paytmbank.com": "Paytm Payments Bank", "paytmmoney.com": "Paytm Money",
    "phonepe.com": "PhonePe", "pay.google.com": "Google Pay", "mobikwik.com": "MobiKwik", "razorpay.com": "Razorpay",
    "zerodha.com": "Zerodha", "groww.in": "Groww",
    "paypal.com": "PayPal",
    # shops / services
    "amazon.in": "Amazon India", "amazon.com": "Amazon", "amazon.co.uk": "Amazon UK", "amazon.de": "Amazon Germany",
    "amazon.ca": "Amazon Canada", "amazon.com.au": "Amazon Australia", "flipkart.com": "Flipkart", "myntra.com": "Myntra",
    "meesho.com": "Meesho", "swiggy.com": "Swiggy", "zomato.com": "Zomato", "irctc.co.in": "IRCTC",
    "licindia.in": "LIC", "netflix.com": "Netflix", "mygov.in": "MyGov (Government of India)",
    # telecoms
    "jio.com": "Jio", "jiomart.com": "JioMart", "jiocinema.com": "JioCinema", "jiosaavn.com": "JioSaavn",
    "airtel.in": "Airtel", "airtel.com": "Airtel", "myvi.in": "Vi (Vodafone Idea)", "bsnl.co.in": "BSNL",
    # couriers
    "indiapost.gov.in": "India Post", "delhivery.com": "Delhivery", "bluedart.com": "Blue Dart",
    "dtdc.in": "DTDC", "dtdc.com": "DTDC", "ekartlogistics.com": "Ekart (Flipkart)", "xpressbees.com": "XpressBees",
    "shadowfax.in": "Shadowfax", "ecomexpress.in": "Ecom Express", "fedex.com": "FedEx", "dhl.com": "DHL",
    "ups.com": "UPS",
    # government services (also covered by *.gov.in, listed so the UI can name the owner)
    "incometax.gov.in": "Income Tax Department", "uidai.gov.in": "UIDAI (Aadhaar)",
    "epfindia.gov.in": "EPFO", "parivahan.gov.in": "Parivahan / e-challan", "cybercrime.gov.in": "National Cyber Crime Portal",
    "sancharsaathi.gov.in": "Sanchar Saathi (DoT)",
}
OFFICIAL_DOMAINS = tuple(OFFICIAL)

# Brand-owned short links (affiliate / merchant payment links). They lead to the
# brand's own site, but anyone with a merchant/affiliate account can create one,
# so they are neither a good sign nor a look-alike.
NEUTRAL = {"amzn.to", "amzn.in", "a.co", "fkrt.it", "paytm.me", "p-y.tm"}
# Real companies whose names merely CONTAIN a brand word (not banks / not impersonation):
# amazonaws.com = Amazon Web Services cloud hosting (anyone can host files there, so it is
# not an "official" sign either); axis.com = Axis Communications (cameras), not Axis Bank.
NEUTRAL_SUFFIXES = {"amazonaws.com", "cloudfront.net", "axis.com"}

SHORTENERS = {"bit.ly", "tinyurl.com", "goo.gl", "t.co", "cutt.ly", "is.gd", "rb.gy", "ow.ly", "shorturl.at",
              "tiny.cc", "1kx.in", "u1.mnge.co", "t.ly", "s.id", "v.gd", "shorte.st", "rebrand.ly", "bl.ink",
              "tinu.be", "short.gy", "qr.ae"}

# Two-level public suffixes, used to show the REAL owner (registrable domain) of a host.
_TWO_LEVEL = {"co.in", "org.in", "net.in", "gov.in", "ac.in", "edu.in", "res.in", "nic.in", "bank.in", "fin.in",
              "firm.in", "gen.in", "ind.in", "co.uk", "org.uk", "com.au", "co.za", "com.br", "com.ng"}

TLDS = (r"com|net|org|info|biz|ly|in|co|io|xyz|top|club|online|site|me|us|uk|ru|cn|link|live|shop|sbi|app|cc|tk|"
        r"icu|vip|buzz|store|click|support|help|gle|ml|ga|cf|gq|pw|cyou|lat|sbs|bond|work|win|loan|today|website|"
        r"space|fun|tech|ws|su|cfd|rest|gd|at|to|it")
_TLDS_BARE = TLDS.replace("|gd|at|to|it", "")   # bare "x.to" / "x.it" only count with http:// or www.
# A link: anything after http(s):// or www., or a bare domain ending in a known TLD.
LINK = re.compile(
    rf"(?:https?://|www\.)[^\s<>\"'()]+"
    rf"|(?<![\w@.-])(?:[a-z0-9@-]+\.)+(?:{_TLDS_BARE})\b(?:[/:?#][^\s<>\"'()]*)?"
    rf"|(?<![\w.-])(?:[a-z0-9-]+\.)+(?:{_TLDS_BARE})\b(?:[/:?#][^\s<>\"'()]*)?"
    rf"|(?:bit\.ly|amzn\.to|fkrt\.it|t\.ly|is\.gd|v\.gd|rb\.gy)/\S+",
    re.I)


def links(text):
    """Return a list of dicts {raw, host, userinfo} for every link in the text."""
    out = []
    for m in LINK.finditer(text or ""):
        raw = m.group(0).rstrip(".,;:!?)]}'\"")
        s = re.sub(r"^https?://", "", raw, flags=re.I)
        authority = re.split(r"[/?#\\]", s, maxsplit=1)[0]
        userinfo = ""
        if "@" in authority:
            userinfo, authority = authority.rsplit("@", 1)
        host = authority.split(":")[0].lower().strip(".")
        if host.startswith("www."):
            host = host[4:]
        if "." not in host:
            continue
        out.append({"raw": raw, "host": host, "userinfo": userinfo.lower()})
    return out


def official_owner(host):
    """Owner name if the host is an allowlisted domain or a real sub-domain of one, else None."""
    host = (host or "").lower().strip(".")
    if host.startswith("www."):
        host = host[4:]
    best = None
    for d, owner in OFFICIAL.items():
        if host == d or host.endswith("." + d):
            if best is None or len(d) > len(best[0]):
                best = (d, owner)
    return best[1] if best else None


def is_official(host):
    return official_owner(host) is not None


def is_shortener(host):
    return host in SHORTENERS


def registrable(host):
    """The part of a host that actually decides who owns it (e.g. evil.xyz)."""
    parts = host.split(".")
    if len(parts) >= 3 and ".".join(parts[-2:]) in _TWO_LEVEL:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


# ---------------------------------------------------------------------------
# Brands: (display name, regex applied to each host token, fuzzy keywords)
# A host token is a piece of the host between dots/hyphens, e.g.
# "sbi-kyc-update.com" -> sbi, kyc, update. Short brand names (sbi, pnb, rbi,
# jio) only count at the START or END of a token, so "lesbian" or "turbine"
# don't match. Fuzzy keywords (long, distinctive names) also match with one
# typo (missing/extra/swapped/wrong letter), e.g. hdcfbank, flipkrat.
# ---------------------------------------------------------------------------
BRANDS = [
    ("SBI", r"^s+bi|sbi$|onlinesbi|^yono", ["onlinesbi", "statebank"]),
    ("HDFC Bank", r"hdfc|hdffc", ["hdfcbank"]),
    ("ICICI Bank", r"[il]c[il]c[il]|icicbank", ["icicibank"]),
    ("Axis Bank", r"^axis", ["axisbank"]),
    ("Kotak", r"kotak", ["kotakbank"]),
    ("PNB", r"^pnb|pnb$|punjabnational", []),
    ("Bank of Baroda", r"bankofbaroda|^bobworld|^bobcard", ["bankofbaroda"]),
    ("Canara Bank", r"canarabank|^canara", ["canarabank"]),
    ("Union Bank", r"unionbank", ["unionbank"]),
    ("IDFC FIRST", r"idfc", ["idfcfirst"]),
    ("Yes Bank", r"yesbank", []),
    ("IndusInd", r"indusind", ["indusind"]),
    ("RBI", r"^rbi|rbi$|reservebank", []),
    ("Paytm", r"p[ae]yt[iey]?m|paytn|paytmm", []),
    ("PhonePe", r"phonepe|phonpe|fonepe|phonepay", []),
    ("Google Pay", r"googlepay|^gpay|gpay$", []),
    ("BHIM / NPCI", r"bhimupi|^bhim$|npci", []),
    ("Amazon", r"amazon|^amzn|amaz0n", []),
    ("Flipkart", r"flipkart|flipcart|flpkart", ["flipkart"]),
    ("Jio", r"^jio|jio$", []),
    ("Airtel", r"airtel|airtl$|airtell", []),
    ("Vi (Vodafone Idea)", r"vodafone|vodaidea|^myvi$", []),
    ("BSNL", r"bsnl", []),
    ("India Post", r"indiapost|^ippb", ["indiapost"]),
    ("Delhivery", r"delhivery|delhivry|dehlivery|delhiveri", []),
    ("Blue Dart", r"bluedart|blu?edart", ["bluedart"]),
    ("DTDC", r"dtdc", []),
    ("Income Tax Dept", r"incometax|incomtax|^itrefund", ["incometax"]),
    ("UIDAI / Aadhaar", r"uidai|uidia|aadha+r|aadhar|adhaar|aadahr", []),
    ("EPFO", r"^epfo|epfindia", []),
    ("Parivahan / e-challan", r"parivahan|echallan|e-?chalan", []),
    ("IRCTC", r"irctc", []),
    ("FedEx", r"fedex|fedx|fed-ex", []),
    ("DHL", r"^dhl|dhl$", []),
    ("PayPal", r"paypal|paypai|paypall", ["paypal"]),
    ("Netflix", r"netflix|netflx|netfliks", []),
]
_BRAND_RE = [(n, re.compile(p), fz) for n, p, fz in BRANDS]

# Brand mentioned in the message TEXT (word boundaries), for the brand/link mismatch rule.
TEXT_BRANDS = [
    ("SBI", r"\bsbi\b|\byono\b|state bank of india"), ("HDFC Bank", r"\bhdfc\b"), ("ICICI Bank", r"\bicici\b"),
    ("Axis Bank", r"\baxis bank\b"), ("Kotak", r"\bkotak\b"), ("PNB", r"\bpnb\b|punjab national bank"),
    ("Bank of Baroda", r"bank of baroda|\bbob (?:world|card|a/?c|account|customer)"), ("Canara Bank", r"\bcanara\b"), ("Union Bank", r"union bank"),
    ("IDFC FIRST", r"\bidfc\b"), ("Yes Bank", r"\byes bank\b"), ("IndusInd", r"\bindusind\b"),
    ("RBI", r"\brbi\b|reserve bank"), ("Paytm", r"\bpaytm\b"), ("PhonePe", r"\bphone ?pe\b"),
    ("Google Pay", r"\bgoogle pay\b|\bgpay\b"), ("BHIM / NPCI", r"\bbhim\b|\bnpci\b"), ("Amazon", r"\bamazon\b"),
    ("Flipkart", r"\bflipkart\b"), ("Jio", r"\bjio\b"), ("Airtel", r"\bairtel\b"),
    ("Vi (Vodafone Idea)", r"\bvodafone\b|\bvi (?:user|customer|sim|number|prepaid|postpaid)\b"), ("BSNL", r"\bbsnl\b"),
    ("India Post", r"\bindia ?post\b"), ("Delhivery", r"\bdelhivery\b"), ("Blue Dart", r"\bblue ?dart\b"),
    ("DTDC", r"\bdtdc\b"), ("Income Tax Dept", r"income ?tax|\bitr\b"), ("UIDAI / Aadhaar", r"\buidai\b|\baadhaa?r\b"),
    ("EPFO", r"\bepfo?\b"), ("IRCTC", r"\birctc\b"), ("Parivahan / e-challan", r"e-?challan|parivahan"),
    ("FedEx", r"\bfedex\b"), ("DHL", r"\bdhl\b"), ("PayPal", r"\bpaypal\b"), ("Netflix", r"\bnetflix\b"),
]
_TEXT_BRAND_RE = [(n, re.compile(p, re.I)) for n, p in TEXT_BRANDS]

_HOMO = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "8": "b", "@": "a", "$": "s"})
_HOMO_L = str.maketrans({"1": "l", "0": "o"})


def _variants(token):
    v = {token, token.translate(_HOMO), token.translate(_HOMO_L).translate(_HOMO)}
    v |= {x.replace("rn", "m").replace("vv", "w") for x in list(v)}
    return v


def _osa(a, b):
    """Optimal-string-alignment edit distance (insert/delete/substitute/swap neighbours)."""
    d = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) + 1):
        d[i][0] = i
    for j in range(len(b) + 1):
        d[0][j] = j
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            c = a[i - 1] != b[j - 1]
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + c)
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)
    return d[-1][-1]


def _fuzzy_hit(token, kw):
    if len(token) < len(kw) - 1:
        return False
    for L in (len(kw) - 1, len(kw), len(kw) + 1):
        for i in range(0, len(token) - L + 1):
            if _osa(token[i:i + L], kw) <= 1:
                return True
    return False


def _tokens(host):
    labels = host.split(".")
    # drop the public suffix (com, in, co.in, bank.in ...): it can't carry a brand
    n_suffix = 2 if len(labels) >= 3 and ".".join(labels[-2:]) in _TWO_LEVEL else 1
    toks = []
    for lab in labels[:-n_suffix] or labels:
        toks.append(lab)
        toks.extend(t for t in lab.split("-") if t and t != lab)
    return toks


def brand_in_host(host):
    """Return the brand a host (or the user-info part of a link) imitates, or None."""
    for tok in _tokens(host):
        for var in _variants(tok):
            for name, rx, fuzzy in _BRAND_RE:
                if rx.search(var) or any(_fuzzy_hit(var, kw) for kw in fuzzy):
                    return name
    return None


def classify_host(host, userinfo=""):
    """'official' | 'lookalike' | 'shortener' | 'neutral' | 'other', plus details."""
    if userinfo and brand_in_host(userinfo.replace("@", ".") + ".x"):
        return "lookalike", {"brand": brand_in_host(userinfo + ".x"), "owner": registrable(host),
                             "why": f"everything before '@' is decoration; the real site is {host}"}
    owner = official_owner(host)
    if owner:
        return "official", {"owner": owner}
    if host in SHORTENERS:
        return "shortener", {}
    if host in NEUTRAL or any(host == d or host.endswith("." + d) for d in NEUTRAL_SUFFIXES):
        return "neutral", {}
    brand = brand_in_host(host)
    if brand:
        return "lookalike", {"brand": brand, "owner": registrable(host)}
    return "other", {"owner": registrable(host)}


def analyse_links(text):
    """Classify every link in the message."""
    res = []
    for l in links(text):
        kind, info = classify_host(l["host"], l["userinfo"])
        res.append({**l, "kind": kind, **info})
    return res


def brands_in_text(text):
    return [n for n, rx in _TEXT_BRAND_RE if rx.search(text or "")]


def mask_official(text):
    """Replace links to official domains with a neutral word (used so other rules
    don't treat an official link as a suspicious 'link')."""
    def rep(m):
        ls = links(m.group(0))
        if ls and all(classify_host(l["host"], l["userinfo"])[0] == "official" for l in ls):
            return "officialsite"
        return m.group(0)
    return LINK.sub(rep, text or "")


if __name__ == "__main__":
    import sys
    for h in sys.argv[1:]:
        print(h, "->", analyse_links(h))
