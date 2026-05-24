export interface Project {
  id: number
  user_id?: string | null
  name: string
  description?: string | null
  status: string
  github_repo_owner?: string | null
  github_repo_name?: string | null
  slack_channel_id?: string | null
  slack_channel_name?: string | null
  created_at: string
  updated_at?: string | null
}

export interface Document {
  id: number
  user_id?: string | null
  project_id: number
  filename: string
  filetype?: string | null
  storage_path?: string | null
  status: string
  created_at: string
  updated_at?: string | null
}

export interface DocumentChunk {
  id: number
  document_id: number
  project_id: number
  chunk_index: number
  content: string
  qdrant_point_id?: string | null
  token_count?: number | null
  created_at: string
}

export interface Task {
  id: number
  user_id?: string | null
  project_id: number
  title: string
  description?: string | null
  priority: 'low' | 'medium' | 'high' | string
  status: string
  approved: boolean
  created_at: string
  updated_at?: string | null
}

export interface GitHubIssue {
  id: number
  user_id?: string | null
  project_id: number
  task_id: number
  issue_number: number
  issue_url: string
  title: string
  created_at: string
}

export interface AuditLog {
  id: number
  user_id?: string | null
  project_id?: number | null
  action: string
  tool_name?: string | null
  input_data?: string | null
  output_data?: string | null
  status: string
  created_at: string
}

export interface WorkflowRun {
  id: number
  user_id?: string | null
  project_id: number
  workflow_type: string
  status: string
  input_data?: string | null
  output_data?: string | null
  error_message?: string | null
  started_at: string
  completed_at?: string | null
}

export interface ProjectSearchResult {
  score: number
  chunk_id?: number | string | null
  document_id?: number | string | null
  chunk_index?: number | string | null
  content?: string | null
}

export interface ProjectSearchResponse {
  project_id: number
  query: string
  results: ProjectSearchResult[]
}

export interface SlackDraftResponse {
  project_id: number
  slack_channel_id?: string | null
  slack_channel_name?: string | null
  draft: string | { message?: string; text?: string; [key: string]: unknown }
}

export interface AnalyzeResponse {
  project_id: number
  chunks_used: number
  tasks_created: number
}

export interface GitHubIssueCreationResponse {
  project_id: number
  issues_created: number
  issues: Array<{
    task_id: number
    issue_number: number
    issue_url: string
    title: string
  }>
  skipped_tasks: Array<{
    task_id: number
    reason: string
    issue_url?: string
  }>
}
