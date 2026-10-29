"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getStoredSession, api } from "../lib/api";
import { UserSession } from "../lib/types";
import { Shield, LogOut, UserCheck } from "lucide-react";

export function Navbar() {
  const router = useRouter();
  const [session, setSession] = useState<UserSession | null>(null);

  useEffect(() => {
    setSession(getStoredSession());
  }, []);

  const handleLogout = () => {
    api.logout();
    router.push("/login");
  };

  return (
    <header className="h-16 bg-white border-b border-gray-200 px-6 flex items-center justify-between sticky top-0 z-20">
      <div className="flex items-center space-x-3">
        <div className="bg-blue-600 text-white p-1.5 rounded-lg shadow-sm">
          <Shield className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-base font-bold text-gray-900 tracking-tight leading-none">
            Document Screening DSS
          </h1>
          <p className="text-[11px] text-gray-500 font-medium">Border & Identity Verification Platform</p>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        {session && (
          <div className="flex items-center space-x-2.5 bg-gray-50 border border-gray-200 py-1 px-3 rounded-full">
            <UserCheck className="w-4 h-4 text-gray-500" />
            <span className="text-xs font-medium text-gray-700">
              {session.username}
            </span>
            <span
              className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full ${
                session.role === "admin"
                  ? "bg-purple-100 text-purple-800 border border-purple-200"
                  : "bg-blue-100 text-blue-800 border border-blue-200"
              }`}
            >
              {session.role}
            </span>
          </div>
        )}

        <button
          onClick={handleLogout}
          className="flex items-center space-x-1.5 text-xs font-semibold text-gray-600 hover:text-red-600 hover:bg-red-50 px-3 py-1.5 rounded-md transition-colors border border-transparent hover:border-red-200"
        >
          <LogOut className="w-4 h-4" />
          <span>Logout</span>
        </button>
      </div>
    </header>
  );
}

