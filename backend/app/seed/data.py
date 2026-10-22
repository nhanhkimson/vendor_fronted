"""Seed data ported from the static prototype (website/assets/data.js).

Prices are converted to cents and rates to basis points. Dates are expressed
relative to the day the seed runs, so coupons and holdback windows stay valid.
"""

PERSONAS = [
    {
        "id": "maya",
        "email": "maya@bazaar.local",
        "name": "Maya R.",
        "role": "customer",
        "blurb": "Cross-border buyer · own-order scope",
        "blurb_kh": "អតិថិជនទិញឆ្លងដែន",
        "source": "organic",
        "city": "Phnom Penh",
        "ip": "203.0.113.14",
        "avatar": True,
    },
    {
        "id": "jess",
        "email": "jess@annescraftworks.local",
        "name": "Jess A.",
        "role": "vendor",
        "vendor_id": "V06",
        "blurb": "Independent vendor · Growth tier 12%",
        "blurb_kh": "អ្នកលក់ឯករាជ្យ — កម្រិតរីកចម្រើន",
        "city": "United States",
        "ip": "198.51.100.22",
        "avatar": True,
    },
    {
        "id": "daniel",
        "email": "daniel@bazaar.local",
        "name": "Daniel O.",
        "role": "super_admin",
        "blurb": "Platform owner · Super Admin",
        "blurb_kh": "ម្ចាស់វេទិកា — អ្នកគ្រប់គ្រងជាន់ខ្ពស់",
        "city": "Phnom Penh",
        "ip": "10.0.0.8",
        "avatar": True,
    },
    {
        "id": "ava",
        "email": "ava@bazaar.local",
        "name": "Ava K.",
        "role": "admin",
        "blurb": "Operations admin · verification, coupons, commission",
        "blurb_kh": "អ្នកគ្រប់គ្រងប្រតិបត្តិការ",
        "city": "Phnom Penh",
        "ip": "10.0.0.9",
        "avatar": False,
    },
    {
        "id": "lin",
        "email": "lin@bazaar.local",
        "name": "Lin S.",
        "role": "support",
        "blurb": "Support agent · reviews, disputes, payout co-signer",
        "blurb_kh": "ភ្នាក់ងារជំនួយ",
        "city": "Phnom Penh",
        "ip": "10.0.0.12",
        "avatar": True,
    },
    {
        "id": "kein",
        "email": "kein@keinmaker.local",
        "name": "Kein Maker",
        "role": "vendor",
        "vendor_id": "V04",
        "blurb": "Power seller · Power tier 6%",
        "blurb_kh": "អ្នកលក់ធំ",
        "city": "United States",
        "ip": "198.51.100.44",
        "avatar": True,
    },
    {
        "id": "theo",
        "email": "theo@mail.local",
        "name": "Theo P.",
        "role": "customer",
        "blurb": "Acquired via WELCOME10",
        "blurb_kh": "អតិថិជនពីគូប៉ុង",
        "source": "coupon",
        "city": "Lisbon",
        "ip": "198.51.100.80",
        "avatar": False,
    },
    {
        "id": "priya",
        "email": "priya@mail.local",
        "name": "Priya S.",
        "role": "customer",
        "blurb": "Came from Instagram",
        "blurb_kh": "អតិថិជនពីសង្គម",
        "source": "social",
        "city": "Singapore",
        "ip": "203.0.113.90",
        "avatar": False,
    },
]

# Customers behind the historical orders that feed the reports.
HISTORY_CUSTOMERS = [
    ("sophea", "Sophea K.", "Phnom Penh", "organic"),
    ("dara", "Dara M.", "Siem Reap", "social"),
    ("lena", "Lena V.", "Berlin", "organic"),
    ("omar", "Omar H.", "Dubai", "referral"),
    ("grace", "Grace L.", "Toronto", "coupon"),
    ("ken", "Ken T.", "Osaka", "social"),
    ("sara", "Sara B.", "Austin", "organic"),
    ("mateo", "Mateo R.", "Madrid", "referral"),
    ("ana", "Ana P.", "Lisbon", "coupon"),
    ("yuki", "Yuki N.", "Tokyo", "organic"),
]

