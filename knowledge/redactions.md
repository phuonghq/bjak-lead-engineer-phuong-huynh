# Redactions and excluded sources

## Wrong LinkedIn was removed

`knowledge/sources/linkedin.md` was deleted. It was built from https://www.linkedin.com/in/phuonghd (Startech AI / Grove & Dean / NashTech / UNIVINA / FPT, GitHub phuonghd, Qdrant, Keycloak-as-this-person's-job). That is another person's public profile. Keeping it is the same failure class as fabricating an employer.

Every Startech, Grove & Dean, UNIVINA, NashTech, FPT, Qdrant, Keycloak-as-employment, and phuonghd fact that came from that scrape is gone from `cv.md`, `projects.md`, `working-style.md`, and `facts.yaml`.

## Candidate LinkedIn deliberately not ingested

The candidate's real profile is https://www.linkedin.com/in/phuong-huynh-510b54124/. They do not actively use LinkedIn and asked that it be removed from the assistant. It was not scraped and is not in this corpus. Do not add it later without an explicit request.

## Redacted from the CV (PII)

The August 2026 docx header contained a neighborhood-level address, a personal email, and a WhatsApp/Zalo phone number. Those are not in committed files. Work locations on the employment record (Singapore, Vietnam, Ho Chi Minh City) were kept.

The docx itself is not committed. The in-repo source of truth is `knowledge/sources/cv.md`.

## Not in this repo

- No LinkedIn source of any kind.
- No local IdeaProjects code was ingested as professional experience.
- No GitHub repositories were ingested as authored projects.

## Synthetic

None. Every employer, title, date, and project bullet is traceable to PHUONG HUYNH_8.2026.docx. If a sentence cannot be traced, it should not be in `knowledge/sources/`.
