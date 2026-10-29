"use client";

import React, { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { api } from "../../lib/api";
import { ScreeningSummary } from "../../lib/types";
import { StatusBadge, RiskBadge } from "../../components/StatusBadge";
import {
  FileText,
  PlusCircle,
  RefreshCw,
  AlertTriangle,
  Clock,
  ShieldAlert,
  CheckCircle2,
} from "lucide-react";

export default function DashboardPage() {
  const [screenings, setScreenings] = useState<ScreeningSummary[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date());
  const [error, setError] = useState<string | null>(null);

  const fetchScreenings = useCallback(async (isBackground = false) => {
    if (!isBackground) setLoading(true);
    try {
      const res = await api.listScreenings();
      setScreenings(res.items);
      setTotal(res.total);
      setLastRefreshed(new Date());
      setError(null);
    } catch (err: any) {
      setError(err?.message || "Failed to load screenings");
    } finally {
      if (!isBackground) setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchScreenings();
    // Auto-refresh every 5 seconds per contract requirement
    const interval = setInterval(() => {
      fetchScreenings(true);
    }, 5000);
    return () => clearInterval(interval);
  }, [fetchScreenings]);

  // Derived metrics
  const reviewRequiredCount = screenings.filter((s) => s.risk_level === "review_required").length;
  const incompleteCount = screenings.filter((s) => s.status === "incomplete" || s.risk_level === "incomplete").length;
  const completedCount = screenings.filter((s) => s.status === "completed").length;

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Screening Queue
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Real-time identity verification feed for border control officers.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 text-xs text-slate-500 bg-white border border-slate-200 px-3 py-1.5 rounded-lg shadow-2xs">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>Auto-refreshing 5s</span>
            <span className="text-slate-400 text-[10px]">
              ({lastRefreshed.toLocaleTimeString()})
            </span>
          </div>

          <button
            onClick={() => fetchScreenings(false)}
            title="Refresh now"
            className="p-1.5 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg border border-slate-200 bg-white transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          <Link
            href="/screenings/new"
            className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-2xs transition-colors"
          >
            <PlusCircle className="w-4 h-4" />
            <span>New Screening</span>
          </Link>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Screenings</span>
            <FileText className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{total}</div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs">
          <div className="flex items-center justify-between text-amber-600 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Review Required (in this view)</span>
            <ShieldAlert className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{reviewRequiredCount}</div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Incomplete (in this view)</span>
            <Clock className="w-4 h-4 text-slate-400" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{incompleteCount}</div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs">
          <div className="flex items-center justify-between text-emerald-600 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Completed (in this view)</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{completedCount}</div>
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="flex items-center space-x-2 p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg">
          <AlertTriangle className="w-4 h-4 text-red-500 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Screenings Table */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-2xs overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-800">
            Recent Submissions
          </h2>
          <span className="text-xs text-slate-500">
            Ordered newest first
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
              <tr>
                <th scope="col" className="px-6 py-3">Screening ID</th>
                <th scope="col" className="px-6 py-3">Document Type</th>
                <th scope="col" className="px-6 py-3">Status</th>
                <th scope="col" className="px-6 py-3">Risk Level</th>
                <th scope="col" className="px-6 py-3">Risk Signal</th>
                <th scope="col" className="px-6 py-3">Submitted</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading && screenings.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-slate-400">
                    <div className="flex flex-col items-center justify-center space-y-2">
                      <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                      <span>Loading screening records...</span>
                    </div>
                  </td>
                </tr>
              ) : screenings.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-slate-400">
                    No screenings recorded yet. Upload a document to start screening.
                  </td>
                </tr>
              ) : (
                screenings.map((s) => (
                  <tr key={s.screening_id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-6 py-4 font-mono font-medium text-slate-800">
                      <span title={s.screening_id}>
                        {s.screening_id.slice(0, 8)}...{s.screening_id.slice(-4)}
                      </span>
                    </td>
                    <td className="px-6 py-4 capitalize font-medium text-slate-700">
                      {s.document_type.replace("_", " ")}
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={s.status} />
                    </td>
                    <td className="px-6 py-4">
                      {s.status === "queued" || s.status === "processing" ? (
                        <span className="text-slate-300 font-mono">—</span>
                      ) : (
                        <RiskBadge riskLevel={s.risk_level} />
                      )}
                    </td>
                    <td className="px-6 py-4 font-mono font-medium text-slate-700">
                      {s.risk_score !== null && s.risk_score !== undefined ? (
                        <div
                          className="flex items-center space-x-1.5 cursor-help"
                          title="Screening signal, not a probability of fraud"
                        >
                          <span>{s.risk_score.toFixed(1)}</span>
                          <span className="text-[10px] text-slate-400 font-sans">signal</span>
                        </div>
                      ) : (
                        <span
                          className="text-slate-300 cursor-help"
                          title="Screening signal, not a probability of fraud"
                        >
                          —
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-slate-500">
                      {new Date(s.created_at).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                        second: "2-digit",
                      })}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

