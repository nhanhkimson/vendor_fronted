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
        "blurb": "អតិថិជនទិញឆ្លងដែន · មើលតែការកម្មង់ផ្ទាល់ខ្លួន",
        "blurb_kh": "អតិថិជនទិញឆ្លងដែន",
        "source": "organic",
        "city": "ភ្នំពេញ",
        "ip": "203.0.113.14",
        "avatar": True,
    },
    {
        "id": "jess",
        "email": "jess@annescraftworks.local",
        "name": "Jess A.",
        "role": "vendor",
        "vendor_id": "V06",
        "blurb": "អ្នកលក់ឯករាជ្យ — កម្រិតរីកចម្រើន ១២%",
        "blurb_kh": "អ្នកលក់ឯករាជ្យ — កម្រិតរីកចម្រើន",
        "city": "ភ្នំពេញ",
        "ip": "198.51.100.22",
        "avatar": True,
    },
    {
        "id": "daniel",
        "email": "daniel@bazaar.local",
        "name": "Daniel O.",
        "role": "super_admin",
        "blurb": "ម្ចាស់វេទិកា — អ្នកគ្រប់គ្រងជាន់ខ្ពស់",
        "blurb_kh": "ម្ចាស់វេទិកា — អ្នកគ្រប់គ្រងជាន់ខ្ពស់",
        "city": "ភ្នំពេញ",
        "ip": "10.0.0.8",
        "avatar": True,
    },
    {
        "id": "ava",
        "email": "ava@bazaar.local",
        "name": "Ava K.",
        "role": "admin",
        "blurb": "អ្នកគ្រប់គ្រងប្រតិបត្តិការ · ផ្ទៀងផ្ទាត់ គូប៉ុង កម្រៃ",
        "blurb_kh": "អ្នកគ្រប់គ្រងប្រតិបត្តិការ",
        "city": "ភ្នំពេញ",
        "ip": "10.0.0.9",
        "avatar": False,
    },
    {
        "id": "lin",
        "email": "lin@bazaar.local",
        "name": "Lin S.",
        "role": "support",
        "blurb": "ភ្នាក់ងារជំនួយ · ពិនិត្យ មតិ វិវាទ ចុះហត្ថលេខាទូទាត់",
        "blurb_kh": "ភ្នាក់ងារជំនួយ",
        "city": "ភ្នំពេញ",
        "ip": "10.0.0.12",
        "avatar": True,
    },
    {
        "id": "kein",
        "email": "kein@keinmaker.local",
        "name": "Kein Maker",
        "role": "vendor",
        "vendor_id": "V04",
        "blurb": "អ្នកលក់ធំ — កម្រិតអ្នកលក់ធំ ៦%",
        "blurb_kh": "អ្នកលក់ធំ",
        "city": "ភ្នំពេញ",
        "ip": "198.51.100.44",
        "avatar": True,
    },
    {
        "id": "theo",
        "email": "theo@mail.local",
        "name": "Theo P.",
        "role": "customer",
        "blurb": "អតិថិជនពីគូប៉ុង WELCOME10",
        "blurb_kh": "អតិថិជនពីគូប៉ុង",
        "source": "coupon",
        "city": "ភ្នំពេញ",
        "ip": "198.51.100.80",
        "avatar": False,
    },
    {
        "id": "priya",
        "email": "priya@mail.local",
        "name": "Priya S.",
        "role": "customer",
        "blurb": "អតិថិជនពីសង្គម (Instagram)",
        "blurb_kh": "អតិថិជនពីសង្គម",
        "source": "social",
        "city": "សៀមរាប",
        "ip": "203.0.113.90",
        "avatar": False,
    },
]

# Customers behind the historical orders that feed the reports.
HISTORY_CUSTOMERS = [
    ("sophea", "សុភា ក.", "ភ្នំពេញ", "organic"),
    ("dara", "តារា ម.", "សៀមរាប", "social"),
    ("lena", "លីណា វ.", "បាត់ដំបង", "organic"),
    ("omar", "អូម៉ារ ហ.", "កំពត", "referral"),
    ("grace", "គ្រេស ល.", "តាកែវ", "coupon"),
    ("ken", "គេន ត.", "កំពង់ឆ្នាំង", "social"),
    ("sara", "សារ៉ា ប.", "កណ្ដាល", "organic"),
    ("mateo", "ម៉ាតេអូ រ.", "ព្រៃវែង", "referral"),
    ("ana", "អាណា ផ.", "កែប", "coupon"),
    ("yuki", "យូគី ន.", "ប៉ៃលិន", "organic"),
]

