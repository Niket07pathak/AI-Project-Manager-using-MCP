import { SignedIn, SignedOut, SignInButton, SignUpButton } from '@clerk/clerk-react'
import { ArrowRight, Bot, FileSearch, GitPullRequest, ListChecks, MessageSquare, ShieldCheck } from 'lucide-react'
import { Link } from 'react-router-dom'

const features = [
  {
    title: 'Document RAG',
    description: 'Upload PRDs, process them into chunks, and search project context through the backend RAG flow.',
    icon: FileSearch,
  },
  {
    title: 'LangGraph task generation',
    description: 'Turn project context into implementation tasks through the LangGraph project analyzer.',
    icon: Bot,
  },
  {
    title: 'Approval-gated GitHub issues',
    description: 'Review, edit, approve, and only then create GitHub issues from approved tasks.',
    icon: GitPullRequest,
  },
  {
    title: 'Slack updates',
    description: 'Draft a project update first, then send it to the configured Slack channel when ready.',
    icon: MessageSquare,
  },
  {
    title: 'Audit logs',
    description: 'Inspect tool actions, inputs, outputs, and workflow outcomes from one project view.',
    icon: ShieldCheck,
  },
]

export function LandingPage() {
  return (
    <div className="relative overflow-hidden">
      <section className="bg-[linear-gradient(135deg,#eff6ff_0%,#ffffff_44%,#ecfeff_100%)]">
        <div className="mx-auto grid min-h-[calc(100vh-4rem)] max-w-7xl items-center gap-12 px-4 py-16 sm:px-6 lg:grid-cols-[1.05fr_0.95fr] lg:px-8">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-blue-200 bg-white px-3 py-1 text-sm font-semibold text-blue-700 shadow-sm">
              <ListChecks className="h-4 w-4" />
              PRD {'->'} RAG {'->'} LangGraph {'->'} MCP {'->'} GitHub and Slack
            </div>
            <h1 className="mt-6 max-w-4xl text-5xl font-black tracking-normal text-slate-950 sm:text-6xl lg:text-7xl">
              AI Project Manager using MCP
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">
              A production-style command center for taking requirements from uploaded documents into searchable RAG
              context, LangGraph-generated tasks, approval-gated GitHub issues, Slack updates, audit logs, and workflow
              visibility.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <SignedOut>
                <SignInButton mode="modal">
                  <button className="btn btn-primary">
                    Sign in
                    <ArrowRight className="h-4 w-4" />
                  </button>
                </SignInButton>
                <SignUpButton mode="modal">
                  <button className="btn btn-secondary">Create account</button>
                </SignUpButton>
              </SignedOut>
              <SignedIn>
                <Link to="/dashboard" className="btn btn-primary">
                  Open dashboard
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </SignedIn>
            </div>
          </div>

          <div className="glass-panel rounded-lg p-4">
            <div className="rounded-lg border border-slate-200 bg-slate-950 p-4 text-white">
              <div className="flex items-center justify-between border-b border-white/10 pb-4">
                <div>
                  <p className="text-sm text-slate-400">Workflow preview</p>
                  <p className="font-semibold">Project launch pipeline</p>
                </div>
                <span className="rounded-full bg-emerald-400/15 px-3 py-1 text-xs font-semibold text-emerald-300">
                  ready
                </span>
              </div>
              <div className="mt-4 space-y-3">
                {['Upload PRD', 'Process chunks', 'Analyze project', 'Approve tasks', 'Create issues', 'Send update'].map(
                  (step, index) => (
                    <div key={step} className="flex items-center gap-3 rounded-lg bg-white/6 p-3">
                      <span className="flex h-7 w-7 items-center justify-center rounded-full bg-blue-500 text-xs font-bold">
                        {index + 1}
                      </span>
                      <span className="text-sm font-medium">{step}</span>
                    </div>
                  ),
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="border-t border-slate-200 bg-white py-14">
        <div className="mx-auto grid max-w-7xl gap-4 px-4 sm:grid-cols-2 sm:px-6 lg:grid-cols-5 lg:px-8">
          {features.map((feature) => (
            <article key={feature.title} className="card rounded-lg p-5">
              <feature.icon className="h-6 w-6 text-blue-600" />
              <h2 className="mt-4 text-base font-bold text-slate-950">{feature.title}</h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">{feature.description}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  )
}
