"""Hand-written robustness probes (NOT used for training).

Each entry is (expected_label, message). These are deliberately varied:
short typo'd SMS, phishing and work emails, OTPs, Indian UPI/KYC scams,
newsletters, obfuscated spam and ordinary chat. Run `python probes.py` to
score the current model.
"""
SPAM, HAM = "spam", "ham"

GENERAL = [
    # --- user-reported / short prize claims (must pass) ---
    (SPAM, "You have wo 1 million dollars"),
    (SPAM, "u won 1 million"),
    (SPAM, "You have won $1,000,000"),
    (SPAM, "congrats you won a lottery"),
    (SPAM, "Congratulations! Your number was selected in our lucky draw. Claim your prize of Rs 25,00,000 now."),
    # --- obfuscated spam ---
    (SPAM, "G3t fr33 v1agra n0w!!! Ch3ap m3ds, no prescripti0n needed"),
    (SPAM, "F.R.E.E iPh0ne 15 w1nner!! click h e r e to cl@im"),
    # --- phishing emails ---
    (SPAM, "Subject: Account suspended\n\nDear Customer, we detected unusual activity on your PayPal account. Your account has been limited. Please verify your identity within 24 hours at http://paypal-secure-verify.com/login or it will be permanently closed."),
    (SPAM, "Subject: Your Netflix payment failed\n\nHi, we couldn't process your last payment. Update your billing details now to avoid service interruption: https://netflix-billing-update.xyz"),
    (SPAM, "Dear Sir/Madam, I am Barrister James Williams. A late client of mine left an inheritance of $10.5 million with no next of kin. I need your assistance to transfer the funds; you will receive 40%. Reply with your full name and bank details."),
    # --- Indian-context scams ---
    (SPAM, "Dear customer, your SBI account will be blocked today. Please update your KYC immediately by clicking http://bit.ly/sbi-kyc-update"),
    (SPAM, "Your electricity connection will be disconnected tonight at 9.30 pm due to unpaid bill. Call our officer immediately on 9876543210."),
    (SPAM, "Congratulations! You have received Rs 5000 cashback on Paytm. Enter your UPI PIN to receive the amount in your account."),
    (SPAM, "Earn Rs 3000 daily working from home! Just like YouTube videos. WhatsApp now to join, limited seats."),
    # --- crypto / investment / lottery ---
    (SPAM, "Double your Bitcoin in 24 hours! Send 0.1 BTC to our wallet and get 0.2 BTC back guaranteed. Limited time offer."),
    (SPAM, "Exclusive crypto signals group: 500% returns guaranteed this week. Join our Telegram now before it's closed!"),
    (SPAM, "URGENT: You are the lucky winner of our weekly draw. Reply WIN to 85023 to claim your £500 Amazon voucher."),
    # --- legitimate: OTP / bank alerts / transactional ---
    (HAM, "Your OTP for login is 482913. Do not share it with anyone. It is valid for 10 minutes."),
    (HAM, "Rs 1,250.00 debited from your HDFC Bank a/c XX4521 on 05-10-26 to VPA swiggy@icici. Not you? Call 18002586161."),
    (HAM, "Your Amazon order #405-1234567 has been shipped and will arrive on Friday."),
    (HAM, "Hi Rishabh, your appointment with Dr. Mehta is confirmed for Thursday at 4:30 PM."),
    # --- legitimate: newsletters / work emails ---
    (HAM, "Subject: This week in Python\n\nHere are this week's top articles: understanding asyncio, a guide to type hints, and what's new in Python 3.13. Happy reading!"),
    (HAM, "Subject: Q3 planning meeting\n\nHi team, let's meet on Monday at 11 am to go over the Q3 roadmap. Please review the attached document beforehand and add your comments."),
    (HAM, "Hi Priya, thanks for sending the report. I've made a few edits in section 2; can you take a look before we send it to the client tomorrow?"),
    (HAM, "Subject: Re: invoice\n\nHi, please find the invoice for September attached. Let me know if you need anything else. Regards, Ankit"),
    (HAM, "The build is failing on main after the last merge. Can someone look at the test logs?"),
    # --- legitimate: casual chat ---
    (HAM, "hey are we still on for dinner tonight?"),
    (HAM, "Happy birthday bro! Have an awesome day 🎉"),
    (HAM, "I won the match today, so happy!"),
    (HAM, "Mom said she will call you after 8, she is at the temple right now"),
    (HAM, "Can you send me the notes from yesterday's class?"),
    (HAM, "lol that movie was so bad, never watching it again"),
]

