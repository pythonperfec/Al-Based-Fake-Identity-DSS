"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { Navbar } from "./Navbar";
import { Sidebar } from "./Sidebar";
import { AlertTriangle } from "lucide-react";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isLoginPage = pathname === "/login";
  const isMock = process.env.NEXT_PUBLIC_USE_MOCK === "true";

  if (isLoginPage) {
    return (
      <div className="min-h-screen bg-slate-900 flex flex-col justify-between">
        {isMock && (
          <div className="bg-amber-400 text-amber-950 px-4 py-2 text-xs font-bold text-center flex items-center justify-center space-x-2 shadow-sm">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span className="uppercase tracking-wider font-extrabold">MOCK MODE</span>
            <span className="font-medium text-amber-900">— Returning simulated contract data</span>
          </div>
        )}
        <main className="flex-1 flex items-center justify-center p-4">
          {children}
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      {isMock && (
        <div className="bg-amber-400 text-amber-950 px-4 py-1.5 text-xs font-bold text-center flex items-center justify-center space-x-2 shadow-sm sticky top-0 z-30">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span className="uppercase tracking-wider font-extrabold">MOCK MODE</span>
          <span className="font-medium text-amber-900">— Simulated responses active (Backend bypassed)</span>
        </div>
      )}
      <Navbar />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 p-6 md:p-8 bg-slate-50 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
}

