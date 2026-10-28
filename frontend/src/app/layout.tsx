import type { Metadata } from "next";
import { Cormorant_Garamond, Kantumruy_Pro, Outfit } from "next/font/google";

import { Providers } from "@/components/providers";
import { SiteFooter, SiteHeader } from "@/components/site";

import "./globals.css";

const sans = Outfit({ subsets: ["latin"], variable: "--font-outfit" });
const serif = Cormorant_Garamond({ subsets: ["latin"], weight: ["500", "600"], variable: "--font-serif" });
const khmer = Kantumruy_Pro({ subsets: ["khmer", "latin"], weight: ["400", "600"], variable: "--font-khmer" });

export const metadata: Metadata = {
  title: "Bazaar",
  description: "A multi-vendor marketplace. Many shops, one checkout.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${sans.variable} ${serif.variable} ${khmer.variable} h-full`} suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&display=swap"
          rel="stylesheet"
        />
        {/* Apply saved locale before paint so Khmer/Chinese fonts are ready on first frame. */}
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var l=localStorage.getItem("bazaar-locale");if(l==="en"||l==="km"||l==="zh"){document.documentElement.dataset.locale=l;document.documentElement.lang=l==="zh"?"zh-CN":l;}}catch(e){}})();`,
          }}
        />
      </head>
      <body className="bazaar min-h-full">
        <Providers>
          <SiteHeader />
          <main>{children}</main>
          <SiteFooter />
        </Providers>
      </body>
    </html>
  );
}
