export default function SiteFooter({
  companyName,
  country,
}: {
  companyName: string;
  country: string;
}) {
  return (
    <footer className="mt-auto border-t border-stone-200 bg-stone-100">
      <div className="mx-auto max-w-5xl px-6 py-8 text-sm text-stone-500 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <p>
          &copy; {new Date().getFullYear()} {companyName}. Demo brand site — WEB-02
          (Enterprise Platform Phase 7).
        </p>
        <p>{country}</p>
      </div>
    </footer>
  );
}
