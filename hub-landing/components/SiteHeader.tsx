import Link from "next/link";

export default function SiteHeader() {
  return (
    <header className="border-b border-slate-200 bg-white/90 backdrop-blur sticky top-0 z-10">
      <div className="mx-auto max-w-6xl px-6 py-4 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 group">
          <span className="flex h-9 w-9 items-center justify-center rounded-md bg-slate-900 text-white font-semibold">
            E
          </span>
          <span className="font-semibold text-slate-900 group-hover:text-slate-700 transition-colors">
            ENTERPRISE_PLATFORM
          </span>
        </Link>
        <nav className="flex items-center gap-6 text-sm font-medium text-slate-600">
          <Link href="/" className="hover:text-slate-900 transition-colors">
            Home
          </Link>
          <Link href="/solutions" className="hover:text-slate-900 transition-colors">
            Industries &amp; Solutions
          </Link>
          <Link href="/about" className="hover:text-slate-900 transition-colors">
            About
          </Link>
        </nav>
      </div>
    </header>
  );
}