DEMO_ACCOUNTS = [
    {
        "email": "maya@bazaar.local",
        "name": "Maya R.",
        "role": "customer",
        "home": "/",
        "try_this": "Shop and check out.",
        "blurb_kh": "អតិថិជន",
    },
    {
        "email": "jess@annescraftworks.local",
        "name": "Jess A.",
        "role": "vendor",
        "home": "/seller",
        "try_this": "Run the shop and add products.",
        "blurb_kh": "អ្នកលក់",
    },
    {
        "email": "kein@keinmaker.local",
        "name": "Kein Maker",
        "role": "vendor",
        "home": "/seller",
        "try_this": "Run a second shop.",
        "blurb_kh": "អ្នកលក់ធំ",
    },
    {
        "email": "daniel@bazaar.local",
        "name": "Daniel O.",
        "role": "super_admin",
        "home": "/admin",
        "try_this": "Manage staff and payouts.",
        "blurb_kh": "អ្នកគ្រប់គ្រងជាន់ខ្ពស់",
    },
    {
        "email": "ava@bazaar.local",
        "name": "Ava K.",
        "role": "admin",
        "home": "/admin",
        "try_this": "Approve shops and listings.",
        "blurb_kh": "អ្នកគ្រប់គ្រង",
    },
    {
        "email": "lin@bazaar.local",
        "name": "Lin S.",
        "role": "support",
        "home": "/admin",
        "try_this": "Help buyers and sellers.",
        "blurb_kh": "ភ្នាក់ងារជំនួយ",
    },
    {
        "email": "theo@mail.local",
        "name": "Theo P.",
        "role": "customer",
        "home": "/",
        "try_this": "Shop as a second buyer.",
        "blurb_kh": "អតិថិជន",
    },
]

TIERS = [
    {"id": "starter", "name": "កម្រិតចាប់ផ្តើម", "name_kh": "កម្រិតចាប់ផ្តើម", "min": 0, "max": 100},
    {"id": "growth", "name": "កម្រិតរីកចម្រើន", "name_kh": "កម្រិតរីកចម្រើន", "min": 101, "max": 1000},
    {"id": "established", "name": "កម្រិតរឹងមាំ", "name_kh": "កម្រិតរឹងមាំ", "min": 1001, "max": 10000},
    {"id": "power", "name": "អ្នកលក់ធំ", "name_kh": "អ្នកលក់ធំ", "min": 10001, "max": None},
]


def tier_for_sales(sales: int) -> str:
    for tier in TIERS:
        if sales >= tier["min"] and (tier["max"] is None or sales <= tier["max"]):
            return tier["id"]
    return "starter"


WAREHOUSES = [
    ("WH-EAST", "ឃ្លាំងភ្នំពេញ", "ភ្នំពេញ"),
    ("WH-SOUTH", "ឃ្លាំងតាកែវ", "តាកែវ"),
    ("WH-TX", "ស្ទូឌីយ៉ូសៀមរាប", "សៀមរាប"),
    ("WH-VT", "សិប្បកម្មបាត់ដំបង", "បាត់ដំបង"),
    ("WH-CA", "សិប្បកម្មកំពង់ឆ្នាំង", "កំពង់ឆ្នាំង"),
    ("WH-UK", "សិប្បកម្មកំពត", "កំពត"),
]

