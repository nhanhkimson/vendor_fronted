"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

export type Locale = "en" | "km" | "zh";

const STORAGE_KEY = "bazaar-locale";

const en = {
  nav: {
    shop: "Shop",
    shops: "Shops",
    reviews: "Reviews",
    sell: "Sell",
    guide: "Guide",
    search: "Search makers",
    cart: "Cart",
    signIn: "Sign in",
    signOut: "Sign out",
    about: "About",
  },
  footer: {
    tagline: "Independent shops. One checkout. Commission frozen at the moment you pay.",
  },
  home: {
    eyebrow: "A marketplace of makers",
    title: "Many shops. One checkout.",
    body: "Buy from independent makers in a single payment. Each shop ships its own parcel, and the commission was frozen when you paid.",
    shops: "shops",
    pieces: "pieces",
    customers: "customers",
    liveNow: "Live now",
    featured: "Featured",
    browseAll: "Browse all",
    shopsHeading: "Shops",
  },
  shops: {
    title: "Shops",
    pieces: "pieces",
  },
  reviews: {
    title: "Reviews",
    intro: "Published reviews only. A verified purchase is one placed on Bazaar and delivered.",
    stars: "stars",
    verified: "verified purchase",
  },
  search: {
    catalogue: "The catalogue",
    resultsFor: "Results for",
    pieces: "pieces",
  },
  about: {
    title: "About Bazaar",
    p1: "Bazaar is a two-sided market. Customers buy from many independent shops in one payment. Each shop fulfils only its own part of the order. The platform keeps a commission that is copied onto the order when it is placed, so a later rate change cannot rewrite history.",
    p2: "Sellers see only their own products, orders, coupons and payouts. Asking for someone else's record looks the same as asking for a record that does not exist.",
    note: "This marketplace is a student project. The demo password is demo.",
  },
  guide: {
    title: "How Bazaar works",
    intro: "One marketplace, three places to work. Pick the surface that matches your role.",
    surfaces: [
      ["Website", "Shop the catalogue, cart, and checkout. Guests can browse; customers pay and track."],
      ["Seller Dashboard", "Run one shop: products, prices, stock, shipping, and payout requests."],
      ["Admin Console", "Staff verify shops, approve listings, resolve disputes, and co-sign payouts."],
    ] as [string, string][],
    step: "Demo step",
    steps: [
      ["Maya shops two makers", "Add a piece from ក្រណាត់ផ្ទះ Jess and another shop, then pay with 4242 4242 4242 4242."],
      ["The order splits", "One payment becomes one sub-order per shop, each with its own tracking number."],
      ["Jess ships only her half", "Seller Dashboard shows ក្រណាត់ផ្ទះ Jess orders. សិប្បករធំខ្មែរ cannot open them."],
      ["Listing maker-checker", "Pending listings wait on /admin/listings until Admin or Support approves."],
      ["Daniel and Lin sign a payout", "Jess requests a payout. Two different staff members must sign before it is paid."],
    ] as [string, string][],
    footerBefore: "Sign in from the",
    loginPage: "login page",
    footerAfter: ". The password for every demo account is",
    apiRef: "API reference is at",
  },
  orientation: {
    title: "Where you are",
    website: "Public website for shopping",
    seller: "Seller Dashboard — your shop only",
    admin: "Admin Console — platform operations",
    account: "Your customer account",
    learnMore: "How Bazaar works",
  },
  sell: {
    title: "Sell on Bazaar",
    intro: "A customer account can open a shop. Documents can be added after the draft is created.",
    signInFirst: "Sign in as a customer first.",
    shopName: "Shop name",
    city: "City",
    headline: "Headline",
    about: "About the shop",
    open: "Open a shop",
    staffNote: "Staff can also review an existing application, such as សិល្បៈក្រដាសថ្មី, from the admin vendors screen.",
    success: "Shop opened. Upload documents in Seller Central.",
    failed: "Application failed",
  },
  login: {
    eyebrow: "Bazaar access",
    title: "Sign in",
    intro: "Pick a role first. You will see what that person can do, then choose a demo account and continue.",
    demoTitle: "Quick demo sign-in",
    demoIntro: "These cards match the role you picked. Password for every demo account is demo.",
    chooseRole: "I want to sign in as",
    chooseAccount: "Demo person",
    noAccounts: "No demo people for this role",
    canDo: "What this role can do",
    landsAt: "Opens",
    passwordHint: "Password: {password}",
    signInAs: "Sign in as {name}",
    signIn: "Sign in",
    continue: "Continue",
    email: "Email",
    password: "Password",
    manualTitle: "Or type email and password",
    manualIntro: "Use this if you already know the demo email. Password is still demo.",
    failed: "That email and password do not match. Every demo account uses the password demo.",
    newHere: "New here?",
    createAccount: "Create a customer account",
    roles: {
      customer: {
        label: "Customer",
        summary: "Shop across many makers in one checkout.",
        home: "Your account",
        capabilities: [
          "Browse shops, search products, and read reviews",
          "Keep a cart, apply coupons, and pay once for many shops",
          "Track each shop’s parcel, confirm delivery, leave reviews",
          "Open a dispute, message sellers, manage wishlist and settings",
        ],
      },
      vendor: {
        label: "Seller",
        summary: "Run one shop only. Other shops stay invisible.",
        home: "Seller Dashboard",
        capabilities: [
          "Create products, set prices, and submit listings for review",
          "Fulfil and ship only this shop’s part of an order",
          "Run shop promotions and reply to reviews",
          "View earnings and request payouts (cannot approve them)",
        ],
      },
      admin: {
        label: "Admin",
        summary: "Day-to-day platform operations.",
        home: "Admin Console",
        capabilities: [
          "Verify seller applications and review documents",
          "Approve or reject product listings (maker-checker)",
          "Manage categories, platform coupons, and commission rules",
          "Oversee orders, customers, disputes, and one payout signature",
        ],
      },
      support: {
        label: "Support",
        summary: "Help customers and sellers without full admin power.",
        home: "Admin Console",
        capabilities: [
          "Approve or reject product listings waiting for review",
          "Search the activity log and moderate reviews",
          "Help with disputes and open-order questions",
          "Provide the second payout signature with another staff member",
        ],
      },
      super_admin: {
        label: "Super Admin",
        summary: "Full platform control and access governance.",
        home: "Admin Console",
        capabilities: [
          "Edit the permission matrix and assign roles",
          "Archive or oversee the activity log",
          "Change commission policy and staff access",
          "Sign payouts and unlock every admin screen",
        ],
      },
    },
  },
  register: {
    title: "Create an account",
    name: "Name",
    email: "Email",
    password: "Password",
    city: "City",
    submit: "Register",
    failed: "Could not create the account",
  },
  cart: {
    title: "Cart",
    empty: "Your cart is empty.",
    qty: "qty",
    remove: "Remove",
    signInToCheckout: "Sign in to check out",
    coupon: "Coupon code",
    apply: "Apply",
    checkout: "Checkout",
    subtotal: "Subtotal",
    discount: "Discount",
    total: "Total",
    refresh: "Refresh prices",
    couponFailed: "Coupon was not applied",
  },
  checkout: {
    title: "Checkout",
    empty: "Your cart is empty.",
    name: "Name",
    address: "Address",
    card: "Card",
    cardHint: "4242 4242 4242 4242 is approved. 4000 0000 0000 0002 is declined and releases the stock.",
    paying: "Paying…",
    pay: "Pay and place the order",
    failed: "Checkout failed",
    signInFirst: "to check out.",
    customersOnly: "Checkout is for customer accounts.",
    placed: "is placed",
  },
  product: {
    addToCart: "Add to cart",
    available: "available",
    soldOut: "Sold out",
    left: "left",
    added: "Added to your cart",
    guestSaved: "Saved in your guest cart",
    addFailed: "Could not add that item",
    customerOnly: "Sign in as a customer to shop",
  },
  lang: {
    label: "Language",
    en: "English",
    km: "ខ្មែរ",
    zh: "中文",
  },
};