# Misspellings / typos / txt-speak (spam and normal).
MISSPELLED = [
    (SPAM, "You have wo 1 million dollars"),
    (SPAM, "u won 1 milion dolars"),
    (SPAM, "Congratulatons! You hav won a lotery of 5 milion"),
    (SPAM, "congrats u r the winer of our lucky draw, cal now to clame ur prize"),
    (SPAM, "Ur acount has been suspnded. Verfy ur detials imediately at http://secure-bank-verfy.com"),
    (SPAM, "FREEE ringtonez!!! txt TONE to 87066 now, onli 1.50 per wk"),
    (SPAM, "Get cheep loanz wit no credit chek, aproved in 5 minuts!"),
    (SPAM, "Dear costumer ur KYC is expird, updte now or ur acount wil be blokd"),
    (SPAM, "You are slected for a free iphon, clik the link to clam"),
    (SPAM, "Urgnt! Ur mobile no. has won 2000 pounds cash, call 09061743810 to colect"),
    (SPAM, "Eaarn $5000 a weeek frm home, no experiance neded!!"),
    (SPAM, "Hot singels in ur area want to met u tonite, reply YES"),
    (SPAM, "Claime ur reward now!! limted time ofer, dont mis out"),
    (SPAM, "Ur paypal acc is lockd. Plz login to unlok: paypa1-support.net"),
    (HAM, "hey wat r u doin tmrw? wanna grab lunch"),
    (HAM, "sry im runnin late, b there in 10 mins"),
    (HAM, "Thnx for the gift, realy luv it!"),
    (HAM, "can u pls send me the adress of the resturant"),
    (HAM, "Meetng is postponed to tomorow, plz inform evryone"),
    (HAM, "i forgt my charger at ur place, wil pick it up l8r"),
    (HAM, "Hapy birthday! hav a grt day ahead"),
    (HAM, "Did u finsh the asignment? i'm stuck on qustion 3"),
    (HAM, "ok gud nite, tc"),
    (HAM, "Plz call me wen u r free, its abt the projct"),
    (HAM, "Mom sed dinner is reddy, come home soon"),
    (HAM, "I won the chess tournment today, so hapy!"),
]