VENDORS = [
    {"id": "V01", "name": "ឈើឆ្លាក់ភ្នំពេញ", "slug": "chheur-chlak-phnom-penh", "country": "KH", "city": "ភ្នំពេញ", "sales": 272, "rating": 5.0, "reviews": 60, "since": "2026-06-01", "catalog": "Medium", "hue": 12, "wh": "WH-EAST", "headline": "ឈ្មោះឆ្លាក់ តាមបញ្ជា។", "about": "សិប្បកម្មឈើឆ្លាក់គ្រួសារពីរនាក់នៅភ្នំពេញ។"},
    {"id": "V02", "name": "ផ្កាដីឥដ្ឋតូច", "slug": "phka-dei-doch", "country": "KH", "city": "កំពត", "sales": 22, "rating": 5.0, "reviews": 5, "since": "2025-12-01", "catalog": "Small", "hue": 32, "wh": "WH-UK", "headline": "ខ្ទាស់សក់ផ្កា បាច់តូច។", "about": "គ្រឿងសក់ដីឥដ្ឋប៉ូលីម័រ ផលិតនៅកំពត។"},
    {"id": "V03", "name": "សូត្រលើកដៃ", "slug": "sout-loek-dai", "country": "KH", "city": "សៀមរាប", "sales": 562, "rating": 5.0, "reviews": 206, "since": "2023-08-01", "catalog": "Medium", "hue": 152, "wh": "WH-TX", "headline": "លើករូបសូត្រខ្មែរ។", "about": "កម្រាល និងរង្វង់លើករូបពីសៀមរាប។"},
    {"id": "V04", "name": "សិប្បករធំខ្មែរ", "slug": "sibakar-thom-khmer", "country": "KH", "city": "ភ្នំពេញ", "sales": 220578, "rating": 4.9, "reviews": 16173, "since": "2024-02-01", "catalog": "Large", "hue": 200, "wh": "WH-EAST", "outlier": True, "headline": "ឧបករណ៍សម្រាប់សិប្បករ។", "about": "ឆៀង ក្រណាត់រុំ និងឧបករណ៍ស្ពាន់លឿង កម្រិតអ្នកលក់ធំ។"},
    {"id": "V05", "name": "ឈើទន្លេសាប", "slug": "chheur-tonle-sap", "country": "KH", "city": "កំពង់ឆ្នាំង", "sales": 625, "rating": 4.96, "rating_flag": "estimated", "reviews": 131, "since": "2019-08-01", "catalog": "Medium", "hue": 280, "wh": "WH-CA", "headline": "ឈើពីតំបន់ទន្លេសាប។", "about": "ក្តារកាត់ និងគ្រឿងផ្ទះបាយឈើពីកំពង់ឆ្នាំង។"},
    {"id": "V06", "name": "ក្រណាត់ផ្ទះ Jess", "slug": "kror-nat-phteah-jess", "country": "KH", "city": "ភ្នំពេញ", "sales": 467, "rating": 5.0, "reviews": 130, "since": "2020-08-01", "catalog": "Medium", "hue": 18, "wh": "WH-EAST", "headline": "ក្រណាត់ផ្ទះ ស្រស់ស្ងប់។", "about": "ហាងក្រណាត់ផ្ទះរបស់ Jess — ប្រើសម្រាប់សាកល្បងការបំបែកហាង។"},
    {"id": "V07", "name": "ទីផ្សារថ្ងៃអាទិត្យ", "slug": "tipsa-thngai-atit", "country": "KH", "city": "ភ្នំពេញ", "sales": 124, "rating": 5.0, "reviews": 39, "since": "2015-08-01", "catalog": "Small", "hue": 48, "wh": "WH-EAST", "headline": "កាបូបទីផ្សារតាំងពី ២០១៥។", "about": "កាបូបកប្បាសក្រាស់។ មានវិវាទបើកក្នុងទិន្នន័យសាកល្បង។"},
    {"id": "V08", "name": "ស្បែកក្របីសៀមរាប", "slug": "sbaek-krabei-siem-reap", "country": "KH", "city": "សៀមរាប", "sales": 4229, "rating": 4.7, "reviews": 788, "since": "2020-08-01", "catalog": "Large", "hue": 220, "wh": "WH-TX", "headline": "ស្បែកក្របីដេរដៃ។", "about": "ខ្សែសោ និងគម្របសៀវភៅស្បែក។"},
    {"id": "V09", "name": "ដីឥដ្ឋខ្មែរ", "slug": "dei-doch-khmer", "country": "KH", "city": "កំពត", "sales": 7355, "rating": 5.0, "reviews": 1651, "since": "2017-08-01", "catalog": "Large", "hue": 330, "wh": "WH-UK", "headline": "ថូដីឥដ្ឋ លាបមួយៗ។", "about": "ស្ទូឌីយ៉ូដីឥដ្ឋកំពត។"},
    {"id": "V10", "name": "សិល្បៈក្រដាសថ្មី", "slug": "selapak-kradas-thmei", "country": "KH", "city": "ភ្នំពេញ", "sales": 6, "rating": 5.0, "reviews": 3, "since": "2021-08-01", "catalog": "Small", "hue": 95, "wh": "WH-EAST", "status": "under_review", "headline": "សៀវភៅសម្គាល់ទំព័រ ហាងថ្មី។", "about": "រង់ចាំផ្ទៀងផ្ទាត់ឯកសារ។ លក់បាន ៦ ដង។"},
]

