import Link from "next/link";
import LogoutButton from "./LogoutButton";

const NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/orders", label: "My Orders" },
  { href: "/visits", label: "Technical Visits" },
  { href: "/recommendations", label: "Recommendations" },
  { href: "/history", label: "Service History" },
];

export default function PortalHeader({ customerName }: { customerName: string }) {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 px-4 py-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
            Farm Portal
          </p>
          <p className="text-sm font-medium text-slate-900">{customerName}</p>
        </div>
        <nav className="flex flex-wrap items-center gap-4 text-sm">
          {NAV.map((item) => (
            <Link key={item.href} href={item.href} className="text-slate-600 hover:text-emerald-700">
              {item.label}
            </Link>
          ))}
          <LogoutButton />
        </nav>
      </div>
    </header>
  );
}