# Hinglish (Hindi-English in Roman script) and Hindi (Devanagari).
HINGLISH = [
    (SPAM, "Aapka KYC pending hai, turant link pe click karo warna account band ho jayega"),
    (SPAM, "Congratulations aapne 10 lakh jeete hai! Claim karne ke liye abhi call karein 9876501234"),
    (SPAM, "Badhai ho! Aapka mobile number lucky draw mein select hua hai, Rs 25 lakh ka inaam jeetne ke liye reply karein"),
    (SPAM, "Ghar baithe kamaye Rs 5000 roz, sirf WhatsApp karein. Limited offer!"),
    (SPAM, "Aapka bijli connection aaj raat 9 baje kaat diya jayega. Turant is number par call karein"),
    (SPAM, "Aapke account mein Rs 50,000 ka loan approve ho gaya hai, abhi link par click karke paise paaye"),
    (SPAM, "Free recharge paaye! Is link par click karein aur apna UPI PIN dalein"),
    (SPAM, "Aapka SIM card 24 ghante mein block ho jayega, KYC update karne ke liye call karein"),
    (SPAM, "Sirf aaj ke liye 90% discount! Jaldi kharido, offer khatam hone wala hai. bit.ly/sale99"),
    (SPAM, "Aapka PAN card block ho gaya hai. Turant update karein: http://pan-kyc-update.in"),
    (SPAM, "बधाई हो! आपने 10 लाख रुपये की लॉटरी जीती है। इनाम पाने के लिए अभी कॉल करें।"),
    (SPAM, "आपका बैंक खाता बंद कर दिया जाएगा। अपना KYC तुरंत अपडेट करें, लिंक पर क्लिक करें।"),
    (SPAM, "मुफ्त रिचार्ज पाने के लिए इस लिंक पर क्लिक करें और अपना OTP बताएं।"),
    (HAM, "Bhai kal milte hai office mein"),
    (HAM, "Mummy ghar kab aaogi?"),
    (HAM, "Kya scene hai aaj raat ka? Movie chalein?"),
    (HAM, "Yaar main thoda late ho jaunga, tum log shuru karo"),
    (HAM, "Papa ne bola hai ki dinner pe sab saath mein khayenge"),
    (HAM, "Kal ka meeting 11 baje hai, presentation ready rakhna"),
    (HAM, "Happy birthday bhai! Party kab de raha hai?"),
    (HAM, "Maine paise transfer kar diye, check kar lena"),
    (HAM, "Aaj bahut garmi hai, AC chala do please"),
    (HAM, "Notes bhej de yaar, kal exam hai"),
    (HAM, "मैं घर पहुंच गया हूं, चिंता मत करना।"),
    (HAM, "कल सुबह 10 बजे मिलते हैं, समय पर आ जाना।"),
    (HAM, "मम्मी, खाना बहुत अच्छा बना था।"),
]

