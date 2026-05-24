import { useAuth } from '@clerk/clerk-react'
import { Activity, FolderKanban, Plus, Workflow } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { EmptyState } from '../components/EmptyState'
import { ErrorState } from '../components/ErrorState'
import { LoadingState } from '../components/LoadingState'
import { StatusBadge } from '../components/StatusBadge'
import type { Project } from '../types/api'

export function DashboardPage() {
  const { getToken } = useAuth()
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadProjects = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.listProjects(getToken)
      setProjects(Array.isArray(data) ? data : [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load projects')
    } finally {
      setLoading(false)
    }
  }, [getToken])

  useEffect(() => {
    void loadProjects()
  }, [loadProjects])

  const stats = useMemo(() => {
    const active = projects.filter((project) => project.status !== 'completed').length
    const configured = projects.filter((project) => project.github_repo_name || project.slack_channel_name).length
    return [
      { label: 'Total projects', value: projects.length, icon: FolderKanban },
      { label: 'Active projects', value: active, icon: Activity },
      { label: 'Configured workflows', value: configured, icon: Workflow },
    ]
  }, [projects])

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm font-semibold text-blue-700">Dashboard</p>
          <h1 className="mt-2 text-3xl font-black text-slate-950">Project command center</h1>
          <p className="mt-2 text-slate-600">Create projects, connect tools, and drive the full MCP workflow.</p>
        </div>
        <Link to="/projects/new" className="btn btn-primary">
          <Plus className="h-4 w-4" />
          Create project
        </Link>
      </div>

      <div className="mt-8 grid gap-4 md:grid-cols-3">
        {stats.map((stat) => (
          <div key={stat.label} className="card rounded-lg p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">{stat.label}</p>
                <p className="mt-2 text-3xl font-black text-slate-950">{stat.value}</p>
              </div>
              <span className="flex h-11 w-11 items-center justify-center rounded-lg bg-blue-50 text-blue-700">
                <stat.icon className="h-5 w-5" />
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8">
        {loading ? <LoadingState label="Loading projects" /> : null}
        {error ? <ErrorState message={error} onRetry={loadProjects} /> : null}
        {!loading && !error && projects.length === 0 ? (
          <EmptyState
            icon={FolderKanban}
            title="No projects yet"
            description="Create your first project and connect a GitHub repo or Slack channel when you are ready."
            action={
              <Link to="/projects/new" className="btn btn-primary">
                <Plus className="h-4 w-4" />
                Create project
              </Link>
            }
          />
        ) : null}

        {!loading && !error && projects.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {projects.map((project) => (
              <Link
                key={project.id}
                to={`/projects/${project.id}`}
                className="card rounded-lg p-5 transition hover:-translate-y-0.5 hover:border-blue-200 hover:shadow-lg"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <h2 className="truncate text-lg font-bold text-slate-950">{project.name}</h2>
                    <p className="mt-2 line-clamp-3 min-h-12 text-sm leading-6 text-slate-600">
                      {project.description || 'No description yet.'}
                    </p>
                  </div>
                  <StatusBadge value={project.status} />
                </div>
                <div className="mt-5 space-y-2 text-sm text-slate-600">
                  <p>
                    <span className="font-semibold text-slate-900">GitHub:</span>{' '}
                    {project.github_repo_owner && project.github_repo_name
                      ? `${project.github_repo_owner}/${project.github_repo_name}`
                      : 'Not configured'}
                  </p>
                  <p>
                    <span className="font-semibold text-slate-900">Slack:</span>{' '}
                    {project.slack_channel_name || 'Not configured'}
                  </p>
                </div>
              </Link>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  )
}
