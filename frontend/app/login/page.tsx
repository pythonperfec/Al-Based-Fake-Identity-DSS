"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "../../lib/api";
import { Shield, Lock, User, AlertCircle, Info } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await api.login(username.trim(), password);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err?.message || "Authentication failed. Please verify credentials.");
    } finally {
      setLoading(false);
    }
  };

  const fillCredentials = (user: string, pass: string) => {
    setUsername(user);
    setPassword(pass);
    setError(null);
  };

  return (
    <div className="w-full max-w-md bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden">
      <div className="bg-slate-950 p-6 text-white text-center border-b border-slate-800">
        <div className="inline-flex p-3 bg-blue-600 rounded-xl mb-3 shadow-md">
          <Shield className="w-7 h-7 text-white" />
        </div>
        <h2 className="text-xl font-bold tracking-tight">Border Screening DSS</h2>
        <p className="text-xs text-slate-400 mt-1">
          Identity & Document Verification Portal
        </p>
      </div>

      <div className="p-6 md:p-8 space-y-6">
        {error && (
          <div className="flex items-start space-x-3 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-xs">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5 text-red-500" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Username
            </label>
            <div className="relative">
              <User className="w-4 h-4 text-slate-400 absolute left-3 top-3 pointer-events-none" />
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="officer or admin"
                className="w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3 pointer-events-none" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold text-sm rounded-lg shadow-sm transition-colors flex items-center justify-center space-x-2"
          >
            {loading ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <span>Sign In</span>
            )}
          </button>
        </form>

        {process.env.NEXT_PUBLIC_DEMO_MODE === "true" && (
          <div className="pt-4 border-t border-slate-200">
            <div className="flex items-center space-x-1.5 text-xs text-slate-500 mb-2 font-medium">
              <Info className="w-3.5 h-3.5" />
              <span>Pre-seeded Demo Credentials:</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <button
                type="button"
                onClick={() => fillCredentials("officer", "OfficerSecure2026!")}
                className="p-2 text-left bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg transition-colors"
              >
                <div className="font-semibold text-slate-800">Officer Role</div>
                <div className="text-[11px] text-slate-500">username: officer</div>
              </button>
              <button
                type="button"
                onClick={() => fillCredentials("admin", "AdminSecure2026!")}
                className="p-2 text-left bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg transition-colors"
              >
                <div className="font-semibold text-slate-800">Admin Role</div>
                <div className="text-[11px] text-slate-500">username: admin</div>
              </button>
            </div>
          </div>
        )}

        <p className="text-[11px] text-center text-slate-400 leading-relaxed">
          Operational Invariant: AI assists the officer; it never makes the final border decision.
        </p>
      </div>
    </div>
  );
}