# Indian scam categories: scams (English / Hinglish / misspelled) plus legitimate
# look-alikes to catch false positives. Keyed by category for per-category scores.
INDIA_SCAMS = {
    "upi_phishing": [
        (SPAM, "You have received a payment request of Rs 4,999 from PhonePe Rewards. Enter your UPI PIN to receive Rs 4,999 cashback in your account."),
        (SPAM, "Aapko Rs 2000 cashback mila hai! Paise receive karne ke liye UPI PIN daalein aur collect request approve karein."),
        (SPAM, "Congrats! U got Rs 999 GPay scratch card rewrd. Aprove the colect request and entr UPI pin to get money in ur acount"),
        (SPAM, "Hi, I am buying your sofa on OLX. I sent a QR code, scan it and enter your UPI PIN to receive the advance of Rs 15,000."),
        (HAM, "Rs 450.00 sent to Ramesh Kumar via UPI on 06-Oct. UPI Ref 427815536201. Not you? Call 1800-111-109 - SBI"),
        (HAM, "Bhai maine GPay pe 500 bhej diye, check kar le"),
    ],
    "kyc_alert": [
        (SPAM, "Dear SBI customer, your YONO account will be blocked today. Update your PAN/KYC immediately: http://sbi-yono-kyc.co/update"),
        (SPAM, "Priy grahak, aapka HDFC account ka KYC expire ho gaya hai. Turant is link par update karein warna account band: hdfc-kyc.in/verify"),
        (SPAM, "Dear Airtel user ur SIM wil be blockd in 24 hrs due to incomplet KYC. Cal executive 7029384756 to updat now"),
        (SPAM, "Your Jio SIM card KYC verification is pending. Your number will be deactivated today. Call 8372615490 immediately."),
        (HAM, "Dear Customer, as per RBI guidelines, please complete your periodic KYC update by visiting your nearest HDFC Bank branch. HDFC Bank never asks for OTP or PIN."),
        (HAM, "Your KYC has been successfully verified. Your Zerodha account is now active. Happy investing!"),
    ],
    "courier_fee": [
        (SPAM, "India Post: Your parcel is held at our warehouse due to incomplete address. Pay Rs 25 redelivery fee within 48 hours: indiapost-redeliver.top"),
        (SPAM, "Aapka parcel deliver nahi ho paya. Address update karne aur Rs 30 fee bharne ke liye link par click karein: bit.ly/dtdc-fee"),
        (SPAM, "FedEx: ur packge cant be deliverd, custom duty pendng. Pay 49 Rs now at fedx-track.xyz or it wil be returnd"),
        (SPAM, "DHL: A package addressed to you contains illegal items and has been seized. Press 1 to speak to our officer or pay the clearance charge."),
        (HAM, "Your Delhivery shipment AWB 1234567890 is out for delivery today. Track: https://www.delhivery.com/track"),
        (HAM, "Bhaiya parcel gate pe guard ko de dena, main ghar pe nahi hu"),
    ],
    "digital_arrest": [
        (SPAM, "This is CBI officer Rajesh Mishra. An FIR has been registered against your Aadhaar for money laundering. You are under digital arrest. Transfer Rs 2,50,000 to the verification account to avoid arrest."),
        (SPAM, "Mumbai Police Cyber Cell: aapke naam se drugs wala parcel pakda gaya hai. Arrest se bachne ke liye turant Rs 50,000 security deposit bhejein aur kisi ko mat batana."),
        (SPAM, "Customs dept notice: ilegal parcel in ur name, arest warrant issud. Pay fine Rs 85000 today on video cal to clear ur name"),
        (SPAM, "Your mobile number is linked to illegal activities. TRAI will disconnect it in 2 hours and a police case will be filed. Press 9 to talk to the officer."),
        (HAM, "Your traffic e-challan of Rs 500 for vehicle DL3CAB1234 can be paid at https://echallan.parivahan.gov.in"),
        (HAM, "Police verification for your passport is scheduled for Saturday 11 AM. Please keep your original documents ready."),
    ],
    "fake_customer_care": [
        (SPAM, "Facing issues with your refund? Call Amazon customer care 24x7 helpline 8293746510 and share the OTP to get your refund instantly."),
        (SPAM, "Paytm customer care: aapka wallet suspend ho gaya hai. Dobara chalu karne ke liye 9123456780 par call karein aur AnyDesk app install karein."),
        (SPAM, "Flipkart helpline no. 7865432190, cal now for refnd. Downlod the app we send and entr ur card detials"),
        (HAM, "Thank you for contacting Swiggy support. Your refund of Rs 180 has been initiated and will reflect in 5-7 working days."),
        (HAM, "Hi, I called the airline about the delayed flight, they said they'll rebook us on the 6 pm one."),
    ],
    "ceo_fraud_bec": [
        (SPAM, "Subject: Urgent - confidential\n\nHi, I need you to process a wire transfer of $48,500 to a new vendor today. I'm in a board meeting and can't talk, just reply when done. Keep this confidential. - Sent from CEO's iPhone"),
        (SPAM, "Subject: Quick task\n\nAre you at your desk? I need you to buy 10 Google Play gift cards worth Rs 5,000 each for a client. Send me the codes asap, I will reimburse you. Regards, MD"),
        (SPAM, "Subject: Change of bank details\n\nDear Accounts, please note our bank account has changed. Kindly remit all pending invoices to the new acount below immediately, the old account is frozen."),
        (HAM, "Subject: Vendor payment approved\n\nHi Neha, the PO for Infosys has been approved in SAP. Please release the payment as per the usual cycle on the 15th. Thanks, Arjun"),
        (HAM, "Subject: Expense reimbursement\n\nYour expense claim #EXP-2291 for Rs 3,450 has been approved and will be paid with your October salary."),
    ],
    "job_fee": [
        (SPAM, "Congratulations! You are selected for a work from home job at Amazon. Earn Rs 30,000/month. Pay a registration fee of Rs 1,500 to confirm your joining."),
        (SPAM, "Part time job! Ghar baithe YouTube videos like karke roz Rs 3000 kamaye. Registration ke liye Rs 500 bhejein. WhatsApp: 9988776655"),
        (SPAM, "Hiring data entry operators, salry 25k per mnth, no intervew. Pay 999 refundable securty deposit to get the ofer leter"),
        (SPAM, "Dear candidate, your profile is shortlisted for Air India cabin crew. Deposit Rs 7,500 for training kit and interview slot booking."),
        (HAM, "Hi Rishabh, thanks for applying to the Data Analyst role at Razorpay. We'd like to schedule a 30-minute call with the hiring manager this week. Does Thursday 3 PM work?"),
        (HAM, "Subject: Offer letter\n\nPlease find your offer letter attached. Kindly sign and return it by Friday. Your joining date is 1st November. - HR Team"),
    ],
    "emergency_money": [
        (SPAM, "Papa accident ho gaya hai, hospital mein hu. Turant 20,000 is number pe bhejo, phone kharab hai, call mat karna"),
        (SPAM, "Mom its me, I lost my phone and this is my new number. I need Rs 15,000 urgently for an emergency, please send to this UPI id now, I'll explain later"),
        (SPAM, "Uncle aapka beta police station mein hai, case khatam karne ke liye abhi 50 hazar Google Pay karo warna jail jayega"),
        (SPAM, "Hi beta, I am in trubble, plz send 10000 to this acount urjently, dont tell anyone, wil return tmrw"),
        (HAM, "Papa main safely hostel pahunch gaya, kal call karunga"),
        (HAM, "Mom can you send 2000 for my books this month? I'll show you the receipt"),
    ],
}

