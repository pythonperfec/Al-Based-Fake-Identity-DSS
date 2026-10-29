"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "../../../lib/api";
import { ApiError } from "../../../lib/types";
import { UploadCloud, File as FileIcon, AlertCircle, ArrowLeft, CheckCircle2 } from "lucide-react";

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ALLOWED_MIME_TYPES = ["image/jpeg", "image/png"];

export default function NewScreeningPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [documentType, setDocumentType] = useState<"passport" | "national_id">("passport");
  // Idempotency-Key is generated once per submit attempt and reused on retry
  const [idempotencyKey, setIdempotencyKey] = useState<string>(() => crypto.randomUUID());
  const [loading, setLoading] = useState<boolean>(false);
  const [errorDetails, setErrorDetails] = useState<ApiError | null>(null);

  const handleFileChange = (newFile: File | null) => {
    setErrorDetails(null);
    if (!newFile) {
      setFile(null);
      return;
    }

    // Client-side validations
    if (!ALLOWED_MIME_TYPES.includes(newFile.type)) {
      setErrorDetails({
        error: "UNSUPPORTED_MEDIA_TYPE",
        message: `File type "${newFile.type || "unknown"}" is not supported. Only image/jpeg and image/png are allowed.`,
      });
      setFile(null);
      return;
    }

    if (newFile.size > MAX_FILE_SIZE) {
      setErrorDetails({
        error: "PAYLOAD_TOO_LARGE",
        message: `File size ${(newFile.size / (1024 * 1024)).toFixed(1)}MB exceeds maximum 10MB limit.`,
      });
      setFile(null);
      return;
    }

    setFile(newFile);
    // Generate new key when new file is selected
    setIdempotencyKey(crypto.randomUUID());
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setErrorDetails({
        error: "VALIDATION_ERROR",
        message: "Please select an image file to screen.",
      });
      return;
    }

    setLoading(true);
    setErrorDetails(null);

    try {
      // Reuses the same idempotencyKey on retry
      await api.createScreening(file, documentType, idempotencyKey);
      router.push("/dashboard");
    } catch (err: any) {
      // Show error adhering to { error, message } envelope
      setErrorDetails({
        error: err?.error || "SUBMISSION_FAILED",
        message: err?.message || "Failed to submit document for screening.",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center space-x-3">
        <Link
          href="/dashboard"
          className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            New Document Screening
          </h1>
          <p className="text-xs text-slate-500">
            Submit document inspection image for automated anomaly and validity screening.
          </p>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-6 md:p-8 shadow-2xs">
        {errorDetails && (
          <div className="flex items-start space-x-3 p-3.5 mb-6 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5 text-red-500" />
            <div>
              <div className="font-bold uppercase tracking-wider text-[11px] mb-0.5">
                {errorDetails.error}
              </div>
              <p className="text-red-800">{errorDetails.message}</p>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Document Type Selection */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
              Document Type
            </label>
            <div className="grid grid-cols-2 gap-3">
              <label
                className={`flex items-center justify-between p-3.5 border rounded-lg cursor-pointer transition-colors ${
                  documentType === "passport"
                    ? "border-blue-600 bg-blue-50/50 text-blue-900 font-semibold"
                    : "border-slate-200 hover:bg-slate-50 text-slate-700"
                }`}
              >
                <div className="flex items-center space-x-2.5">
                  <input
                    type="radio"
                    name="document_type"
                    value="passport"
                    checked={documentType === "passport"}
                    onChange={() => setDocumentType("passport")}
                    className="text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm">Passport</span>
                </div>
              </label>

              <label
                className={`flex items-center justify-between p-3.5 border rounded-lg cursor-pointer transition-colors ${
                  documentType === "national_id"
                    ? "border-blue-600 bg-blue-50/50 text-blue-900 font-semibold"
                    : "border-slate-200 hover:bg-slate-50 text-slate-700"
                }`}
              >
                <div className="flex items-center space-x-2.5">
                  <input
                    type="radio"
                    name="document_type"
                    value="national_id"
                    checked={documentType === "national_id"}
                    onChange={() => setDocumentType("national_id")}
                    className="text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm">National ID</span>
                </div>
              </label>
            </div>
          </div>

          {/* File Upload Dropzone */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
              Document Image Payload
            </label>
            <div className="border-2 border-dashed border-slate-300 hover:border-blue-400 rounded-xl p-8 text-center transition-colors bg-slate-50/50">
              <input
                type="file"
                id="file-upload"
                accept="image/jpeg,image/png"
                onChange={(e) => handleFileChange(e.target.files?.[0] || null)}
                className="hidden"
              />
              <label
                htmlFor="file-upload"
                className="cursor-pointer flex flex-col items-center justify-center space-y-2"
              >
                <div className="p-3 bg-white rounded-full border border-slate-200 shadow-2xs">
                  <UploadCloud className="w-6 h-6 text-blue-600" />
                </div>
                {file ? (
                  <div className="flex items-center space-x-2 text-xs font-medium text-slate-800">
                    <FileIcon className="w-4 h-4 text-blue-600" />
                    <span>{file.name}</span>
                    <span className="text-slate-400">
                      ({(file.size / 1024).toFixed(1)} KB)
                    </span>
                  </div>
                ) : (
                  <>
                    <p className="text-sm font-semibold text-slate-700">
                      Click to upload or drag & drop image
                    </p>
                    <p className="text-xs text-slate-500">
                      Supported formats: image/jpeg, image/png only (max 10MB)
                    </p>
                  </>
                )}
              </label>
            </div>
            <div className="mt-2 text-[11px] text-slate-400 font-mono">
              Idempotency-Key: {idempotencyKey} (preserved across retries)
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-200">
            <Link
              href="/dashboard"
              className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={loading || !file}
              className="px-5 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 text-white text-xs font-semibold rounded-lg shadow-2xs transition-colors flex items-center space-x-2"
            >
              {loading ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Submitting Screening...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Submit for Screening</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
