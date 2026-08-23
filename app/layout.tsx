import type { Metadata } from "next";
import "leaflet/dist/leaflet.css";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:5173"),
  title: "HeatOps Decision Dashboard",
  description:
    "Explainable heat-risk analysis and cooling-resource placement for urban response teams.",
  openGraph: {
    title: "HeatOps Decision Dashboard",
    description: "From heat intelligence to action.",
    images: [{ url: "/og.png", width: 1200, height: 630, alt: "HeatOps" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "HeatOps Decision Dashboard",
    description: "From heat intelligence to action.",
    images: ["/og.png"],
  },
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