# Scams that IMITATE the format of genuine alerts. These check that the
# "standard transactional alert" safe signal can't be abused.
INDIA_SCAMS["alert_lookalike_scams"] = [
    (SPAM, "Rs 4,999 credited to your a/c XX1234 as GST refund. To receive it, enter your UPI PIN at http://gst-refund-upi.in"),
    (SPAM, "Your SBI a/c XX4521 is debited Rs 9,999. If not done by you, call 9876543210 immediately to block your account."),
    (SPAM, "Your OTP is 552341. Do not share it with anyone. If you did not request this, click http://sbi-secure-cancel.co to cancel."),
    (SPAM, "Your Amazon order has been shipped but is on hold. Pay Rs 25 delivery charge at amzn-deliver.top to receive it today."),
    (SPAM, "UPI Ref No 334455667788: Rs 2,000 received from PhonePe. Approve the collect request and enter UPI PIN to credit it."),
    (SPAM, "Your KYC has been successfully verified! Click bit.ly/kyc-bonus to claim your Rs 500 reward."),
    (SPAM, "Traffic e-challan of Rs 2,000 pending against your vehicle. Pay now at echallan-parivahan.in/pay to avoid court action."),
    (SPAM, "Subject: Expense claim approved\n\nYour reimbursement of Rs 45,000 has been processed. Please confirm your net banking password at http://hr-payroll-verify.com to receive it."),
]