type DeepStringify<T> = {
  [K in keyof T]: T[K] extends string
    ? string
    : T[K] extends readonly (infer U)[]
      ? DeepStringify<U>[]
      : T[K] extends object
        ? DeepStringify<T[K]>
        : T[K];
};

type Dictionary = DeepStringify<typeof en>;

const km: Dictionary = {
  nav: {
    shop: "ទិញ",
    shops: "ហាង",
    reviews: "មតិ",
    sell: "លក់",
    guide: "ណែនាំ",
    search: "ស្វែងរកសិប្បករ",
    cart: "កន្ត្រក",
    signIn: "ចូល",
    signOut: "ចេញ",
    about: "អំពី",
  },
  footer: {
    tagline: "ហាងឯករាជ្យ។ ទូទាត់មួយដង។ កម្រៃជើងសារាត្រូវបានបង្កកនៅពេលអ្នកបង់។",
  },
  home: {
    eyebrow: "ផ្សារទំនិញពីសិប្បករ",
    title: "ហាងច្រើន។ ទូទាត់មួយដង។",
    body: "ទិញពីសិប្បករឯករាជ្យក្នុងការទូទាត់តែមួយ។ ហាងនីមួយៗដឹកជញ្ជូនកញ្ចប់របស់ខ្លួន ហើយកម្រៃជើងសារត្រូវបានបង្កកនៅពេលអ្នកបង់។",
    shops: "ហាង",
    pieces: "មុខទំនិញ",
    customers: "អតិថិជន",
    liveNow: "កំពុងដំណើរការ",
    featured: "ពិសេស",
    browseAll: "មើលទាំងអស់",
    shopsHeading: "ហាង",
  },
  shops: {
    title: "ហាង",
    pieces: "មុខទំនិញ",
  },
  reviews: {
    title: "មតិ",
    intro: "មានតែមតិដែលបានផ្សាយ។ ការទិញដែលបានផ្ទៀងផ្ទាត់គឺជាការបញ្ជាទិញនៅលើ Bazaar ហើយបានដឹកជញ្ជូន។",
    stars: "ផ្កាយ",
    verified: "ការទិញដែលបានផ្ទៀងផ្ទាត់",
  },
  search: {
    catalogue: "កាតាឡុក",
    resultsFor: "លទ្ធផលសម្រាប់",
    pieces: "មុខទំនិញ",
  },
  about: {
    title: "អំពី Bazaar",
    p1: "Bazaar គឺជាទីផ្សារពីរភាគី។ អតិថិជនទិញពីហាងឯករាជ្យច្រើនក្នុងការទូទាត់តែមួយ។ ហាងនីមួយៗបំពេញតែផ្នែករបស់ខ្លួននៃការបញ្ជាទិញ។ វេទិការក្សាកម្រៃជើងសារដែលត្រូវបានចម្លងទៅលើការបញ្ជាទិញនៅពេលដាក់ ដូច្នេះការផ្លាស់ប្តូរអត្រាក្រោយមិនអាចកែប្រវត្តិបានទេ។",
    p2: "អ្នកលក់ឃើញតែផលិតផល ការបញ្ជាទិញ ប័ណ្ណ និងការទូទាត់របស់ខ្លួន។ ការស្នើសុំកំណត់ត្រារបស់អ្នកផ្សេងទៀតមើលទៅដូចគ្នានឹងការស្នើសុំកំណត់ត្រាដែលមិនមាន។",
    note: "ផ្សារនេះជាការងារសិក្សា។ ពាក្យសម្ងាត់សាកល្បងគឺ demo។",
  },
  guide: {
    title: "របៀបដែល Bazaar ដំណើរការ",
    intro: "ទីផ្សារមួយ មានកន្លែងធ្វើការបី។ ជ្រើសតាមតួនាទីរបស់អ្នក។",
    surfaces: [
      ["គេហទំព័រ", "មើលកាតាឡុក កន្ត្រក និងបង់ប្រាក់។"],
      ["Seller Dashboard", "គ្រប់គ្រងហាងមួយ៖ ផលិតផល តម្លៃ ស្តុក និងស្នើទូទាត់។"],
      ["Admin Console", "បុគ្គលិកផ្ទៀងផ្ទាត់ហាង អនុម័តផលិតផល និងចុះហត្ថលេខាទូទាត់។"],
    ],
    step: "ជំហានសាកល្បង",
    steps: [
      ["Maya ទិញពីសិប្បករពីរនាក់", "បន្ថែមទំនិញពី ក្រណាត់ផ្ទះ Jess និងហាងផ្សេងទៀត បន្ទាប់មកបង់ដោយ 4242 4242 4242 4242។"],
      ["ការបញ្ជាទិញបំបែក", "ការទូទាត់មួយក្លាយជាអនុការបញ្ជាទិញមួយក្នុងមួយហាង។"],
      ["Jess ដឹកតែផ្នែករបស់នាង", "Seller Dashboard បង្ហាញតែការបញ្ជាទិញ ក្រណាត់ផ្ទះ Jess។"],
      ["Listing maker-checker", "ផលិតផលរង់ចាំនៅ /admin/listings រហូត Admin ឬ Support អនុម័ត។"],
      ["Daniel និង Lin ចុះហត្ថលេខាលើការទូទាត់", "Jess ស្នើទូទាត់។ បុគ្គលិកពីរនាក់ផ្សេងគ្នាត្រូវចុះហត្ថលេខា។"],
    ],
    footerBefore: "ចូលពី",
    loginPage: "ទំព័រចូល",
    footerAfter: "។ ពាក្យសម្ងាត់សម្រាប់គណនីសាកល្បងទាំងអស់គឺ",
    apiRef: "ឯកសារ API នៅ",
  },
  orientation: {
    title: "អ្នកនៅទីនេះ",
    website: "គេហទំព័រសម្រាប់ទិញ",
    seller: "Seller Dashboard — តែហាងរបស់អ្នក",
    admin: "Admin Console — ប្រតិបត្តិការវេទិកា",
    account: "គណនីអតិថិជនរបស់អ្នក",
    learnMore: "របៀបដែល Bazaar ដំណើរការ",
  },
  sell: {
    title: "លក់នៅលើ Bazaar",
    intro: "គណនីអតិថិជនអាចបើកហាង។ ឯកសារអាចបន្ថែមបន្ទាប់ពីបង្កើតសេចក្តីព្រាង។",
    signInFirst: "សូមចូលជាអតិថិជនជាមុនសិន។",
    shopName: "ឈ្មោះហាង",
    city: "ទីក្រុង",
    headline: "ចំណងជើង",
    about: "អំពីហាង",
    open: "បើកហាង",
    staffNote: "បុគ្គលិកក៏អាចពិនិត្យពាក្យសុំដែលមានរួច ដូចជា សិល្បៈក្រដាសថ្មី ពីអេក្រង់អ្នកលក់របស់អ្នកគ្រប់គ្រង។",
    success: "ហាងបានបើក។ បង្ហោះឯកសារនៅ Seller Central។",
    failed: "ពាក្យសុំបរាជ័យ",
  },
  login: {
    eyebrow: "ការចូល Bazaar",
    title: "ចូល",
    intro: "ជ្រើសតួនាទីសិន។ អ្នកនឹងឃើញអ្វីដែលតួនាទីនោះអាចធ្វើ បន្ទាប់មកជ្រើសគណនីសាកល្បង។",
    demoTitle: "ចូលសាកល្បងរហ័ស",
    demoIntro: "កាតទាំងនេះត្រូវនឹងតួនាទីដែលអ្នកជ្រើស។ ពាក្យសម្ងាត់គណនីសាកល្បងទាំងអស់គឺ demo។",
    chooseRole: "ខ្ញុំចង់ចូលជា",
    chooseAccount: "មនុស្សសាកល្បង",
    noAccounts: "មិនមានមនុស្សសាកល្បងសម្រាប់តួនាទីនេះ",
    canDo: "អ្វីដែលតួនាទីនេះអាចធ្វើ",
    landsAt: "បើកទៅ",
    passwordHint: "ពាក្យសម្ងាត់: {password}",
    signInAs: "ចូលជា {name}",
    signIn: "ចូល",
    continue: "បន្ត",
    email: "អ៊ីមែល",
    password: "ពាក្យសម្ងាត់",
    manualTitle: "ឬវាយអ៊ីមែល និងពាក្យសម្ងាត់",
    manualIntro: "ប្រើបើអ្នកដឹងអ៊ីមែលសាកល្បងរួច។ ពាក្យសម្ងាត់នៅតែ demo។",
    failed: "អ៊ីមែល និងពាក្យសម្ងាត់មិនត្រូវគ្នា។ គណនីសាកល្បងទាំងអស់ប្រើពាក្យសម្ងាត់ demo។",
    newHere: "ថ្មីនៅទីនេះ?",
    createAccount: "បង្កើតគណនីអតិថិជន",
    roles: {
      customer: {
        label: "អតិថិជន",
        summary: "ទិញពីហាងច្រើនក្នុងការទូទាត់មួយ។",
        home: "គណនីរបស់អ្នក",
        capabilities: [
          "រកមើលហាង ផលិតផល និងមតិ",
          "រក្សាកន្ត្រក ដាក់គូប៉ុង និងបង់ប្រាក់ម្តង",
          "តាមដានកញ្ចប់ បញ្ជាក់ការដឹក ទុកមតិ",
          "បើកវិវាទ សារ ចង់បាន និងការកំណត់",
        ],
      },
      vendor: {
        label: "អ្នកលក់",
        summary: "គ្រប់គ្រងតែហាងផ្ទាល់ខ្លួន។",
        home: "Seller Dashboard",
        capabilities: [
          "បង្កើតផលិតផល កំណត់តម្លៃ និងដាក់ស្នើសម្រាប់ពិនិត្យ",
          "ដឹកជញ្ជូនតែផ្នែកនៃការបញ្ជាទិញរបស់ហាងនេះ",
          "បង្កើតប្រូម៉ូសិន និងឆ្លើយមតិ",
          "មើលចំណូល និងស្នើសុំការទូទាត់ (មិនអាចអនុម័ត)",
        ],
      },
      admin: {
        label: "អ្នកគ្រប់គ្រង",
        summary: "ប្រតិបត្តិការវេទិកាប្រចាំថ្ងៃ។",
        home: "Admin Console",
        capabilities: [
          "ផ្ទៀងផ្ទាត់ពាក្យសុំអ្នកលក់",
          "អនុម័ត ឬបដិសេធផលិតផលដែលរង់ចាំ",
          "គ្រប់គ្រងប្រភេទ គូប៉ុង និងកម្រៃ",
          "មើលការបញ្ជាទិញ វិវាទ និងចុះហត្ថលេខាទូទាត់មួយ",
        ],
      },
      support: {
        label: "ជំនួយ",
        summary: "ជួយអតិថិជន និងអ្នកលក់។",
        home: "Admin Console",
        capabilities: [
          "អនុម័ត ឬបដិសេធផលិតផលដែលរង់ចាំ",
          "ស្វែងរកកំណត់ហេតុសកម្មភាព និងត្រួតពិនិត្យមតិ",
          "ជួយវិវាទ និងសំណួរការបញ្ជាទិញ",
          "ចុះហត្ថលេខាទូទាត់ទីពីរ",
        ],
      },
      super_admin: {
        label: "អ្នកគ្រប់គ្រងជាន់ខ្ពស់",
        summary: "ការគ្រប់គ្រងពេញលេញនៃវេទិកា។",
        home: "Admin Console",
        capabilities: [
          "កែម៉ាទ្រីសសិទ្ធិ និងផ្តល់តួនាទី",
          "គ្រប់គ្រងកំណត់ហេតុសកម្មភាព",
          "ផ្លាស់ប្តូរគោលការណ៍កម្រៃ និងសិទ្ធិបុគ្គលិក",
          "ចុះហត្ថលេខាទូទាត់ និងបើកគ្រប់អេក្រង់ admin",
        ],
      },
    },
  },
  register: {
    title: "បង្កើតគណនី",
    name: "ឈ្មោះ",
    email: "អ៊ីមែល",
    password: "ពាក្យសម្ងាត់",
    city: "ទីក្រុង",
    submit: "ចុះឈ្មោះ",
    failed: "មិនអាចបង្កើតគណនីបានទេ",
  },
  cart: {
    title: "កន្ត្រក",
    empty: "កន្ត្រករបស់អ្នកទទេ។",
    qty: "ចំនួន",
    remove: "លុប",
    signInToCheckout: "ចូលដើម្បីទូទាត់",
    coupon: "លេខកូដប័ណ្ណ",
    apply: "អនុវត្ត",
    checkout: "ទូទាត់",
    subtotal: "សរុបរង",
    discount: "បញ្ចុះតម្លៃ",
    total: "សរុប",
    refresh: "ផ្ទុកតម្លៃឡើងវិញ",
    couponFailed: "ប័ណ្ណមិនត្រូវបានអនុវត្ត",
  },
  checkout: {
    title: "ទូទាត់",
    empty: "កន្ត្រករបស់អ្នកទទេ។",
    name: "ឈ្មោះ",
    address: "អាសយដ្ឋាន",
    card: "កាត",
    cardHint: "4242 4242 4242 4242 ត្រូវបានអនុម័ត។ 4000 0000 0000 0002 ត្រូវបានបដិសេធ និងដោះលែងស្តុក។",
    paying: "កំពុងបង់…",
    pay: "បង់ និងដាក់ការបញ្ជាទិញ",
    failed: "ការទូទាត់បរាជ័យ",
    signInFirst: "ដើម្បីទូទាត់។",
    customersOnly: "ការទូទាត់សម្រាប់គណនីអតិថិជន។",
    placed: "បានដាក់",
  },
  product: {
    addToCart: "បន្ថែមទៅកន្ត្រក",
    available: "មានស្តុក",
    soldOut: "អស់ស្តុក",
    left: "នៅសល់",
    added: "បានបន្ថែមទៅកន្ត្រក",
    guestSaved: "បានរក្សាទុកក្នុងកន្ត្រកភ្ញៀវ",
    addFailed: "មិនអាចបន្ថែមទំនិញនោះបានទេ",
    customerOnly: "ចូលជាអតិថិជនដើម្បីទិញ",
  },
  lang: {
    label: "ភាសា",
    en: "English",
    km: "ខ្មែរ",
    zh: "中文",
  },
};