SHIPPING_FEE_CENTS = {"KH": 300, "US": 500, "CA": 650, "UK": 750}

DOCUMENTS = [
    ("DOC-01", "V01", "government_id", "អត្តសញ្ញាណប័ណ្ណ", "verified"),
    ("DOC-02", "V01", "address_proof", "ភស្តុតាងអាសយដ្ឋាន", "verified"),
    ("DOC-10a", "V10", "government_id", "អត្តសញ្ញាណប័ណ្ណ", "submitted"),
    ("DOC-10b", "V10", "address_proof", "ភស្តុតាងអាសយដ្ឋាន", "submitted"),
    ("DOC-10c", "V10", "payout_account", "គណនីទូទាត់", "submitted"),
]

CATEGORIES = [
    ("c1", "គ្រឿងអលង្ការ", "គ្រឿងអលង្ការ", "jewelry", None),
    ("c1a", "គ្រឿងសក់", "គ្រឿងសក់", "hair-accessories", "c1"),
    ("c1b", "ស្បែក", "ស្បែក", "leather-goods", "c1"),
    ("c2", "ផ្ទះ", "ផ្ទះ", "home", None),
    ("c2a", "ក្រណាត់", "ក្រណាត់", "textiles", "c2"),
    ("c2b", "ឈើ និងផ្ទះបាយ", "ឈើ និងផ្ទះបាយ", "wood-kitchen", "c2"),
    ("c2c", "សេរ៉ាមិច", "សេរ៉ាមិច", "ceramics", "c2"),
    ("c3", "សម្លៀកបំពាក់", "សម្លៀកបំពាក់", "wearables", None),
    ("c3a", "កាបូប", "កាបូប", "bags", "c3"),
    ("c4", "សម្ភារៈសរសេរ", "សម្ភារៈសរសេរ", "stationery", None),
    ("c5", "អំណោយតាមបញ្ជា", "អំណោយតាមបញ្ជា", "custom-gifts", None),
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
    {"id": "P01", "vendor": "V01", "title": "ផ្ទាំងឈ្មោះឈើឆ្លាក់តាមបញ្ជា", "price": 28, "stock": 14, "cat": "c5", "tags": ["custom", "gift"], "low": 4, "blurb": "ឈើខ្មៅឆ្លាក់ឈ្មោះតាមបញ្ជា រួចក្នុងពីរបីថ្ងៃ ភ្ជាប់ប្រអប់អំណោយ។"},
    {"id": "P02", "vendor": "V01", "title": "ស្លាកអក្សរកាត់ឈើ", "price": 16, "stock": 32, "cat": "c5", "tags": ["custom", "gift"], "low": 6, "blurb": "ស្លាកកាបូបឈើមានអក្សរពីរ ផលិតនៅភ្នំពេញ។"},
    {"id": "P03", "vendor": "V02", "title": "ខ្ទាស់សក់ផ្ការំដួល", "price": 12, "cat": "c1a", "tags": ["small-batch"], "low": 3, "blurb": "ខ្ទាស់សក់ដីឥដ្ឋប៉ូលីម័រ រូបផ្ការំដួល ផលិតតិចៗ។", "variants": [("P03-blush", "P03-BLUSH", "ទំហំមួយ", "ផ្កាលឿង", 5), ("P03-sage", "P03-SAGE", "ទំហំមួយ", "បៃតងស្លឹក", 3)]},
    {"id": "P04", "vendor": "V03", "title": "កម្រាលលើករូបសូត្រដៃ", "price": 48, "stock": 11, "cat": "c2a", "tags": ["embroidery", "home"], "low": 3, "blurb": "កម្រាលសូត្រលើករូបផ្កាខ្មែរ ទំហំ ១២ អ៊ីញ។"},
    {"id": "P05", "vendor": "V03", "title": "រង្វង់លើកស្លឹក ៨ អ៊ីញ", "price": 36, "stock": 7, "cat": "c2a", "tags": ["embroidery"], "low": 2, "blurb": "រង្វង់លើកស្លឹកស្ងួត រួចព្យួរបានភ្លាម។"},
    {"id": "P06", "vendor": "V04", "title": "រុំឧបករណ៍សិប្បករ", "price": 42, "stock": 86, "cat": "c2b", "tags": ["maker", "tools"], "low": 12, "blurb": "ក្រណាត់ក្រមួនរុំកាំបិត និងឧបករណ៍ឆ្លាក់។"},
    {"id": "P07", "vendor": "V04", "title": "ឆៀងសិប្បករក្រណាត់ក្រាស់", "price": 58, "cat": "c3", "tags": ["maker"], "low": 8, "blurb": "ឆៀងខ្នងឆ្លង សម្រាប់សិប្បករ។", "variants": [("P07-s", "P07-S", "S", "ក្រណាត់", 10), ("P07-m", "P07-M", "M", "ក្រណាត់", 18), ("P07-l", "P07-L", "L", "ក្រណាត់", 12)]},
    {"id": "P08", "vendor": "V04", "title": "ឧបករណ៍វាស់ស្ពាន់លឿង", "price": 34, "stock": 120, "cat": "c2b", "tags": ["tools", "maker"], "low": 20, "blurb": "ស្ពាន់លឿងរឹង សម្រាប់សិប្បកម្ម។"},
    {"id": "P09", "vendor": "V05", "title": "ក្តារកាត់ឈើទន្លេសាប", "price": 64, "stock": 9, "cat": "c2b", "tags": ["wood"], "low": 3, "blurb": "ក្តារកាត់ឈើមូលពីសិប្បកម្មកំពង់ឆ្នាំង។"},
    {"id": "P10", "vendor": "V06", "title": "ឈុតក្រណាត់ក្រាលពែង", "price": 22, "cat": "c2a", "tags": ["home"], "low": 5, "blurb": "ឈុតបួនដុំ ក្រណាត់អារម្មណ៍ស្រួលដៃ។", "variants": [("P10-nat", "P10-NAT", "ឈុត ៤", "ធម្មជាតិ", 11), ("P10-ch", "P10-CHR", "ឈុត ៤", "ខ្មៅធ្យូង", 7)]},
    {"id": "P11", "vendor": "V06", "title": "ស្រោមពែងដេរដៃ", "price": 19, "stock": 1, "cat": "c2a", "tags": ["home"], "low": 4, "blurb": "នៅសល់តែមួយ — សម្រាប់សាកល្បងការជូនដំណឹងស្តុកទាប។"},
    {"id": "P12", "vendor": "V06", "title": "ឈុតថង់ក្រណាត់ទិញបន្លែ", "price": 26, "stock": 15, "cat": "c2a", "tags": ["home", "bag"], "low": 4, "blurb": "ថង់ចងខ្សែបីទំហំ លាងម៉ាស៊ីនបាន។"},
    {"id": "P13", "vendor": "V07", "title": "កាបូបទីផ្សារថ្ងៃអាទិត្យ", "price": 32, "stock": 6, "cat": "c3a", "tags": ["bag"], "low": 2, "blurb": "កាបូបកប្បាសក្រាស់ សម្រាប់ទីផ្សារព្រឹក។"},
    {"id": "P14", "vendor": "V08", "title": "ខ្សែសោស្បែកក្របី", "price": 18, "cat": "c1b", "tags": ["leather"], "low": 8, "blurb": "ស្បែកក្របីធម្មជាតិ ខ្ទាស់ស្ពាន់លឿង។", "variants": [("P14-tan", "P14-TAN", "ទំហំមួយ", "ត្នោត", 24), ("P14-ox", "P14-OX", "ទំហំមួយ", "ក្រហមស៊ីត", 20)]},
    {"id": "P15", "vendor": "V08", "title": "គម្របសៀវភៅដេរស្បែក", "price": 39, "stock": 21, "cat": "c4", "tags": ["leather", "paper"], "low": 5, "blurb": "សម្រាប់សៀវភៅ A5 ដេរដោយដៃ។"},
    {"id": "P16", "vendor": "V09", "title": "ថូដីឥដ្ឋខ្មែរ", "price": 29, "stock": 17, "cat": "c2c", "tags": ["ceramic"], "low": 4, "blurb": "ថូដីឥដ្ឋមានចំណុច លាបពណ៌មួយៗមិនដូចគ្នា។"},
    {"id": "P17", "vendor": "V09", "title": "ពែងកាហ្វេដីឥដ្ឋ", "price": 24, "cat": "c2c", "tags": ["ceramic"], "low": 6, "blurb": "ពែង ៤ អោនស៍ លាងចានបាន។", "variants": [("P17-sp", "P17-SP", "៤ អោនស៍", "ចំណុច", 14), ("P17-ink", "P17-INK", "៤ អោនស៍", "ខ្មៅទឹកថ្នាំ", 11)]},
    {"id": "P18", "vendor": "V10", "title": "សៀវភៅសម្គាល់ទំព័រគូរទឹកពណ៌", "price": 8, "stock": 3, "cat": "c4", "tags": ["paper", "gift"], "low": 2, "blurb": "គូរដោយដៃពីហាងថ្មីៗ។"},
    {
        "id": "P19",
        "vendor": "V06",
        "title": "ឈុតកន្សែងតុក្រណាត់",
        "price": 24,
        "stock": 8,
        "cat": "c2a",
        "tags": ["home"],
        "low": 3,
        "blurb": "ផលិតផលរង់ចាំការអនុម័តពីបុគ្គលិក (maker-checker)។",
        "listing_status": "pending_review",
    },
]

