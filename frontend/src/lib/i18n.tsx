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
    title: "Demo guide",
    step: "Step",
    steps: [
      ["Maya shops two makers", "Add a piece from AnnesCraftworks and another shop, then pay with 4242 4242 4242 4242."],
      ["The order splits", "One payment becomes one sub-order per shop, each with its own tracking number."],
      ["Jess ships only her half", "Seller Central shows AnnesCraftworks orders. KeinMaker cannot open them."],
      ["Ava changes a rate", "Revising a commission rule closes the old version. Orders already placed keep the old fee."],
      ["Daniel and Lin sign a payout", "Jess can request PAY-06. She cannot approve it. Two different staff members must sign."],
    ] as [string, string][],
    footerBefore: "Sign in from the",
    loginPage: "login page",
    footerAfter: ". The password for every demo account is",
    apiRef: "API reference is at",
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
    staffNote: "Staff can also review an existing application, such as SimplyCreativeJess, from the admin vendors screen.",
    success: "Shop opened. Upload documents in Seller Central.",
    failed: "Application failed",
  },
  login: {
    title: "Sign in",
    demoTitle: "Demo accounts",
    demoIntro: "Password for every account is demo. Click a card to sign in.",
    signIn: "Sign in",
    continue: "Continue",
    failed: "That email and password do not match. Every demo account uses the password demo.",
    newHere: "New here?",
    createAccount: "Create a customer account",
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
    title: "ណែនាំសាកល្បង",
    step: "ជំហាន",
    steps: [
      ["Maya ទិញពីសិប្បករពីរនាក់", "បន្ថែមទំនិញពី AnnesCraftworks និងហាងផ្សេងទៀត បន្ទាប់មកបង់ដោយ 4242 4242 4242 4242។"],
      ["ការបញ្ជាទិញបំបែក", "ការទូទាត់មួយក្លាយជាអនុការបញ្ជាទិញមួយក្នុងមួយហាង ដែលមានលេខតាមដានផ្ទាល់ខ្លួន។"],
      ["Jess ដឹកតែផ្នែករបស់នាង", "Seller Central បង្ហាញការបញ្ជាទិញ AnnesCraftworks។ KeinMaker មិនអាចបើកបានទេ។"],
      ["Ava ផ្លាស់ប្តូរអត្រា", "ការកែច្បាប់កម្រៃជើងសារបិទកំណែចាស់។ ការបញ្ជាទិញដែលបានដាក់រក្សាថ្លៃចាស់។"],
      ["Daniel និង Lin ចុះហត្ថលេខាលើការទូទាត់", "Jess អាចស្នើ PAY-06។ នាងមិនអាចអនុម័តបានទេ។ បុគ្គលិកពីរនាក់ផ្សេងគ្នាត្រូវចុះហត្ថលេខា។"],
    ],
    footerBefore: "ចូលពី",
    loginPage: "ទំព័រចូល",
    footerAfter: "។ ពាក្យសម្ងាត់សម្រាប់គណនីសាកល្បងទាំងអស់គឺ",
    apiRef: "ឯកសារ API នៅ",
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
    staffNote: "បុគ្គលិកក៏អាចពិនិត្យពាក្យសុំដែលមានរួច ដូចជា SimplyCreativeJess ពីអេក្រង់អ្នកលក់របស់អ្នកគ្រប់គ្រង។",
    success: "ហាងបានបើក។ បង្ហោះឯកសារនៅ Seller Central។",
    failed: "ពាក្យសុំបរាជ័យ",
  },
  login: {
    title: "ចូល",
    demoTitle: "គណនីសាកល្បង",
    demoIntro: "ពាក្យសម្ងាត់សម្រាប់គណនីទាំងអស់គឺ demo។ ចុចកាតដើម្បីចូល។",
    signIn: "ចូល",
    continue: "បន្ត",
    failed: "អ៊ីមែល និងពាក្យសម្ងាត់មិនត្រូវគ្នា។ គណនីសាកល្បងទាំងអស់ប្រើពាក្យសម្ងាត់ demo។",
    newHere: "ថ្មីនៅទីនេះ?",
    createAccount: "បង្កើតគណនីអតិថិជន",
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
    title: "演示指南",
    step: "步骤",
    steps: [
      ["Maya 选购两家匠人", "从 AnnesCraftworks 和另一家店各加一件，然后用 4242 4242 4242 4242 付款。"],
      ["订单拆分", "一次付款变成每店一个子订单，各自有追踪号。"],
      ["Jess 只发自己那一半", "卖家中心只显示 AnnesCraftworks 的订单。KeinMaker 打不开。"],
      ["Ava 修改费率", "修改佣金规则会关闭旧版本。已下的订单保留旧费率。"],
      ["Daniel 与 Lin 签署结算", "Jess 可以申请 PAY-06，但不能批准。必须由两名不同员工签署。"],
    ],
    footerBefore: "从",
    loginPage: "登录页",
    footerAfter: "登录。每个演示账号的密码都是",
    apiRef: "API 文档见",
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
    staffNote: "员工也可在管理端的卖家页面审核已有申请，例如 SimplyCreativeJess。",
    success: "店铺已开设。请在卖家中心上传文件。",
    failed: "申请失败",
  },
  login: {
    title: "登录",
    demoTitle: "演示账号",
    demoIntro: "所有账号密码均为 demo。点击卡片即可登录。",
    signIn: "登录",
    continue: "继续",
    failed: "邮箱或密码不匹配。所有演示账号的密码都是 demo。",
    newHere: "新用户？",
    createAccount: "创建顾客账号",
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
            locale === item.code ? "bg-[#24362c] text-[#f6efe3]" : "text-[#6b6258] hover:bg-white"
          } ${item.code === "km" ? "kh" : item.code === "zh" ? "zh" : ""}`}
          aria-pressed={locale === item.code}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}