# Official-domain check: genuine alerts that link to the organisation's OWN domain
# (should be Not spam), the same kind of message with a look-alike link (Spam), and
# scams that add an official link as a decoy (must stay Spam: an official link never
# overrides a strong red flag).
INDIA_SCAMS["official_domains"] = [
    # genuine, official links
    (HAM, "Rs 1,250.00 debited from your HDFC Bank a/c XX4521 on 05-10-26 to VPA swiggy@icici. Not you? Report at https://www.hdfcbank.com/fraud or call 18002586161."),
    (HAM, "Rs 450.00 sent to Ramesh Kumar via UPI on 06-Oct. UPI Ref 427815536201. Not you? Visit https://sbi.bank.in or call 1800-111-109 - SBI"),
    (HAM, "Your Amazon order #405-1234567 has been delivered. Rate your delivery at https://www.amazon.in/your-orders"),
    (HAM, "Rs 2,000.00 credited to your ICICI Bank a/c XX7788 on 06-Oct by NEFT. Avl Bal Rs 12,450.10. Details: https://www.icicibank.com"),
    (HAM, "Your ITR for AY 2026-27 has been processed. Check the status at https://www.incometax.gov.in"),
    (HAM, "Aapka Jio recharge Rs 299 safal raha. Validity 28 din. Details: https://www.jio.com/selfcare"),
    (HAM, "Your OTP for SBI login is 482913. Do not share it with anyone. @onlinesbi.sbi #482913"),
    (HAM, "Your Blue Dart shipment 81234567890 has been dispatched and will be delivered by Friday. Track at https://www.bluedart.com"),
    (HAM, "Download your updated Aadhaar from https://myaadhaar.uidai.gov.in after the update request is completed."),
    # the same kinds of message with look-alike / impersonating links
    (SPAM, "Rs 1,250.00 debited from your HDFC Bank a/c XX4521 on 05-10-26. Not you? Report at https://hdfcbank.com.secure-verify.xyz"),
    (SPAM, "Rs 450.00 sent via UPI. UPI Ref 427815536201. Not you? Raise a dispute at sbi-upi-dispute.com - SBI"),
    (SPAM, "Your Amazon order #405-1234567 has been delivered. Rate your delivery at https://arnazon.in/your-orders"),
    (SPAM, "Rs 2,000.00 credited to your ICICI Bank a/c XX7788. Avl Bal Rs 12,450.10. Details: https://icici-netbanking.in"),
    (SPAM, "Your ITR refund has been processed. Check the status at https://incometax-gov.in/refund"),
    (SPAM, "Aapka Paytm cashback Rs 500 ready hai. Abhi claim karein: paytm-reward.top"),
    (SPAM, "HDFC Bank: your netbanking will be deactivated. Login to continue: hdfcbnk.com/login"),
    (SPAM, "ICICI alert: unusual login detected. Secure your account at 1cici.co/secure"),
    (SPAM, "SBI: your YONO access is paused. Re-activate at http://onlinesbi.sbi@evil.xyz/yono"),
    (SPAM, "Your SBI reward points expire today. Redeem now at sbii-rewards.in"),
    (SPAM, "Dear HDFC customer, verify your account at hdfcbank.co.in.verify.xyz to avoid suspension."),
    (SPAM, "Your HDFC Bank account needs re-verification. Continue at https://hdfcbank.com.evil.xyz/login"),
    # brand named, link goes elsewhere (medium rule)
    (SPAM, "Your Flipkart order is on hold. Confirm your address at bit.ly/fk-addr-123"),
    (SPAM, "Dear Airtel customer, claim your free 5G upgrade at freeupgrade.online today."),
    (SPAM, "Delhivery: your parcel could not be delivered. Reschedule at https://track-parcel-now.com"),
    # scams with an official link as a decoy: strong rules still win
    (SPAM, "HDFC Bank: to stop the debit of Rs 9,999, share the OTP sent to you with our executive. Details at https://www.hdfcbank.com"),
    (SPAM, "CBI notice: your Aadhaar is linked to money laundering. You are under digital arrest. Transfer Rs 1,50,000 for verification. Verify the case at https://cybercrime.gov.in"),
    (SPAM, "PhonePe: you have received Rs 2,000 cashback. Enter your UPI PIN to receive it. https://www.phonepe.com"),
    (SPAM, "Your SBI account will be frozen today. Pay Rs 1,999 penalty to UPI id sbikyc@ybl to avoid it. Official site: https://onlinesbi.sbi"),
    (SPAM, "Congratulations! You won Rs 25 lakh in the Amazon lucky draw. Claim at https://www.amazon.in and call 9876543210."),
]

