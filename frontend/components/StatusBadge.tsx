import React from "react";
import { ScreeningStatus, RiskLevel } from "../lib/types";

interface StatusBadgeProps {
  status: ScreeningStatus;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const styles: Record<ScreeningStatus, string> = {
    queued: "bg-gray-100 text-gray-700 border-gray-300",
    processing: "bg-blue-100 text-blue-800 border-blue-300 animate-pulse",
    completed: "bg-green-100 text-green-800 border-green-300",
    incomplete: "bg-amber-100 text-amber-800 border-amber-300",
    failed: "bg-red-100 text-red-800 border-red-300",
  };

  const labels: Record<ScreeningStatus, string> = {
    queued: "Queued",
    processing: "Processing",
    completed: "Completed",
    incomplete: "Incomplete",
    failed: "Failed",
  };

  const currentStyle = styles[status] || "bg-gray-100 text-gray-700 border-gray-300";
  const label = labels[status] || status;

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${currentStyle}`}
    >
      {label}
    </span>
  );
}

interface RiskBadgeProps {
  riskLevel: RiskLevel | null;
}

export function RiskBadge({ riskLevel }: RiskBadgeProps) {
  if (!riskLevel) {
    return <span className="text-xs text-gray-400 font-mono">-</span>;
  }

  const styles: Record<RiskLevel, string> = {
    low: "bg-green-100 text-green-800 border-green-300",
    review_required: "bg-amber-100 text-amber-800 border-amber-300",
    high: "bg-red-100 text-red-800 border-red-300 font-bold",
    incomplete: "bg-gray-100 text-gray-700 border-gray-300",
  };

  const labels: Record<RiskLevel, string> = {
    low: "Low Risk",
    review_required: "Review Required",
    high: "High Risk",
    incomplete: "Incomplete",
  };

  const currentStyle = styles[riskLevel] || "bg-gray-100 text-gray-700 border-gray-300";
  const label = labels[riskLevel] || riskLevel;

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${currentStyle}`}
    >
      {label}
    </span>
  );
}