DEMO_ACCOUNTS = [
    {
        "email": "maya@bazaar.local",
        "name": "Maya R.",
        "role": "customer",
        "home": "/account",
        "try_this": "Shop two shops in one cart, pay with 4242 4242 4242 4242, track each shipment, open a dispute.",
        "blurb_kh": "អតិថិជន",
    },
    {
        "email": "jess@annescraftworks.local",
        "name": "Jess A.",
        "role": "vendor",
        "home": "/seller",
        "try_this": "Ship sub-order O-1001-V06, restock the mug wrap, reply to a review, request a payout.",
        "blurb_kh": "អ្នកលក់",
    },
    {
        "email": "kein@keinmaker.local",
        "name": "Kein Maker",
        "role": "vendor",
        "home": "/seller",
        "try_this": "Request payout PAY-04. Try to open Jess's order and get a 404: tenants are isolated.",
        "blurb_kh": "អ្នកលក់ធំ",
    },
    {
        "email": "daniel@bazaar.local",
        "name": "Daniel O.",
        "role": "super_admin",
        "home": "/admin",
        "try_this": "Edit the permission matrix, assign roles, archive the activity log, first payout signature.",
        "blurb_kh": "អ្នកគ្រប់គ្រងជាន់ខ្ពស់",
    },
    {
        "email": "ava@bazaar.local",
        "name": "Ava K.",
        "role": "admin",
        "home": "/admin",
        "try_this": "Verify SimplyCreativeJess, create a coupon, change a commission rate, resolve dispute D1.",
        "blurb_kh": "អ្នកគ្រប់គ្រង",
    },
    {
        "email": "lin@bazaar.local",
        "name": "Lin S.",
        "role": "support",
        "home": "/admin",
        "try_this": "Search the activity log, moderate a review, add the second payout signature.",
        "blurb_kh": "ភ្នាក់ងារជំនួយ",
    },
    {
        "email": "theo@mail.local",
        "name": "Theo P.",
        "role": "customer",
        "home": "/account",
        "try_this": "Already used WELCOME10 once, so the coupon is refused (one per customer).",
        "blurb_kh": "អតិថិជន",
    },
]

TIERS = [
    {"id": "starter", "name": "Starter", "name_kh": "កម្រិតចាប់ផ្តើម", "min": 0, "max": 100},
    {"id": "growth", "name": "Growth", "name_kh": "កម្រិតរីកចម្រើន", "min": 101, "max": 1000},
    {"id": "established", "name": "Established", "name_kh": "កម្រិតរឹងមាំ", "min": 1001, "max": 10000},
    {"id": "power", "name": "Power Seller", "name_kh": "អ្នកលក់ធំ", "min": 10001, "max": None},
]


def tier_for_sales(sales: int) -> str:
    for tier in TIERS:
        if sales >= tier["min"] and (tier["max"] is None or sales <= tier["max"]):
            return tier["id"]
    return "starter"


WAREHOUSES = [
    ("WH-EAST", "East Coast hub", "Ohio, USA"),
    ("WH-SOUTH", "South hub", "Kentucky, USA"),
    ("WH-TX", "Dallas studio", "Dallas, TX"),
    ("WH-VT", "Vermont barn", "South Burlington, VT"),
    ("WH-CA", "Ontario loft", "Bowmanville, Canada"),
    ("WH-UK", "Teesside studio", "Stockton-on-Tees, UK"),
]

