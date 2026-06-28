import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Order Management & AI Diagnostic Dashboard",
  description: "Next.js + FastAPI fullstack prototype with async task processing, webhook verification, and database persistence.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  );
}
