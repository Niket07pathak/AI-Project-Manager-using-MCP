import type {
  AnalyzeResponse,
  AuditLog,
  Document,
  DocumentChunk,
  GitHubIssue,
  GitHubIssueCreationResponse,
  Project,
  ProjectSearchResponse,
  SlackDraftResponse,
  Task,
  WorkflowRun,
} from '../types/api'

type GetToken = () => Promise<string | null>

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

async function readError(response: Response): Promise<string> {
  try {
    const data = (await response.json()) as { detail?: unknown; message?: unknown }
    const detail = data.detail ?? data.message
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) return detail.map((item) => item.msg ?? String(item)).join(', ')
    if (detail) return JSON.stringify(detail)
  } catch {
    return response.statusText
  }
  return response.statusText
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  getToken: GetToken,
): Promise<T> {
  const token = await getToken()
  if (!token) throw new Error('Authentication token is missing.')

  const headers = new Headers(options.headers)

  headers.set('Authorization', `Bearer ${token}`)
  if (options.body && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    throw new Error(await readError(response))
  }

  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

export async function uploadDocument(
  projectId: number,
  file: File,
  getToken: GetToken,
): Promise<Document> {
  const formData = new FormData()
  formData.append('file', file)

  return apiRequest<Document>(
    `/projects/${projectId}/documents/upload`,
    {
      method: 'POST',
      body: formData,
    },
    getToken,
  )
}

export const api = {
  listProjects: (getToken: GetToken) => apiRequest<Project[]>('/projects', {}, getToken),
  createProject: (payload: Partial<Project>, getToken: GetToken) =>
    apiRequest<Project>(
      '/projects',
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      getToken,
    ),
  getProject: (projectId: number, getToken: GetToken) =>
    apiRequest<Project>(`/projects/${projectId}`, {}, getToken),
  listDocuments: (projectId: number, getToken: GetToken) =>
    apiRequest<Document[]>(`/projects/${projectId}/documents`, {}, getToken),
  processDocument: (documentId: number, getToken: GetToken) =>
    apiRequest<{ document_id: number; project_id: number; chunks_created: number; status: string }>(
      `/documents/${documentId}/process`,
      { method: 'POST' },
      getToken,
    ),
  listDocumentChunks: (documentId: number, getToken: GetToken) =>
    apiRequest<DocumentChunk[]>(`/documents/${documentId}/chunks`, {}, getToken),
  searchProject: (projectId: number, query: string, topK: number, getToken: GetToken) =>
    apiRequest<ProjectSearchResponse>(
      `/projects/${projectId}/search`,
      {
        method: 'POST',
        body: JSON.stringify({ query, top_k: topK }),
      },
      getToken,
    ),
  analyzeProject: (projectId: number, getToken: GetToken) =>
    apiRequest<AnalyzeResponse>(`/projects/${projectId}/analyze`, { method: 'POST' }, getToken),
  listTasks: (projectId: number, getToken: GetToken) =>
    apiRequest<Task[]>(`/project/${projectId}/tasks`, {}, getToken),
  approveTask: (taskId: number, getToken: GetToken) =>
    apiRequest<Task>(`/tasks/${taskId}/approve`, { method: 'PATCH' }, getToken),
  rejectTask: (taskId: number, getToken: GetToken) =>
    apiRequest<Task>(`/tasks/${taskId}/reject`, { method: 'PATCH' }, getToken),
  editTask: (
    taskId: number,
    payload: { title?: string; description?: string; priority?: string },
    getToken: GetToken,
  ) =>
    apiRequest<Task>(
      `/tasks/${taskId}/edit`,
      {
        method: 'PATCH',
        body: JSON.stringify(payload),
      },
      getToken,
    ),
  createGitHubIssues: (projectId: number, getToken: GetToken) =>
    apiRequest<GitHubIssueCreationResponse>(
      `/projects/${projectId}/github/issues/create`,
      { method: 'POST' },
      getToken,
    ),
  listGitHubIssues: (projectId: number, getToken: GetToken) =>
    apiRequest<GitHubIssue[]>(`/projects/${projectId}/github/issues`, {}, getToken),
  draftSlackUpdate: (projectId: number, getToken: GetToken) =>
    apiRequest<SlackDraftResponse>(
      `/projects/${projectId}/notifications/slack/draft`,
      { method: 'POST' },
      getToken,
    ),
  sendSlackUpdate: (projectId: number, message: string, getToken: GetToken) =>
    apiRequest<unknown>(
      `/projects/${projectId}/notifications/slack/send`,
      {
        method: 'POST',
        body: JSON.stringify({ message }),
      },
      getToken,
    ),
  listAuditLogs: (projectId: number, getToken: GetToken) =>
    apiRequest<AuditLog[]>(`/projects/${projectId}/audit-logs`, {}, getToken),
  listWorkflowRuns: (projectId: number, getToken: GetToken) =>
    apiRequest<WorkflowRun[]>(`/projects/${projectId}/workflow-runs`, {}, getToken),
}
