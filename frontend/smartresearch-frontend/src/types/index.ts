export type FileInfo = {
  file_id: string;
  old_name: string;
  new_name: string;
  title?: string | null;
  authors?: string | null;
  year?: number | null;
  size_bytes: number;
};

export type JobStart = {
  file_ids: string[];
  max_pages?: number;
  num_topics?: number;
  cluster_k?: number | null;
  summary_chars?: number;
  section_mode?: "full" | "abstract" | "section";
  section_label?: string | null;
  use_abstractive?: boolean; // ← new
};


export type JobStatus = {
  state: "QUEUED" | "PROCESSING" | "DONE" | "ERROR";
  stage: string;
  overall_progress: number;   // 0..100
  message?: string | null;
  eta_seconds?: number | null;   // 👈 add this
};

export type ClusterMember = {
  file_id: string;
  new_name?: string | null;
  title?: string | null;
  authors?: string | null;
  year?: number | null;
  paper_summary?: string | null;
  key_terms: string[];
};

export type Cluster = {
  topic_id: number;
  topic_label: string;
  summary: string;
  members: ClusterMember[];
};

export type JobResult = {
  job_id: string;
  clusters: Cluster[];
  metrics: { [k: string]: string | number };
};