REVIEWS = [
    ("R01", "ebay", 1.5, "negative", "shipping_delay", "រង់ចាំជាងមួយសប្តាហ៍មិនទាន់បានទំនិញ ស្នើសុំសងប្រាក់វិញ។", "V07", "P13", "maya"),
    ("R02", "ebay", 1.0, "negative", "no_response", "ផ្ញើសារទៅអ្នកលក់ច្រើនដងអំពីការកម្មង់មិនទាន់ដឹក — គ្មានចម្លើយ។", "V02", "P03", "theo"),
    ("R03", "etsy", None, "friction", "metric_noise", "ពិន្ទុឆ្លើយតបធ្លាក់ដោយសារសារពីអ្នកទិញដែលមិនពាក់ព័ន្ធ។", "V06", "P10", "maya"),
    ("R04", "ebay", 5, "positive", "fast_shipping", "ទំនិញមកលឿន វេចខ្ចប់យ៉ាងល្អ។", "V06", "P10", "priya"),
    ("R05", "ebay", 5, "positive", "communication", "គុណភាព វេចខ្ចប់ និងការឆ្លើយតបល្អក្នុងការកម្មង់តែមួយ។", "V09", "P16", "maya"),
    ("R06", "ebay", 5, "positive", "international_shipping", "អតិថិជនពីខេត្តផ្សេង សរសើរការដឹកលឿន និងទំនាក់ទំនងល្អ។", "V03", "P04", "maya"),
    ("R07", "ebay", 5, "positive", "care_packaging", "មានអារម្មណ៍ថាអ្នកលក់យកចិត្តទុកដាក់ វេចខ្ចប់យ៉ាងប្រុងប្រយ័ត្ន។", "V08", "P14", "theo"),
    ("R08", "ebay", 5, "positive", "value_speed", "ដឹកលឿន តម្លៃសមរម្យ។", "V01", "P01", "priya"),
    ("R09", "ebay", 5, "positive", "early_delivery", "មកមុនពេលកំណត់ វេចខ្ចប់ល្អ។", "V05", "P09", "theo"),
    ("R10", "etsy", 5, "positive", "seller_reply", "អ្នកលក់ឆ្លើយអរគុណផ្ទាល់ ទំនិញមកមុនថ្ងៃបុណ្យ។", "V06", "P12", "maya"),
]