const zh: Dictionary = {
  nav: {
    shop: "选购",
    shops: "店铺",
    reviews: "评价",
    sell: "开店",
    guide: "指南",
    search: "搜索匠人",
    cart: "购物车",
    signIn: "登录",
    signOut: "退出",
    about: "关于",
  },
  footer: {
    tagline: "独立店铺，一次结账。佣金在付款时锁定。",
  },
  home: {
    eyebrow: "匠人市集",
    title: "多家店铺，一次结账。",
    body: "一次付款即可从多家独立匠人购买。每家店铺单独发货，佣金在您付款时已锁定。",
    shops: "店铺",
    pieces: "件商品",
    customers: "顾客",
    liveNow: "进行中",
    featured: "精选",
    browseAll: "浏览全部",
    shopsHeading: "店铺",
  },
  shops: {
    title: "店铺",
    pieces: "件商品",
  },
  reviews: {
    title: "评价",
    intro: "仅显示已发布评价。已验证购买指在 Bazaar 下单并已送达的订单。",
    stars: "星",
    verified: "已验证购买",
  },
  search: {
    catalogue: "商品目录",
    resultsFor: "搜索结果",
    pieces: "件商品",
  },
  about: {
    title: "关于 Bazaar",
    p1: "Bazaar 是一个双边市场。顾客一次付款即可从多家独立店铺购买。每家店铺只履约自己的订单部分。平台在下单时将佣金写入订单，之后的费率变更无法改写历史。",
    p2: "卖家只能看到自己的商品、订单、优惠券和结算。查询他人记录与查询不存在的记录看起来一样。",
    note: "本市集为学习项目。演示密码为 demo。",
  },
  guide: {
    title: "Bazaar 如何运作",
    intro: "一个市场，三处工作台。按角色选择入口。",
    surfaces: [
      ["网站", "浏览目录、购物车与结账。"],
      ["卖家工作台", "管理一家店：商品、价格、库存与提现申请。"],
      ["管理后台", "审核店铺与上架、处理纠纷、会签提现。"],
    ],
    step: "演示步骤",
    steps: [
      ["Maya 选购两家匠人", "从 ក្រណាត់ផ្ទះ Jess 和另一家店各加一件，然后用 4242 4242 4242 4242 付款。"],
      ["订单拆分", "一次付款变成每店一个子订单，各自有追踪号。"],
      ["Jess 只发自己那一半", "卖家工作台只显示 ក្រណាត់ផ្ទះ Jess 的订单。"],
      ["上架双人审核", "待审商品在 /admin/listings，需管理员或客服批准。"],
      ["Daniel 与 Lin 签署结算", "Jess 申请提现，须两名不同员工签署后才能支付。"],
    ],
    footerBefore: "从",
    loginPage: "登录页",
    footerAfter: "登录。每个演示账号的密码都是",
    apiRef: "API 文档见",
  },
  orientation: {
    title: "你在这里",
    website: "面向购物的公开网站",
    seller: "卖家工作台 — 仅本店",
    admin: "管理后台 — 平台运营",
    account: "你的顾客账户",
    learnMore: "Bazaar 如何运作",
  },
  sell: {
    title: "在 Bazaar 开店",
    intro: "顾客账号可以开店。草稿创建后可再上传文件。",
    signInFirst: "请先以顾客身份登录。",
    shopName: "店铺名称",
    city: "城市",
    headline: "标语",
    about: "店铺简介",
    open: "开设店铺",
    staffNote: "员工也可在管理端的卖家页面审核已有申请，例如 សិល្បៈក្រដាសថ្មី。",
    success: "店铺已开设。请在卖家中心上传文件。",
    failed: "申请失败",
  },
  login: {
    eyebrow: "Bazaar 登录",
    title: "登录",
    intro: "先选择角色，查看该角色能做什么，再选择演示账号继续。",
    demoTitle: "快速演示登录",
    demoIntro: "这些卡片对应当前角色。所有演示账号密码都是 demo。",
    chooseRole: "我要以什么身份登录",
    chooseAccount: "演示人物",
    noAccounts: "此角色暂无演示人物",
    canDo: "该角色可以做什么",
    landsAt: "进入",
    passwordHint: "密码：{password}",
    signInAs: "以 {name} 登录",
    signIn: "登录",
    continue: "继续",
    email: "邮箱",
    password: "密码",
    manualTitle: "或手动输入邮箱和密码",
    manualIntro: "如果你已知道演示邮箱，可用这里。密码仍是 demo。",
    failed: "邮箱或密码不匹配。所有演示账号的密码都是 demo。",
    newHere: "新用户？",
    createAccount: "创建顾客账号",
    roles: {
      customer: {
        label: "顾客",
        summary: "一次结账购买多家独立店铺。",
        home: "我的账户",
        capabilities: [
          "浏览店铺、搜索商品并阅读评价",
          "购物车、优惠券，一笔支付多家店",
          "分别跟踪包裹、确认收货、发表评价",
          "发起纠纷、联系卖家、管理心愿单与设置",
        ],
      },
      vendor: {
        label: "卖家",
        summary: "只管理自己的店铺，看不到其他卖家。",
        home: "卖家工作台",
        capabilities: [
          "创建商品、设置价格并提交审核",
          "只履约并配送本店子订单",
          "店铺促销并回复评价",
          "查看收益并申请提现（不能审批）",
        ],
      },
      admin: {
        label: "管理员",
        summary: "平台日常运营。",
        home: "管理后台",
        capabilities: [
          "审核卖家申请与资料",
          "批准或拒绝待审商品上架",
          "管理分类、平台优惠券与佣金规则",
          "处理订单、纠纷并提供一次提现签名",
        ],
      },
      support: {
        label: "客服支持",
        summary: "协助顾客与卖家，权限低于管理员。",
        home: "管理后台",
        capabilities: [
          "批准或拒绝待审商品上架",
          "搜索活动日志并审核评价",
          "协助纠纷与未完成订单问题",
          "与另一位员工一起完成第二次提现签名",
        ],
      },
      super_admin: {
        label: "超级管理员",
        summary: "完整平台控制与权限治理。",
        home: "管理后台",
        capabilities: [
          "编辑权限矩阵并分配角色",
          "管理活动日志",
          "调整佣金政策与员工访问",
          "签署提现并打开全部管理页面",
        ],
      },
    },
  },
  register: {
    title: "创建账号",
    name: "姓名",
    email: "邮箱",
    password: "密码",
    city: "城市",
    submit: "注册",
    failed: "无法创建账号",
  },
  cart: {
    title: "购物车",
    empty: "购物车是空的。",
    qty: "数量",
    remove: "移除",
    signInToCheckout: "登录后结账",
    coupon: "优惠码",
    apply: "应用",
    checkout: "结账",
    subtotal: "小计",
    discount: "折扣",
    total: "合计",
    refresh: "刷新价格",
    couponFailed: "优惠码未生效",
  },
  checkout: {
    title: "结账",
    empty: "购物车是空的。",
    name: "姓名",
    address: "地址",
    card: "银行卡",
    cardHint: "4242 4242 4242 4242 会通过。4000 0000 0000 0002 会拒付并释放库存。",
    paying: "支付中…",
    pay: "支付并下单",
    failed: "结账失败",
    signInFirst: "后结账。",
    customersOnly: "结账仅限顾客账号。",
    placed: "已下单",
  },
  product: {
    addToCart: "加入购物车",
    available: "有货",
    soldOut: "售罄",
    left: "件剩余",
    added: "已加入购物车",
    guestSaved: "已保存到访客购物车",
    addFailed: "无法添加该商品",
    customerOnly: "请以顾客身份登录后再购买",
  },
  lang: {
    label: "语言",
    en: "English",
    km: "ខ្មែរ",
    zh: "中文",
  },
};