VENDORS = [
    {"id": "V01", "name": "CustomByInstant", "country": "US", "city": "Ohio, USA", "sales": 272, "rating": 5.0, "reviews": 60, "since": "2026-06-01", "catalog": "Medium", "hue": 12, "wh": "WH-EAST", "headline": "Names, ready this week.", "about": "Laser-cut maple plaques and tags from a two-person Ohio studio."},
    {"id": "V02", "name": "PrettyLittleCustom1", "country": "UK", "city": "Stockton-on-Tees, UK", "sales": 22, "rating": 5.0, "reviews": 5, "since": "2025-12-01", "catalog": "Small", "hue": 32, "wh": "WH-UK", "headline": "Tiny florals, small batches.", "about": "Polymer clay hair pieces made in Teesside."},
    {"id": "V03", "name": "VonDelleStitching", "country": "CA", "city": "Bowmanville, Canada", "sales": 562, "rating": 5.0, "reviews": 206, "since": "2023-08-01", "catalog": "Medium", "hue": 152, "wh": "WH-CA", "headline": "Botanical stitches on linen.", "about": "Canadian linen samplers and hoops."},
    {"id": "V04", "name": "KeinMaker", "country": "US", "city": "United States", "sales": 220578, "rating": 4.9, "reviews": 16173, "since": "2024-02-01", "catalog": "Large", "hue": 200, "wh": "WH-EAST", "outlier": True, "headline": "Workshop kit for serious makers.", "about": "High-volume canvas, brass and tool wraps. Power-seller tier."},
    {"id": "V05", "name": "MarMadeThat", "country": "US", "city": "South Burlington, VT", "sales": 625, "rating": 4.96, "rating_flag": "estimated", "reviews": 131, "since": "2019-08-01", "catalog": "Medium", "hue": 280, "wh": "WH-VT", "headline": "Maple from the Green Mountains.", "about": "End-grain boards from a Vermont barn shop."},
    {"id": "V06", "name": "AnnesCraftworks", "country": "US", "city": "United States", "sales": 467, "rating": 5.0, "reviews": 130, "since": "2020-08-01", "catalog": "Medium", "hue": 18, "wh": "WH-EAST", "headline": "Wool, linen and quiet colour.", "about": "Jess's Growth-tier home textiles studio. The demo vendor for tenant isolation."},
    {"id": "V07", "name": "FirstSundayHandmade", "country": "US", "city": "United States", "sales": 124, "rating": 5.0, "reviews": 39, "since": "2015-08-01", "catalog": "Small", "hue": 48, "wh": "WH-EAST", "headline": "Market totes since 2015.", "about": "Heavy cotton totes. Has an open dispute in the demo seed."},
    {"id": "V08", "name": "CJsHandmadeLLC", "country": "US", "city": "Mt. Washington, KY", "sales": 4229, "rating": 4.7, "reviews": 788, "since": "2020-08-01", "catalog": "Large", "hue": 220, "wh": "WH-SOUTH", "headline": "Veg-tan from Kentucky.", "about": "Leather fobs and journal covers, saddle stitched."},
    {"id": "V09", "name": "AnnalieHandmade", "country": "US", "city": "Dallas, TX", "sales": 7355, "rating": 5.0, "reviews": 1651, "since": "2017-08-01", "catalog": "Large", "hue": 330, "wh": "WH-TX", "headline": "Speckled stoneware, one glaze at a time.", "about": "Dallas clay studio. Established tier."},
    {"id": "V10", "name": "SimplyCreativeJess", "country": "US", "city": "United States", "sales": 6, "rating": 5.0, "reviews": 3, "since": "2021-08-01", "catalog": "Small", "hue": 95, "wh": "WH-EAST", "status": "under_review", "headline": "Watercolour bookmarks, starter shop.", "about": "Awaiting document verification in the demo. Six lifetime sales."},
]

SHIPPING_FEE_CENTS = {"US": 500, "CA": 650, "UK": 750}

DOCUMENTS = [
    ("DOC-01", "V01", "government_id", "Government ID", "verified"),
    ("DOC-02", "V01", "address_proof", "Address proof", "verified"),
    ("DOC-10a", "V10", "government_id", "Government ID", "submitted"),
    ("DOC-10b", "V10", "address_proof", "Address proof", "missing"),
    ("DOC-10c", "V10", "payout_account", "Payout account token", "submitted"),
]

