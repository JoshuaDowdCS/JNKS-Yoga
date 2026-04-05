export interface CategoryFeedback {
  strengths: string[];
  issues: string[];
  corrections: string[];
}

export interface CategoryScore {
  name: string;
  score: number;
  label: "Excellent" | "Good" | "Needs Work" | "Poor";
  tip: string;
  feedback?: CategoryFeedback | null;
}

export interface ClipResult {
  clip_index: number;
  time_range: string;
  feedback: string;
}

export interface AnalysisResult {
  overallScore: number;
  overallLabel: "Excellent" | "Good" | "Needs Work" | "Poor";
  categories: CategoryScore[];
  timestamp: string;
  inputType: "webcam" | "upload";
  coaching?: string;
  coachSummary?: string | null;
  clips?: ClipResult[] | null;
}
