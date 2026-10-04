Before modifying this repository:

1. Read `documents/productization/00_demo_platform_master_plan.md`.
2. Read `documents/project_status.md`.
3. Read only the business-flow documents relevant to the current task.
4. Search existing code before creating new DocTypes/modules.
5. Do not modify the ENLIE runtime stack (`D:\ME\ERP_ENLIE\`) for demo-platform tasks. It is reference-only and may be under active concurrent development by another session.
6. Do not copy ENLIE production data into public demos.
7. Keep Frappe/ERPNext as the default business core.
8. Add Next.js only for justified UX use cases.
9. Add NestJS only for justified integration/service use cases.
10. All AI calls must go through the provider-agnostic AI Gateway.
11. Update relevant documentation and `project_status.md` after each task.
12. Distinguish CODE COMPLETE, MIGRATED, TESTED and DEMO READY — never mark a task `DONE`.

## Known name collision — read before touching anything called "Pharmacountry"

Two unrelated codebases use the name "Pharmacountry":
- `D:\ME\ERP_ENLIE\vnpharma-develop\pharmacountry\` — the actual Frappe/ERPNext app this master plan is about.
- `D:\ME\Pharmacountry\`, `D:\ME\Quantri-pharmacountry\`, `D:\ME\ERP_ENLIE\pharmacountry_be\/_fe\/_db\` — an unrelated NestJS+Next.js B2B pharma-company directory/marketplace product. Out of scope here.

Do not assume a file or folder is in scope just because it has "pharmacountry" in its name.

## Where the reference ERP code actually lives

The custom Frappe app is **not** inside this repo yet. It lives at `D:\ME\ERP_ENLIE\vnpharma-develop\pharmacountry\` (git repo, branch `main`, actively developed). A stale predecessor exists at `D:\ME\ERP_ENLIE\vnpharma\vnpharma\` (branch `develop`) — treat as legacy, do not audit both as if current. See `documents/productization/01_productization_audit.md` §0 for full detail and §7 for open decisions on how/when ENLIE code should cross into this repo.
