"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, PlusCircle } from "lucide-react";

export function Sidebar() {
  const pathname = usePathname();

  const links = [
    {
      name: "Dashboard",
      href: "/dashboard",
      icon: LayoutDashboard,
    },
    {
      name: "New Screening",
      href: "/screenings/new",
      icon: PlusCircle,
    },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 min-h-[calc(100vh-4rem)] flex flex-col justify-between p-4 border-r border-slate-800">
      <div>
        <div className="text-[11px] font-semibold text-slate-400 tracking-wider uppercase px-3 mb-3">
          Navigation
        </div>
        <nav className="space-y-1">
          {links.map((link) => {
            const Icon = link.icon;
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.name}
                href={link.href}
                className={`flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-blue-600 text-white shadow-sm"
                    : "hover:bg-slate-800 text-slate-300 hover:text-white"
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{link.name}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="bg-slate-800/60 border border-slate-700/50 rounded-lg p-3 text-xs">
        <p className="font-semibold text-slate-200">System Mode</p>
        <p className="text-slate-400 mt-1">
          {process.env.NEXT_PUBLIC_USE_MOCK === "true" ? (
            <span className="inline-flex items-center text-amber-400 font-medium">
              ● Mock Mode Active
            </span>
          ) : (
            <span className="inline-flex items-center text-green-400 font-medium">
              ● Live Backend Connected
            </span>
          )}
        </p>
      </div>
    </aside>
  );
}

