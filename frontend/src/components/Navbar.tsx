import { SignedIn, SignedOut, SignInButton, SignUpButton, UserButton } from '@clerk/clerk-react'
import { BrainCircuit, LayoutDashboard, Plus } from 'lucide-react'
import { NavLink, Link } from 'react-router-dom'

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  `inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold transition ${
    isActive ? 'bg-blue-50 text-blue-700' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-950'
  }`

export function Navbar() {
  return (
    <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/85 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link to="/" className="flex items-center gap-3">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600 text-white">
            <BrainCircuit className="h-5 w-5" />
          </span>
          <span className="text-sm font-black tracking-normal text-slate-950 sm:text-base">
            AI Project Manager
          </span>
        </Link>

        <nav className="hidden items-center gap-1 md:flex">
          <SignedIn>
            <NavLink to="/dashboard" className={navLinkClass}>
              <LayoutDashboard className="h-4 w-4" />
              Dashboard
            </NavLink>
            <NavLink to="/projects/new" className={navLinkClass}>
              <Plus className="h-4 w-4" />
              Create Project
            </NavLink>
          </SignedIn>
        </nav>

        <div className="flex items-center gap-2">
          <SignedOut>
            <SignInButton mode="modal">
              <button className="btn btn-secondary">Sign in</button>
            </SignInButton>
            <SignUpButton mode="modal">
              <button className="btn btn-primary">Sign up</button>
            </SignUpButton>
          </SignedOut>
          <SignedIn>
            <div className="md:hidden">
              <Link to="/projects/new" className="btn btn-primary">
                <Plus className="h-4 w-4" />
              </Link>
            </div>
            <UserButton afterSignOutUrl="/" />
          </SignedIn>
        </div>
      </div>
    </header>
  )
}
