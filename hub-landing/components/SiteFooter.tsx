export default function SiteFooter() {
  return (
    <footer className="mt-auto border-t border-slate-200 bg-slate-50">
      <div className="mx-auto max-w-6xl px-6 py-8 text-sm text-slate-500 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <p>
          &copy; {new Date().getFullYear()} ENTERPRISE_PLATFORM. Demonstration platform —
          Platform Hub (user-requested, Enterprise Platform Phase 7).
        </p>
        <p>Built on Frappe/ERPNext v16.36.0</p>
      </div>
    </footer>
  );
}