CATEGORIES = [
    ("c1", "Jewelry", "គ្រឿងអលង្ការ", "jewelry", None),
    ("c1a", "Hair accessories", "គ្រឿងសក់", "hair-accessories", "c1"),
    ("c1b", "Leather goods", "ស្បែក", "leather-goods", "c1"),
    ("c2", "Home", "ផ្ទះ", "home", None),
    ("c2a", "Textiles", "ក្រណាត់", "textiles", "c2"),
    ("c2b", "Wood & kitchen", "ឈើ និងផ្ទះបាយ", "wood-kitchen", "c2"),
    ("c2c", "Ceramics", "សេរ៉ាមិច", "ceramics", "c2"),
    ("c3", "Wearables", "សម្លៀកបំពាក់", "wearables", None),
    ("c3a", "Bags & totes", "កាបូប", "bags", "c3"),
    ("c4", "Stationery", "សម្ភារៈសរសេរ", "stationery", None),
    ("c5", "Custom gifts", "អំណោយតាមបញ្ជា", "custom-gifts", None),
]

TAGS = [
    ("t-custom", "custom"),
    ("t-gift", "gift"),
    ("t-small", "small-batch"),
    ("t-emb", "embroidery"),
    ("t-maker", "maker"),
    ("t-tools", "tools"),
    ("t-wood", "wood"),
    ("t-home", "home"),
    ("t-bag", "bag"),
    ("t-leather", "leather"),
    ("t-ceramic", "ceramic"),
    ("t-paper", "paper"),
]

