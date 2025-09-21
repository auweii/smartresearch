import axios from "axios";
import type { FileInfo, JobStart, JobStatus, JobResult } from "../types";

const BASE = process.env.NEXT_PUBLIC_BACKEND!;

export async function uploadOne(file: File): Promise<FileInfo> {
  const form = new FormData();
  form.append("files", file, file.name);
  const { data } = await axios.post<FileInfo[]>(`${BASE}/files`, form, {
    onUploadProgress: () => {}, // handled per-row in UI if you want
    headers: { "ngrok-skip-browser-warning": "1" },
  });
  return data[0]; // we send one file at a time
}

export async function startJob(payload: JobStart): Promise<string> {
  const { data } = await axios.post<{ job_id: string }>(`${BASE}/jobs/summarize_cluster`, payload);
  return data.job_id;
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const { data } = await axios.get<JobStatus>(`${BASE}/jobs/${jobId}/status`);
  return data;
}

export async function getJobResult(jobId: string): Promise<JobResult | { error: string }> {
  const { data } = await axios.get(`${BASE}/jobs/${jobId}/result`);
  return data;
}