export const dictionaries: Record<Locale, Dictionary> = { en, km, zh };

export const locales: { code: Locale; label: string }[] = [
  { code: "en", label: "EN" },
  { code: "km", label: "ខ្មែរ" },
  { code: "zh", label: "中文" },
];

type I18nValue = {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: Dictionary;
};

const I18nContext = createContext<I18nValue>({
  locale: "en",
  setLocale: () => {},
  t: dictionaries.en,
});

function readStoredLocale(): Locale {
  if (typeof window === "undefined") return "en";
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (raw === "en" || raw === "km" || raw === "zh") return raw;
  return "en";
}

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("en");
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setLocaleState(readStoredLocale());
    setReady(true);
  }, []);

  const setLocale = useCallback((next: Locale) => {
    setLocaleState(next);
    window.localStorage.setItem(STORAGE_KEY, next);
  }, []);

  useEffect(() => {
    if (!ready) return;
    const root = document.documentElement;
    root.lang = locale === "zh" ? "zh-CN" : locale;
    root.dataset.locale = locale;
  }, [locale, ready]);

  const value = useMemo<I18nValue>(
    () => ({ locale, setLocale, t: dictionaries[locale] }),
    [locale, setLocale],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  return useContext(I18nContext);
}

export function LanguageSwitcher() {
  const { locale, setLocale, t } = useI18n();
  return (
    <div className="flex items-center gap-1" role="group" aria-label={t.lang.label}>
      {locales.map((item) => (
        <button
          key={item.code}
          type="button"
          onClick={() => setLocale(item.code)}
          className={`rounded-full px-2.5 py-1.5 text-xs ${
            locale === item.code
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:bg-muted"
          } ${item.code === "km" ? "kh" : item.code === "zh" ? "zh" : ""}`}
          aria-pressed={locale === item.code}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}
