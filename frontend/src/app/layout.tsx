import type { Metadata } from "next";
import { Cormorant_Garamond, Kantumruy_Pro, Outfit } from "next/font/google";

import { AppChrome } from "@/components/chrome";
import { Providers } from "@/components/providers";

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
        {/* Theme before paint. Locale is locked to English until translation work resumes. */}
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{document.documentElement.dataset.locale="en";document.documentElement.lang="en";var t=localStorage.getItem("theme");var d=window.matchMedia("(prefers-color-scheme: dark)").matches;if(t==="dark"||(t!=="light"&&d)){document.documentElement.classList.add("dark");}else{document.documentElement.classList.remove("dark");}}catch(e){}})();`,
          }}
        />
      </head>
      <body className="bazaar min-h-full">
        <Providers>
          <AppChrome>{children}</AppChrome>
        </Providers>
      </body>
    </html>
  );
}
