import Link from "next/link";
import LogoutButton from "./LogoutButton";

const NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/catalog", label: "Catalog & Stock" },
  { href: "/orders", label: "My Orders" },
  { href: "/invoices", label: "My Invoices" },
  { href: "/debt", label: "My Debt" },
  { href: "/returns", label: "Returns" },
];

export default function PortalHeader({ customerName }: { customerName: string }) {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 px-4 py-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">
            Dealer Portal
          </p>
          <p className="text-sm font-medium text-slate-900">{customerName}</p>
        </div>
        <nav className="flex flex-wrap items-center gap-4 text-sm">
          {NAV.map((item) => (
            <Link key={item.href} href={item.href} className="text-slate-600 hover:text-indigo-600">
              {item.label}
            </Link>
          ))}
          <LogoutButton />
        </nav>
      </div>
    </header>
  );
}
