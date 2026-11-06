const SHOP_IDS: Record<string, string> = {
  V01: "Phnom Penh Woodcarving",
  V02: "Little Clay Flowers",
  V03: "Hand Silk",
  V04: "Khmer Maker Co.",
  V05: "Tonle Sap Wood",
  V06: "Jess Home Textiles",
  V07: "Sunday Market",
  V08: "Siem Reap Leather",
  V09: "Khmer Clay",
  V10: "New Paper Studio",
};

const SHOPS: Record<string, string> = {
  "chheur-chlak-phnom-penh": "Phnom Penh Woodcarving",
  "phka-dei-doch": "Little Clay Flowers",
  "sout-loek-dai": "Hand Silk",
  "sibakar-thom-khmer": "Khmer Maker Co.",
  "chheur-tonle-sap": "Tonle Sap Wood",
  "kror-nat-phteah-jess": "Jess Home Textiles",
  "tipsa-thngai-atit": "Sunday Market",
  "sbaek-krabei-siem-reap": "Siem Reap Leather",
  "dei-doch-khmer": "Khmer Clay",
  "selapak-kradas-thmei": "New Paper Studio",
};

const PRODUCTS: Record<string, string> = {
  P01: "Custom carved name plaque",
  P02: "Wooden monogram tag",
  P03: "Romduol flower hair clip",
  P04: "Hand-embroidered silk cushion",
  P05: "Dried-leaf embroidery hoop",
  P06: "Maker tool roll",
  P07: "Heavy canvas apron",
  P08: "Brass measuring tools",
  P09: "Tonle Sap cutting board",
  P10: "Linen coaster set",
  P11: "Hand-sewn mug cozy",
  P12: "Market tote set",
  P13: "Sunday market bag",
  P14: "Buffalo leather key strap",
  P15: "Leather A5 journal cover",
  P16: "Khmer clay vase",
  P17: "Clay coffee cup",
  P18: "Watercolor page markers",
  P19: "Linen napkin set",
};

const PRODUCT_BLURBS: Record<string, string> = {
  P01: "Carved to order in a few days, packed in a gift box.",
  P02: "Wooden bag tag with two letters, made in Phnom Penh.",
  P03: "Small-batch clay hair clip in a romduol flower shape.",
  P04: "Silk cushion with Khmer floral embroidery, 12 inch.",
  P05: "Dried-leaf hoop, ready to hang.",
  P06: "Waxed canvas roll for knives and carving tools.",
  P07: "Cross-back apron for makers.",
  P08: "Solid brass measuring tools for the workshop.",
  P09: "Round cutting board from Kampong Chhnang woodwork.",
  P10: "Set of four linen coasters, soft in the hand.",
  P11: "Hand-sewn mug cozy. Last one in this batch.",
  P12: "Three string-tie totes in mixed sizes. Machine washable.",
  P13: "Heavy cotton bag for the morning market.",
  P14: "Natural buffalo leather with a brass clip.",
  P15: "Hand-stitched cover for an A5 notebook.",
  P16: "Speckled clay vase. Each one is glazed a little differently.",
  P17: "4 oz clay cup. Dishwasher safe.",
  P18: "Hand-painted page markers from a new shop.",
  P19: "Linen napkin set for the table.",
};

const CATEGORIES: Record<string, string> = {
  jewelry: "Jewelry",
  "hair-accessories": "Hair",
  "leather-goods": "Leather",
  home: "Home goods",
  textiles: "Textiles",
  "wood-kitchen": "Kitchen",
  ceramics: "Ceramics",
  wearables: "Clothing",
  bags: "Bags",
  stationery: "Stationery",
  "custom-gifts": "Gifts",
};

const CITIES: Record<string, string> = {
  ភ្នំពេញ: "Phnom Penh",
  សៀមរាប: "Siem Reap",
  កំពត: "Kampot",
  កំពង់ឆ្នាំង: "Kampong Chhnang",
  បាត់ដំបង: "Battambang",
  តាកែវ: "Takeo",
};

const SHOP_BLURBS: Record<string, string> = {
  V01: "Names carved to order.",
  V02: "Small-batch flower hair clips.",
  V03: "Khmer silk embroidery.",
  V04: "Tools and aprons for makers.",
  V05: "Wood from the Tonle Sap.",
  V06: "Quiet home textiles.",
  V07: "Heavy market bags since 2015.",
  V08: "Hand-stitched buffalo leather.",
  V09: "One-of-a-kind clay glaze.",
  V10: "New paper studio, in review.",
};

const TIERS: Record<string, string> = {
  starter: "Starter",
  growth: "Growth",
  established: "Established",
  power: "Power seller",
};

const DOC_KINDS: Record<string, string> = {
  government_id: "ID card",
  address_proof: "Address proof",
  payout_account: "Bank account",
};

const PRODUCT_SALE: Record<string, number> = {
  P01: 15,
  P03: 12,
  P04: 10,
  P07: 20,
  P09: 12,
  P12: 5,
  P13: 10,
  P16: 10,
};

const SHOP_SALE: Record<string, number> = {
  V06: 5,
};

export type SaleDeal = { percent: number; was: number; now: number };

export function saleFor(productId?: string | null, vendorId?: string | null, price = 0): SaleDeal | null {
  const percent = (productId && PRODUCT_SALE[productId]) || (vendorId && SHOP_SALE[vendorId]) || 0;
  if (!percent || price <= 0) return null;
  return { percent, now: price, was: Math.round(price / (1 - percent / 100)) };
}

export function shopLabel(slug: string, fallback: string) {
  return SHOP_IDS[slug] || SHOPS[slug] || fallback;
}

export function productLabel(id: string, fallback: string) {
  return PRODUCTS[id] || fallback;
}

export function productBlurb(id: string, fallback: string) {
  return PRODUCT_BLURBS[id] || fallback;
}

export function categoryLabel(slug: string | null | undefined, fallback: string) {
  if (!slug) return fallback;
  return CATEGORIES[slug] || fallback;
}

export function cityLabel(city: string) {
  return CITIES[city] || city;
}

export function shopBlurb(id: string, fallback = "") {
  return SHOP_BLURBS[id] || fallback;
}

export function tierLabel(id: string, fallback = "") {
  return TIERS[id] || fallback.replaceAll("_", " ") || "Shop";
}

export function docLabel(kind: string, fallback = "") {
  return DOC_KINDS[kind] || fallback;
}

export function isDemoListing(title: string) {
  return /\bQA\b/i.test(title);
}