# code, funded_by, vendor, type, value, min $, start offset days, length days, limit, used, per customer, flash, note
COUPONS = [
    ("WELCOME10", "platform", None, "percent", 10, 20, -150, 330, 500, 41, 1, False, "គូប៉ុងវេទិកា។ មិនកាត់បន្ថយទឹកប្រាក់អ្នកលក់ ឬមូលដ្ឋានកម្រៃ។"),
    ("ANNE5", "vendor", "V06", "percent", 5, 15, -140, 260, 80, 12, 2, False, "គូប៉ុងហាងក្រណាត់ផ្ទះ Jess។ កម្រៃយកលើតម្លៃបន្ទាប់ពីបញ្ចុះ។"),
    ("FLASH24", "platform", None, "percent", 20, 30, 0, 1, 100, 8, 1, True, "គូប៉ុងភ្លាមៗ ២៤ ម៉ោង។ វេទិកាទទួលបន្ទុកបញ្ចុះតម្លៃ។"),
]

# id, name, target type, target id, rate bps, min fee cents
COMMISSION_RULES = [
    ("CR-PLAT", "អត្រាវេទិកាលំនាំដើម", "platform", "*", 1500, 30),
    ("CR-START", "កម្រិតចាប់ផ្តើម", "tier", "starter", 1500, 30),
    ("CR-GROW", "កម្រិតរីកចម្រើន", "tier", "growth", 1200, 30),
    ("CR-EST", "កម្រិតរឹងមាំ", "tier", "established", 900, 50),
    ("CR-POW", "កម្រិតអ្នកលក់ធំ", "tier", "power", 600, 50),
]

