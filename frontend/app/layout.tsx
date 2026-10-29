import React from "react";
import type { Metadata } from "next";
import "./globals.css";
import { AuthGuard } from "../components/AuthGuard";
import { AppShell } from "../components/AppShell";

export const metadata: Metadata = {
  title: "AI Document Screening System",
  description: "AI-assisted border identity & document screening decision support system",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-slate-50 min-h-screen text-slate-900 antialiased">
        <AuthGuard>
          <AppShell>{children}</AppShell>
        </AuthGuard>
      </body>
    </html>
  );
}