PRODUCTS = [
    {"id": "P01", "vendor": "V01", "title": "Instant custom name plaque", "price": 28, "stock": 14, "cat": "c5", "tags": ["custom", "gift"], "low": 4, "blurb": "Laser-cut maple, ready in days. Gift box included."},
    {"id": "P02", "vendor": "V01", "title": "Same-week monogram tag", "price": 16, "stock": 32, "cat": "c5", "tags": ["custom", "gift"], "low": 6, "blurb": "Bag charm with two initials. Ships from Ohio."},
    {"id": "P03", "vendor": "V02", "title": "Tiny floral hair clip", "price": 12, "cat": "c1a", "tags": ["small-batch"], "low": 3, "blurb": "Polymer clay blossom. Small-batch UK studio.", "variants": [("P03-blush", "P03-BLUSH", "One size", "Blush", 5), ("P03-sage", "P03-SAGE", "One size", "Sage", 3)]},
    {"id": "P04", "vendor": "V03", "title": "Hand-stitched linen sampler", "price": 48, "stock": 11, "cat": "c2a", "tags": ["embroidery", "home"], "low": 3, "blurb": "Canadian linen, botanical stitches, 12 inch."},
    {"id": "P05", "vendor": "V03", "title": "Botanical hoop 8 inch", "price": 36, "stock": 7, "cat": "c2a", "tags": ["embroidery"], "low": 2, "blurb": "Pressed-leaf hoop. Ready to hang."},
    {"id": "P06", "vendor": "V04", "title": "Workshop tool wrap", "price": 42, "stock": 86, "cat": "c2b", "tags": ["maker", "tools"], "low": 12, "blurb": "Waxed canvas roll for chisels and gauges."},
    {"id": "P07", "vendor": "V04", "title": "Maker apron, heavy canvas", "price": 58, "cat": "c3", "tags": ["maker"], "low": 8, "blurb": "Cross-back apron. A power-seller staple.", "variants": [("P07-s", "P07-S", "S", "Canvas", 10), ("P07-m", "P07-M", "M", "Canvas", 18), ("P07-l", "P07-L", "L", "Canvas", 12)]},
    {"id": "P08", "vendor": "V04", "title": "Brass marking gauge", "price": 34, "stock": 120, "cat": "c2b", "tags": ["tools", "maker"], "low": 20, "blurb": "Solid brass. KeinMaker workshop line."},
    {"id": "P09", "vendor": "V05", "title": "Vermont maple cutting board", "price": 64, "stock": 9, "cat": "c2b", "tags": ["wood"], "low": 3, "blurb": "End-grain maple from South Burlington."},
    {"id": "P10", "vendor": "V06", "title": "Wool felt coaster set", "price": 22, "cat": "c2a", "tags": ["home"], "low": 5, "blurb": "Set of four. Merino felt from a Growth-tier shop.", "variants": [("P10-nat", "P10-NAT", "Set of 4", "Natural", 11), ("P10-ch", "P10-CHR", "Set of 4", "Charcoal", 7)]},
    {"id": "P11", "vendor": "V06", "title": "Quilted mug wrap", "price": 19, "stock": 1, "cat": "c2a", "tags": ["home"], "low": 4, "blurb": "Last unit in stock: the demo low-stock alert."},
    {"id": "P12", "vendor": "V06", "title": "Linen produce bag trio", "price": 26, "stock": 15, "cat": "c2a", "tags": ["home", "bag"], "low": 4, "blurb": "Drawstring bags. Machine washable."},
    {"id": "P13", "vendor": "V07", "title": "Sunday market tote", "price": 32, "stock": 6, "cat": "c3a", "tags": ["bag"], "low": 2, "blurb": "Heavy cotton tote. Eleven years on the platform."},
    {"id": "P14", "vendor": "V08", "title": "Kentucky leather key fob", "price": 18, "cat": "c1b", "tags": ["leather"], "low": 8, "blurb": "Veg-tan leather, brass snap.", "variants": [("P14-tan", "P14-TAN", "One size", "Tan", 24), ("P14-ox", "P14-OX", "One size", "Oxblood", 20)]},
    {"id": "P15", "vendor": "V08", "title": "Stitched journal cover", "price": 39, "stock": 21, "cat": "c4", "tags": ["leather", "paper"], "low": 5, "blurb": "Fits A5 notebooks. Saddle stitch."},
    {"id": "P16", "vendor": "V09", "title": "Dallas clay bud vase", "price": 29, "stock": 17, "cat": "c2c", "tags": ["ceramic"], "low": 4, "blurb": "Speckled stoneware, one-of-a-kind glaze."},
    {"id": "P17", "vendor": "V09", "title": "Speckled espresso cup", "price": 24, "cat": "c2c", "tags": ["ceramic"], "low": 6, "blurb": "4 oz cup. Dishwasher safe.", "variants": [("P17-sp", "P17-SP", "4 oz", "Speckled", 14), ("P17-ink", "P17-INK", "4 oz", "Ink", 11)]},
    {"id": "P18", "vendor": "V10", "title": "Mini watercolor bookmark", "price": 8, "stock": 3, "cat": "c4", "tags": ["paper", "gift"], "low": 2, "blurb": "Painted by a six-sale starter shop."},
]

REVIEWS = [
    ("R01", "ebay", 1.5, "negative", "shipping_delay", "Waited over a week with no delivery, asked for a refund.", "V07", "P13", "maya"),
    ("R02", "ebay", 1.0, "negative", "no_response", "Messaged the seller repeatedly about an unshipped order, no reply.", "V02", "P03", "theo"),
    ("R03", "etsy", None, "friction", "metric_noise", "Response-rate score dropped because of an unrelated buyer-side message.", "V06", "P10", "maya"),
    ("R04", "ebay", 5, "positive", "fast_shipping", "Item arrived quickly and was carefully packaged.", "V06", "P10", "priya"),
    ("R05", "ebay", 5, "positive", "communication", "Praised quality, packaging and responsiveness in one order.", "V09", "P16", "maya"),
    ("R06", "ebay", 5, "positive", "international_shipping", "Overseas buyer highlighted fast delivery and good communication.", "V03", "P04", "maya"),
    ("R07", "ebay", 5, "positive", "care_packaging", "Buyer felt the seller genuinely cared, citing thoughtful packaging.", "V08", "P14", "theo"),
    ("R08", "ebay", 5, "positive", "value_speed", "Quick delivery and good value for money.", "V01", "P01", "priya"),
    ("R09", "ebay", 5, "positive", "early_delivery", "Arrived earlier than expected, well packaged.", "V05", "P09", "theo"),
    ("R10", "etsy", 5, "positive", "seller_reply", "Seller personally replied thanking the buyer; item arrived before a holiday deadline.", "V06", "P12", "maya"),
]