# The six named orders from the prototype. lines: (product, variant or None, qty).
NAMED_ORDERS = [
    {"id": "O-1001", "buyer": "maya", "source": "organic", "days_ago": 7, "lines": [("P10", "P10-nat", 1), ("P04", None, 1)], "statuses": {"V06": "packing", "V03": "shipped"}, "tracking": {"V03": "KH-44821"}},
    {"id": "O-1002", "buyer": "maya", "source": "organic", "days_ago": 13, "lines": [("P13", None, 1)], "statuses": {"V07": "shipped"}, "tracking": {"V07": "KH-77310"}},
    {"id": "O-1003", "buyer": "maya", "source": "organic", "days_ago": 16, "lines": [("P16", None, 1)], "statuses": {"V09": "delivered"}, "tracking": {"V09": "KH-99102"}},
    {"id": "O-1004", "buyer": "theo", "source": "coupon", "coupon": "WELCOME10", "days_ago": 5, "lines": [("P07", "P07-m", 1), ("P08", None, 1)], "statuses": {"V04": "delivered"}, "tracking": {"V04": "KH-22011"}},
    {"id": "O-1005", "buyer": "priya", "source": "social", "days_ago": 3, "lines": [("P09", None, 1)], "statuses": {"V05": "shipped"}, "tracking": {"V05": "KH-1882"}},
    {"id": "O-1006", "buyer": "maya", "source": "organic", "days_ago": 1, "lines": [("P01", None, 1)], "statuses": {"V01": "accepted"}},
]

# Earnings accrued before the demo period, paid out through the seeded payouts.
OPENING_BALANCES = {"V04": 920000, "V06": 18480, "V07": 9600, "V09": 126000}

# id, vendor, amount, status, note
PAYOUTS = [
    ("PAY-04", "V04", 920000, "eligible", "បង់ប្រចាំសប្តាហ៍អ្នកលក់ធំ — ផុតពេលរក្សា"),
    ("PAY-06", "V06", 18480, "eligible", "រយៈពេលរបាយការណ៍ — ផុតពេលរក្សា"),
    ("PAY-07", "V07", 9600, "held_for_dispute", "រក្សាទុកខណៈវិវាទ D1 នៅបើក"),
    ("PAY-09", "V09", 126000, "paid", "របាយការណ៍ខែកញ្ញា"),
]
