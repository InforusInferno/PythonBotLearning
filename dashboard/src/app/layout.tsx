import type { Metadata } from "next";
import { Outfit } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/Providers"; // <--- Add this

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
});

export const metadata: Metadata = {
  title: "HorizonBot Dashboard",
  description: "Manage your Discord ecosystem with this interface.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${outfit.variable}`}>
        <Providers> {/* <--- Wrap children in Providers */}
          {children}
        </Providers>
      </body>
    </html>
  );
}