# Unit checks for the domain matcher itself (domains.classify_host): link -> expected kind.
# official = allowlisted domain or a real sub-domain; lookalike = uses a brand name/typo
# but isn't official; other = unrelated; shortener / neutral = bit.ly etc. / brand short links.
DOMAIN_CASES = [
    ("hdfcbank.com", "official"), ("https://netbanking.hdfcbank.com/x", "official"), ("HDFCBANK.COM", "official"),
    ("onlinesbi.sbi", "official"), ("retail.onlinesbi.sbi", "official"), ("sbi.bank.in", "official"),
    ("hdfc.bank.in", "official"), ("canarabank.bank.in", "official"), ("myaadhaar.uidai.gov.in", "official"),
    ("https://www.incometax.gov.in/iec", "official"), ("rbi.org.in", "official"), ("https://www.delhivery.com/track", "official"),
    ("pay.google.com", "official"), ("echallan.parivahan.gov.in", "official"),
    ("hdfcbank.com.evil.xyz", "lookalike"), ("hdfcbank-kyc.com", "lookalike"), ("sbi-kyc-update.com", "lookalike"),
    ("hdfcbank.co.in.verify.xyz", "lookalike"), ("icici-netbanking.in", "lookalike"), ("paytm-reward.top", "lookalike"),
    ("hdfcbnk.com", "lookalike"), ("hdcfbank.com", "lookalike"), ("sbii.in", "lookalike"), ("1cici.co", "lookalike"),
    ("paypa1-support.net", "lookalike"), ("arnazon.in", "lookalike"), ("uidai-gov.in", "lookalike"),
    ("incometax-gov.in", "lookalike"), ("sbi.bank.in.evil.com", "lookalike"), ("flipkrat-sale.shop", "lookalike"),
    ("http://onlinesbi.sbi@evil.xyz/login", "lookalike"),
    ("gov.in.evil.com", "other"), ("bank.in.evil.com", "other"), ("google.com", "other"), ("praxis.com", "other"),
    ("taxis.in", "other"), ("kodak.com", "other"), ("amazing.in", "other"), ("turbine.com", "other"), ("lesbian.com", "other"),
    ("bit.ly/abc", "shortener"), ("amzn.to/abc", "neutral"), ("paytm.me/x-1", "neutral"),
]


def run_domain_cases(verbose=True):
    """Check domains.analyse_links against DOMAIN_CASES. Returns (passed, total, misses)."""
    from domains import analyse_links
    bad = []
    for link, exp in DOMAIN_CASES:
        got = [l["kind"] for l in analyse_links(link)]
        got = got[0] if got else "none"
        if got != exp:
            bad.append((link, exp, got))
        if verbose:
            print(f"  {'ok  ' if got == exp else 'MISS'} {link:<40} expected {exp:<9} got {got}")
    return len(DOMAIN_CASES) - len(bad), len(DOMAIN_CASES), bad


GROUPS = {"general": GENERAL, "misspelled": MISSPELLED, "hinglish": HINGLISH}
GROUPS.update({f"india:{k}": v for k, v in INDIA_SCAMS.items()})
PROBES = [p for g in GROUPS.values() for p in g]


def run(model, probes=None, unsure=(0.35, 0.65), verbose=True):
    """Return (passed, total, misses). A probe passes when the predicted class
    (P(spam) >= 0.5) matches the expectation."""
    probes = PROBES if probes is None else probes
    texts = [t for _, t in probes]
    probs = model.predict_proba(texts)[:, 1]
    misses = []
    for (exp, text), p in zip(probes, probs):
        pred = SPAM if p >= 0.5 else HAM
        ok = pred == exp
        if not ok:
            misses.append((exp, round(float(p), 3), text))
        if verbose:
            flag = "ok  " if ok else "MISS"
            band = " (unsure)" if unsure[0] <= p < unsure[1] else ""
            print(f"  {flag} exp={exp:<4} p_spam={p:6.3f}{band}  {text[:70]!r}")
    return len(probes) - len(misses), len(probes), misses


if __name__ == "__main__":
    import joblib
    model = joblib.load("model.joblib")
    summary = {}
    for name, group in GROUPS.items():
        print(f"\n[{name}]")
        summary[name] = run(model, group)[:2]
    print("\n[domain matcher]")
    d_ok, d_n, _ = run_domain_cases()
    print()
    for name, (passed, total) in summary.items():
        print(f"  {name:<11} {passed}/{total}")
    print(f"  domain cases {d_ok}/{d_n}")
