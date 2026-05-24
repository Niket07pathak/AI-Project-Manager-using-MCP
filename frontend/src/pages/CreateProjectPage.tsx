import { useAuth } from '@clerk/clerk-react'
import { ArrowLeft, Save } from 'lucide-react'
import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { ErrorState } from '../components/ErrorState'

const initialForm = {
  name: '',
  description: '',
  github_repo_owner: '',
  github_repo_name: '',
  slack_channel_id: '',
  slack_channel_name: '',
}

export function CreateProjectPage() {
  const { getToken } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState(initialForm)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const updateField = (field: keyof typeof initialForm, value: string) => {
    setForm((current) => ({ ...current, [field]: value }))
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSaving(true)
    setError(null)
    try {
      const project = await api.createProject(
        {
          name: form.name,
          description: form.description || null,
          github_repo_owner: form.github_repo_owner || null,
          github_repo_name: form.github_repo_name || null,
          slack_channel_id: form.slack_channel_id || null,
          slack_channel_name: form.slack_channel_name || null,
        },
        getToken,
      )
      navigate(`/projects/${project.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create project')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
      <Link to="/dashboard" className="inline-flex items-center gap-2 text-sm font-semibold text-slate-600 hover:text-slate-950">
        <ArrowLeft className="h-4 w-4" />
        Back to dashboard
      </Link>

      <div className="mt-6">
        <p className="text-sm font-semibold text-blue-700">New project</p>
        <h1 className="mt-2 text-3xl font-black text-slate-950">Create an MCP workflow project</h1>
        <p className="mt-2 text-slate-600">Configure optional GitHub and Slack destinations up front.</p>
      </div>

      <form onSubmit={handleSubmit} className="card mt-8 rounded-lg p-6">
        {error ? <ErrorState message={error} /> : null}

        <div className="grid gap-5 md:grid-cols-2">
          <label className="md:col-span-2">
            <span className="text-sm font-semibold text-slate-700">Name</span>
            <input
              className="field mt-1"
              required
              value={form.name}
              onChange={(event) => updateField('name', event.target.value)}
              placeholder="AI Project Manager launch"
            />
          </label>
          <label className="md:col-span-2">
            <span className="text-sm font-semibold text-slate-700">Description</span>
            <textarea
              className="field mt-1 min-h-28"
              value={form.description}
              onChange={(event) => updateField('description', event.target.value)}
              placeholder="Upload a PRD, generate tasks, approve work, create GitHub issues, and notify Slack."
            />
          </label>
          <label>
            <span className="text-sm font-semibold text-slate-700">GitHub repo owner</span>
            <input
              className="field mt-1"
              value={form.github_repo_owner}
              onChange={(event) => updateField('github_repo_owner', event.target.value)}
              placeholder="Niket07pathak"
            />
          </label>
          <label>
            <span className="text-sm font-semibold text-slate-700">GitHub repo name</span>
            <input
              className="field mt-1"
              value={form.github_repo_name}
              onChange={(event) => updateField('github_repo_name', event.target.value)}
              placeholder="Test-mcp-repo"
            />
          </label>
          <label>
            <span className="text-sm font-semibold text-slate-700">Slack channel ID</span>
            <input
              className="field mt-1"
              value={form.slack_channel_id}
              onChange={(event) => updateField('slack_channel_id', event.target.value)}
              placeholder="C0B4PFF7R8R"
            />
          </label>
          <label>
            <span className="text-sm font-semibold text-slate-700">Slack channel name</span>
            <input
              className="field mt-1"
              value={form.slack_channel_name}
              onChange={(event) => updateField('slack_channel_name', event.target.value)}
              placeholder="test-mcp-messages"
            />
          </label>
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <Link to="/dashboard" className="btn btn-secondary">
            Cancel
          </Link>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            <Save className="h-4 w-4" />
            {saving ? 'Creating' : 'Create project'}
          </button>
        </div>
      </form>
    </div>
  )
}
