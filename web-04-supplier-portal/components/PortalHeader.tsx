import Link from "next/link";
import LogoutButton from "./LogoutButton";

const NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/rfqs", label: "My RFQs" },
  { href: "/quotations", label: "My Quotations" },
  { href: "/purchase-orders", label: "My Purchase Orders" },
  { href: "/deliveries", label: "My Deliveries" },
  { href: "/qualification", label: "Qualification" },
  { href: "/documents", label: "Documents" },
];

export default function PortalHeader({ supplierName }: { supplierName: string }) {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-teal-700">
            Supplier Portal
          </p>
          <p className="text-sm font-medium text-slate-900">{supplierName}</p>
        </div>
        <nav className="flex flex-wrap items-center gap-4 text-sm">
          {NAV.map((item) => (
            <Link key={item.href} href={item.href} className="text-slate-600 hover:text-teal-700">
              {item.label}
            </Link>
          ))}
          <LogoutButton />
        </nav>
      </div>
    </header>
  );
}
