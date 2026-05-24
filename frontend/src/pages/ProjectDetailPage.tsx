import { useAuth } from '@clerk/clerk-react'
import {
  Bot,
  Check,
  ChevronDown,
  ExternalLink,
  FileText,
  GitPullRequest,
  MessageSquare,
  RefreshCw,
  Save,
  Search,
  Send,
  ShieldCheck,
  Upload,
  Workflow,
  X,
} from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, uploadDocument } from '../api/client'
import { EmptyState } from '../components/EmptyState'
import { ErrorState } from '../components/ErrorState'
import { LoadingState } from '../components/LoadingState'
import { StatusBadge } from '../components/StatusBadge'
import type {
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

type Tab = 'overview' | 'documents' | 'tasks' | 'github' | 'slack' | 'audit' | 'workflows'

const tabs: Array<{ id: Tab; label: string; icon: typeof FileText }> = [
  { id: 'overview', label: 'Overview', icon: ShieldCheck },
  { id: 'documents', label: 'Documents', icon: FileText },
  { id: 'tasks', label: 'Tasks', icon: Bot },
  { id: 'github', label: 'GitHub', icon: GitPullRequest },
  { id: 'slack', label: 'Slack', icon: MessageSquare },
  { id: 'audit', label: 'Audit Logs', icon: ShieldCheck },
  { id: 'workflows', label: 'Workflow Runs', icon: Workflow },
]

const formatDate = (value?: string | null) => (value ? new Date(value).toLocaleString() : '-')

const draftToText = (draft: SlackDraftResponse['draft']) => {
  if (typeof draft === 'string') return draft
  if (typeof draft.message === 'string') return draft.message
  if (typeof draft.text === 'string') return draft.text
  return JSON.stringify(draft, null, 2)
}

function StatCard({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="text-sm font-medium text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-black text-slate-950">{value}</p>
    </div>
  )
}

function JsonDetails({ label, value }: { label: string; value?: string | null }) {
  if (!value) return <span className="text-slate-400">-</span>
  return (
    <details className="group">
      <summary className="inline-flex cursor-pointer items-center gap-1 text-sm font-semibold text-blue-700">
        {label}
        <ChevronDown className="h-4 w-4 transition group-open:rotate-180" />
      </summary>
      <pre className="mt-2 max-h-48 overflow-auto rounded-lg bg-slate-950 p-3 text-xs leading-5 text-slate-100">
        {value}
      </pre>
    </details>
  )
}

export function ProjectDetailPage() {
  const { projectId } = useParams()
  const id = Number(projectId)
  const { getToken } = useAuth()

  const [activeTab, setActiveTab] = useState<Tab>('overview')
  const [project, setProject] = useState<Project | null>(null)
  const [documents, setDocuments] = useState<Document[]>([])
  const [tasks, setTasks] = useState<Task[]>([])
  const [issues, setIssues] = useState<GitHubIssue[]>([])
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([])
  const [workflowRuns, setWorkflowRuns] = useState<WorkflowRun[]>([])
  const [chunksByDocument, setChunksByDocument] = useState<Record<number, DocumentChunk[]>>({})
  const [openChunkDocumentId, setOpenChunkDocumentId] = useState<number | null>(null)
  const [searchResponse, setSearchResponse] = useState<ProjectSearchResponse | null>(null)
  const [githubResult, setGithubResult] = useState<GitHubIssueCreationResponse | null>(null)
  const [slackDraft, setSlackDraft] = useState('')
  const [editingTask, setEditingTask] = useState<Task | null>(null)

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [busyAction, setBusyAction] = useState<string | null>(null)

  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [topK, setTopK] = useState(5)

  const loadProjectBundle = useCallback(async () => {
    if (!Number.isFinite(id)) return
    setLoading(true)
    setError(null)
    try {
      const [projectData, documentData, taskData, issueData, auditData, workflowData] = await Promise.all([
        api.getProject(id, getToken),
        api.listDocuments(id, getToken),
        api.listTasks(id, getToken),
        api.listGitHubIssues(id, getToken),
        api.listAuditLogs(id, getToken),
        api.listWorkflowRuns(id, getToken),
      ])
      setProject(projectData)
      setDocuments(Array.isArray(documentData) ? documentData : [])
      setTasks(Array.isArray(taskData) ? taskData : [])
      setIssues(Array.isArray(issueData) ? issueData : [])
      setAuditLogs(Array.isArray(auditData) ? auditData : [])
      setWorkflowRuns(Array.isArray(workflowData) ? workflowData : [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load project')
    } finally {
      setLoading(false)
    }
  }, [getToken, id])

  const refreshObservability = async () => {
    const [auditData, workflowData] = await Promise.all([
      api.listAuditLogs(id, getToken),
      api.listWorkflowRuns(id, getToken),
    ])
    setAuditLogs(Array.isArray(auditData) ? auditData : [])
    setWorkflowRuns(Array.isArray(workflowData) ? workflowData : [])
  }

  const runAction = async (key: string, action: () => Promise<void>) => {
    setBusyAction(key)
    setActionError(null)
    try {
      await action()
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Action failed')
    } finally {
      setBusyAction(null)
    }
  }

  useEffect(() => {
    void loadProjectBundle()
  }, [loadProjectBundle])

  const counts = useMemo(() => {
    const approvedTasks = tasks.filter((task) => task.approved).length
    return {
      documents: documents.length,
      tasks: tasks.length,
      approvedTasks,
      issues: issues.length,
      workflowRuns: workflowRuns.length,
    }
  }, [documents, tasks, issues, workflowRuns])

  const handleUpload = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!selectedFile) return
    await runAction('upload', async () => {
      await uploadDocument(id, selectedFile, getToken)
      setSelectedFile(null)
      setDocuments(await api.listDocuments(id, getToken))
    })
  }

  const handleProcessDocument = async (documentId: number) => {
    await runAction(`process-${documentId}`, async () => {
      await api.processDocument(documentId, getToken)
      setDocuments(await api.listDocuments(id, getToken))
      if (openChunkDocumentId === documentId) {
        const chunks = await api.listDocumentChunks(documentId, getToken)
        setChunksByDocument((current) => ({ ...current, [documentId]: chunks }))
      }
    })
  }

  const handleToggleChunks = async (documentId: number) => {
    if (openChunkDocumentId === documentId) {
      setOpenChunkDocumentId(null)
      return
    }
    setOpenChunkDocumentId(documentId)
    if (!chunksByDocument[documentId]) {
      await runAction(`chunks-${documentId}`, async () => {
        const chunks = await api.listDocumentChunks(documentId, getToken)
        setChunksByDocument((current) => ({ ...current, [documentId]: chunks }))
      })
    }
  }

  const handleSearch = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!searchQuery.trim()) return
    await runAction('search', async () => {
      const result = await api.searchProject(id, searchQuery.trim(), topK, getToken)
      setSearchResponse(result)
    })
  }

  const handleAnalyze = async () => {
    await runAction('analyze', async () => {
      await api.analyzeProject(id, getToken)
      setTasks(await api.listTasks(id, getToken))
      await refreshObservability()
    })
  }

  const handleTaskDecision = async (taskId: number, decision: 'approve' | 'reject') => {
    await runAction(`${decision}-${taskId}`, async () => {
      if (decision === 'approve') await api.approveTask(taskId, getToken)
      else await api.rejectTask(taskId, getToken)
      setTasks(await api.listTasks(id, getToken))
      setAuditLogs(await api.listAuditLogs(id, getToken))
    })
  }

  const handleEditTask = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!editingTask) return
    await runAction(`edit-${editingTask.id}`, async () => {
      await api.editTask(
        editingTask.id,
        {
          title: editingTask.title,
          description: editingTask.description || '',
          priority: editingTask.priority,
        },
        getToken,
      )
      setEditingTask(null)
      setTasks(await api.listTasks(id, getToken))
      setAuditLogs(await api.listAuditLogs(id, getToken))
    })
  }

  const handleCreateIssues = async () => {
    await runAction('github', async () => {
      const result = await api.createGitHubIssues(id, getToken)
      setGithubResult(result)
      setIssues(await api.listGitHubIssues(id, getToken))
      await refreshObservability()
    })
  }

  const handleDraftSlack = async () => {
    await runAction('slack-draft', async () => {
      const result = await api.draftSlackUpdate(id, getToken)
      setSlackDraft(draftToText(result.draft))
      setAuditLogs(await api.listAuditLogs(id, getToken))
    })
  }

  const handleSendSlack = async () => {
    if (!slackDraft.trim()) return
    await runAction('slack-send', async () => {
      await api.sendSlackUpdate(id, slackDraft, getToken)
      await refreshObservability()
    })
  }

  if (!Number.isFinite(id)) {
    return <ErrorState message="Invalid project id" />
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <LoadingState label="Loading project workspace" />
      </div>
    )
  }

  if (error || !project) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
        <ErrorState message={error || 'Project not found'} onRetry={loadProjectBundle} />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
        <div>
          <Link to="/dashboard" className="text-sm font-semibold text-blue-700 hover:text-blue-900">
            Dashboard
          </Link>
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <h1 className="text-3xl font-black text-slate-950">{project.name}</h1>
            <StatusBadge value={project.status} />
          </div>
          <p className="mt-2 max-w-3xl text-slate-600">{project.description || 'No description yet.'}</p>
        </div>
        <button className="btn btn-secondary" onClick={() => void loadProjectBundle()}>
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {actionError ? <div className="mt-6"><ErrorState message={actionError} /></div> : null}

      <div className="mt-8 overflow-x-auto rounded-lg border border-slate-200 bg-white p-1">
        <div className="flex min-w-max gap-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              className={`inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold transition ${
                activeTab === tab.id ? 'bg-blue-600 text-white' : 'text-slate-600 hover:bg-slate-100'
              }`}
              onClick={() => setActiveTab(tab.id)}
            >
              <tab.icon className="h-4 w-4" />
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <section className="mt-6">
        {activeTab === 'overview' ? (
          <div className="space-y-6">
            <div className="grid gap-4 md:grid-cols-5">
              <StatCard label="Documents" value={counts.documents} />
              <StatCard label="Tasks" value={counts.tasks} />
              <StatCard label="Approved tasks" value={counts.approvedTasks} />
              <StatCard label="GitHub issues" value={counts.issues} />
              <StatCard label="Workflow runs" value={counts.workflowRuns} />
            </div>
            <div className="card grid gap-6 rounded-lg p-6 md:grid-cols-2">
              <div>
                <h2 className="text-lg font-bold text-slate-950">GitHub</h2>
                <p className="mt-2 text-slate-600">
                  {project.github_repo_owner && project.github_repo_name
                    ? `${project.github_repo_owner}/${project.github_repo_name}`
                    : 'No GitHub repository configured.'}
                </p>
              </div>
              <div>
                <h2 className="text-lg font-bold text-slate-950">Slack</h2>
                <p className="mt-2 text-slate-600">
                  {project.slack_channel_name || project.slack_channel_id
                    ? `${project.slack_channel_name || 'Channel'} ${project.slack_channel_id ? `(${project.slack_channel_id})` : ''}`
                    : 'No Slack channel configured.'}
                </p>
              </div>
            </div>
          </div>
        ) : null}

        {activeTab === 'documents' ? (
          <div className="space-y-6">
            <form onSubmit={handleUpload} className="card rounded-lg p-5">
              <h2 className="text-lg font-bold text-slate-950">Upload PRD or project document</h2>
              <div className="mt-4 flex flex-col gap-3 sm:flex-row">
                <input
                  className="field"
                  type="file"
                  accept=".pdf,.docx,.txt,application/pdf,text/plain"
                  onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
                />
                <button className="btn btn-primary" disabled={!selectedFile || busyAction === 'upload'}>
                  <Upload className="h-4 w-4" />
                  {busyAction === 'upload' ? 'Uploading' : 'Upload'}
                </button>
              </div>
            </form>

            <div className="card rounded-lg p-5">
              <h2 className="text-lg font-bold text-slate-950">Documents</h2>
              <div className="mt-4 space-y-3">
                {documents.length === 0 ? <EmptyState title="No documents uploaded yet." /> : null}
                {documents.map((document) => (
                  <div key={document.id} className="rounded-lg border border-slate-200 p-4">
                    <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
                      <div>
                        <p className="font-semibold text-slate-950">{document.filename}</p>
                        <p className="mt-1 text-sm text-slate-500">{document.filetype || 'Unknown type'}</p>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <StatusBadge value={document.status} />
                        <button
                          className="btn btn-secondary"
                          onClick={() => void handleProcessDocument(document.id)}
                          disabled={busyAction === `process-${document.id}`}
                        >
                          {busyAction === `process-${document.id}` ? 'Processing' : 'Process'}
                        </button>
                        <button className="btn btn-secondary" onClick={() => void handleToggleChunks(document.id)}>
                          Chunks
                        </button>
                      </div>
                    </div>
                    {openChunkDocumentId === document.id ? (
                      <div className="mt-4 space-y-3">
                        {(chunksByDocument[document.id] || []).map((chunk) => (
                          <div key={chunk.id} className="rounded-lg bg-slate-50 p-3 text-sm text-slate-700">
                            <p className="font-semibold text-slate-900">Chunk {chunk.chunk_index}</p>
                            <p className="mt-1 line-clamp-4">{chunk.content}</p>
                          </div>
                        ))}
                        {(chunksByDocument[document.id] || []).length === 0 ? (
                          <EmptyState title="No chunks found for this document." />
                        ) : null}
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            </div>

            <form onSubmit={handleSearch} className="card rounded-lg p-5">
              <h2 className="text-lg font-bold text-slate-950">Search project documents</h2>
              <div className="mt-4 grid gap-3 md:grid-cols-[1fr_120px_auto]">
                <input className="field" value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} placeholder="Search implementation requirements" />
                <input className="field" type="number" min={1} max={20} value={topK} onChange={(event) => setTopK(Number(event.target.value))} />
                <button className="btn btn-primary" disabled={busyAction === 'search'}>
                  <Search className="h-4 w-4" />
                  Search
                </button>
              </div>
              {searchResponse ? (
                <div className="mt-5 space-y-3">
                  {searchResponse.results.map((result, index) => (
                    <div key={`${result.chunk_id}-${index}`} className="rounded-lg border border-slate-200 p-4">
                      <p className="text-sm font-semibold text-slate-950">
                        Score {Number(result.score).toFixed(3)} | Document {result.document_id ?? '-'} | Chunk {result.chunk_index ?? '-'}
                      </p>
                      <p className="mt-2 text-sm leading-6 text-slate-600">{result.content || 'No preview available.'}</p>
                    </div>
                  ))}
                </div>
              ) : null}
            </form>
          </div>
        ) : null}

        {activeTab === 'tasks' ? (
          <div className="space-y-6">
            <div className="card flex flex-col justify-between gap-4 rounded-lg p-5 sm:flex-row sm:items-center">
              <div>
                <h2 className="text-lg font-bold text-slate-950">LangGraph analysis</h2>
                <p className="mt-1 text-sm text-slate-600">Generate implementation tasks from processed RAG context.</p>
              </div>
              <button className="btn btn-primary" onClick={() => void handleAnalyze()} disabled={busyAction === 'analyze'}>
                <Bot className="h-4 w-4" />
                {busyAction === 'analyze' ? 'Analyzing' : 'Analyze Project'}
              </button>
            </div>

            {tasks.length === 0 ? <EmptyState title="No tasks generated yet." /> : null}
            <div className="grid gap-4 lg:grid-cols-2">
              {tasks.map((task) => (
                <article key={task.id} className="card rounded-lg p-5">
                  <div className="flex items-start justify-between gap-3">
                    <h3 className="text-lg font-bold text-slate-950">{task.title}</h3>
                    <StatusBadge value={task.priority} />
                  </div>
                  <p className="mt-3 text-sm leading-6 text-slate-600">{task.description || 'No description.'}</p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <StatusBadge value={task.status} />
                    <StatusBadge value={task.approved} />
                  </div>
                  <div className="mt-5 flex flex-wrap gap-2">
                    <button className="btn btn-secondary" onClick={() => setEditingTask(task)}>
                      Edit
                    </button>
                    <button className="btn btn-primary" onClick={() => void handleTaskDecision(task.id, 'approve')} disabled={busyAction === `approve-${task.id}`}>
                      <Check className="h-4 w-4" />
                      Approve
                    </button>
                    <button className="btn btn-danger" onClick={() => void handleTaskDecision(task.id, 'reject')} disabled={busyAction === `reject-${task.id}`}>
                      <X className="h-4 w-4" />
                      Reject
                    </button>
                  </div>
                </article>
              ))}
            </div>

            {editingTask ? (
              <form onSubmit={handleEditTask} className="card rounded-lg p-5">
                <h2 className="text-lg font-bold text-slate-950">Edit task</h2>
                <div className="mt-4 grid gap-4">
                  <input className="field" value={editingTask.title} onChange={(event) => setEditingTask({ ...editingTask, title: event.target.value })} />
                  <textarea className="field min-h-28" value={editingTask.description || ''} onChange={(event) => setEditingTask({ ...editingTask, description: event.target.value })} />
                  <select className="field" value={editingTask.priority} onChange={(event) => setEditingTask({ ...editingTask, priority: event.target.value })}>
                    <option value="low">low</option>
                    <option value="medium">medium</option>
                    <option value="high">high</option>
                  </select>
                </div>
                <div className="mt-4 flex gap-2">
                  <button className="btn btn-primary">
                    <Save className="h-4 w-4" />
                    Save task
                  </button>
                  <button type="button" className="btn btn-secondary" onClick={() => setEditingTask(null)}>
                    Cancel
                  </button>
                </div>
              </form>
            ) : null}
          </div>
        ) : null}

        {activeTab === 'github' ? (
          <div className="space-y-6">
            <div className="card flex flex-col justify-between gap-4 rounded-lg p-5 sm:flex-row sm:items-center">
              <div>
                <h2 className="text-lg font-bold text-slate-950">GitHub issues</h2>
                <p className="mt-1 text-sm text-slate-600">Only approved tasks are eligible for issue creation.</p>
              </div>
              <button className="btn btn-primary" onClick={() => void handleCreateIssues()} disabled={busyAction === 'github'}>
                <GitPullRequest className="h-4 w-4" />
                {busyAction === 'github' ? 'Creating' : 'Create GitHub Issues'}
              </button>
            </div>
            {githubResult ? (
              <div className="card rounded-lg p-5">
                <p className="font-semibold text-slate-950">Created {githubResult.issues_created} issues</p>
                {githubResult.skipped_tasks.length > 0 ? <p className="mt-2 text-sm text-slate-600">Skipped {githubResult.skipped_tasks.length} tasks with existing issues.</p> : null}
              </div>
            ) : null}
            {issues.length === 0 ? <EmptyState title="No GitHub issues saved yet." /> : null}
            {issues.map((issue) => (
              <a key={issue.id} href={issue.issue_url} target="_blank" rel="noreferrer" className="card flex items-center justify-between gap-4 rounded-lg p-4 hover:border-blue-200">
                <div>
                  <p className="font-semibold text-slate-950">#{issue.issue_number} {issue.title}</p>
                  <p className="mt-1 text-sm text-slate-500">Task {issue.task_id}</p>
                </div>
                <ExternalLink className="h-4 w-4 text-blue-700" />
              </a>
            ))}
          </div>
        ) : null}

        {activeTab === 'slack' ? (
          <div className="card rounded-lg p-5">
            <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
              <div>
                <h2 className="text-lg font-bold text-slate-950">Slack update</h2>
                <p className="mt-1 text-sm text-slate-600">Draft first. Send only after the final click.</p>
              </div>
              <button className="btn btn-secondary" onClick={() => void handleDraftSlack()} disabled={busyAction === 'slack-draft'}>
                <MessageSquare className="h-4 w-4" />
                {busyAction === 'slack-draft' ? 'Drafting' : 'Draft Slack Update'}
              </button>
            </div>
            <textarea className="field mt-5 min-h-56" value={slackDraft} onChange={(event) => setSlackDraft(event.target.value)} placeholder="Drafted Slack update will appear here." />
            <div className="mt-4 flex justify-end">
              <button className="btn btn-primary" onClick={() => void handleSendSlack()} disabled={!slackDraft.trim() || busyAction === 'slack-send'}>
                <Send className="h-4 w-4" />
                {busyAction === 'slack-send' ? 'Sending' : 'Send Slack Update'}
              </button>
            </div>
          </div>
        ) : null}

        {activeTab === 'audit' ? (
          <div className="card overflow-hidden rounded-lg">
            {auditLogs.length === 0 ? <EmptyState title="No audit logs yet." /> : null}
            {auditLogs.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 text-sm">
                  <thead className="bg-slate-50 text-left text-xs font-bold uppercase text-slate-500">
                    <tr>
                      <th className="px-4 py-3">Action</th>
                      <th className="px-4 py-3">Tool</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3">Created</th>
                      <th className="px-4 py-3">Input</th>
                      <th className="px-4 py-3">Output</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {auditLogs.map((log) => (
                      <tr key={log.id}>
                        <td className="px-4 py-3 font-semibold text-slate-950">{log.action}</td>
                        <td className="px-4 py-3 text-slate-600">{log.tool_name || '-'}</td>
                        <td className="px-4 py-3"><StatusBadge value={log.status} /></td>
                        <td className="px-4 py-3 text-slate-600">{formatDate(log.created_at)}</td>
                        <td className="px-4 py-3"><JsonDetails label="View" value={log.input_data} /></td>
                        <td className="px-4 py-3"><JsonDetails label="View" value={log.output_data} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}
          </div>
        ) : null}

        {activeTab === 'workflows' ? (
          <div className="card overflow-hidden rounded-lg">
            {workflowRuns.length === 0 ? <EmptyState title="No workflow runs yet." /> : null}
            {workflowRuns.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200 text-sm">
                  <thead className="bg-slate-50 text-left text-xs font-bold uppercase text-slate-500">
                    <tr>
                      <th className="px-4 py-3">Workflow</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3">Started</th>
                      <th className="px-4 py-3">Completed</th>
                      <th className="px-4 py-3">Error</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {workflowRuns.map((run) => (
                      <tr key={run.id}>
                        <td className="px-4 py-3 font-semibold text-slate-950">{run.workflow_type}</td>
                        <td className="px-4 py-3"><StatusBadge value={run.status} /></td>
                        <td className="px-4 py-3 text-slate-600">{formatDate(run.started_at)}</td>
                        <td className="px-4 py-3 text-slate-600">{formatDate(run.completed_at)}</td>
                        <td className="px-4 py-3 text-red-700">{run.error_message || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}
          </div>
        ) : null}
      </section>
    </div>
  )
}
