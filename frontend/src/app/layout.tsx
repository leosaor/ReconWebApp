import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Clavis Recon Surface",
  description: "Plataforma Clavis para reconhecimento automatizado autorizado",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body className="bg-[#06111f] text-slate-100 antialiased">{children}</body>
    </html>
  );
}
