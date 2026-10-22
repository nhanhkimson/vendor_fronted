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
    <html lang="en" className={`${sans.variable} ${serif.variable} ${khmer.variable} h-full`}>
      <body className={`${sans.className} bazaar min-h-full`}>
        <Providers>
          <SiteHeader />
          <main>{children}</main>
          <SiteFooter />
        </Providers>
      </body>
    </html>
  );
}