# code, funded_by, vendor, type, value, min $, start offset days, length days, limit, used, per customer, flash, note
COUPONS = [
    ("WELCOME10", "platform", None, "percent", 10, 20, -150, 330, 500, 41, 1, False, "Platform-funded. Does not reduce the vendor's net or commission base."),
    ("ANNE5", "vendor", "V06", "percent", 5, 15, -140, 260, 80, 12, 2, False, "Vendor-funded by AnnesCraftworks. Commission is charged on the discounted amount."),
    ("FLASH24", "platform", None, "percent", 20, 30, 0, 1, 100, 8, 1, True, "Flash window: 24 hours. The platform absorbs the discount."),
]

# id, name, target type, target id, rate bps, min fee cents
COMMISSION_RULES = [
    ("CR-PLAT", "Platform default", "platform", "*", 1500, 30),
    ("CR-START", "Starter tier", "tier", "starter", 1500, 30),
    ("CR-GROW", "Growth tier", "tier", "growth", 1200, 30),
    ("CR-EST", "Established tier", "tier", "established", 900, 50),
    ("CR-POW", "Power seller tier", "tier", "power", 600, 50),
]

# The six named orders from the prototype. lines: (product, variant or None, qty).
NAMED_ORDERS = [
    {"id": "O-1001", "buyer": "maya", "source": "organic", "days_ago": 7, "lines": [("P10", "P10-nat", 1), ("P04", None, 1)], "statuses": {"V06": "packing", "V03": "shipped"}, "tracking": {"V03": "CA-44821"}},
    {"id": "O-1002", "buyer": "maya", "source": "organic", "days_ago": 13, "lines": [("P13", None, 1)], "statuses": {"V07": "shipped"}, "tracking": {"V07": "US-77310"}},
    {"id": "O-1003", "buyer": "maya", "source": "organic", "days_ago": 16, "lines": [("P16", None, 1)], "statuses": {"V09": "delivered"}, "tracking": {"V09": "TX-99102"}},
    {"id": "O-1004", "buyer": "theo", "source": "coupon", "coupon": "WELCOME10", "days_ago": 5, "lines": [("P07", "P07-m", 1), ("P08", None, 1)], "statuses": {"V04": "delivered"}, "tracking": {"V04": "US-22011"}},
    {"id": "O-1005", "buyer": "priya", "source": "social", "days_ago": 3, "lines": [("P09", None, 1)], "statuses": {"V05": "shipped"}, "tracking": {"V05": "VT-1882"}},
    {"id": "O-1006", "buyer": "maya", "source": "organic", "days_ago": 1, "lines": [("P01", None, 1)], "statuses": {"V01": "accepted"}},
]

# Earnings accrued before the demo period, paid out through the seeded payouts.
OPENING_BALANCES = {"V04": 920000, "V06": 18480, "V07": 9600, "V09": 126000}

# id, vendor, amount, status, note
PAYOUTS = [
    ("PAY-04", "V04", 920000, "eligible", "Power-seller weekly window, past the holdback"),
    ("PAY-06", "V06", 18480, "eligible", "Statement window, past the holdback"),
    ("PAY-07", "V07", 9600, "held_for_dispute", "Held while dispute D1 is open"),
    ("PAY-09", "V09", 126000, "paid", "September statement"),
]
