# Conflicts and gaps

The assistant does not pick a winner when sources disagree or a field is missing. Retrieval returns what is written. The prompt tells the model to report the claims and cite them. The post-gate does not fill in blanks.

## Real gap: Agoda has no end date

**What is missing**

- `cv#senior-software-engineer-agoda` lists **Senior Software Engineer — Agoda**, Singapore, **07/2023 –** with a blank after the dash.
- The CV does **not** say "Present", "current", or an end month.
- `facts#role-0` records `end: unspecified` for that reason. It is not a second source; it is the same blank, structured.

**Why it exists**

This is the August 2026 CV (`PHUONG HUYNH_8.2026.docx`). Every other role has both a start and an end. Agoda is the only open-ended line. A recruiter may read the trailing dash as "to present". That reading is an inference, not a sentence on the page.

**What the system does**

On a question about current employer, whether they still work at Agoda, or when they left Agoda:

1. Fact lookup hits the Agoda row (`end: unspecified`).
2. BM25 also pulls `cv#senior-software-engineer-agoda`.
3. The model is instructed: report what is written, cite it, do not invent "Present" or an end date.
4. "When did Phuong leave Agoda?" is unanswerable and must refuse. "Who is the latest listed employer?" can name Agoda and the 07/2023 start, and must not upgrade the blank into a confirmed current job.

There is no LinkedIn-vs-CV conflict in this corpus. LinkedIn is not a source.

## Other gaps (not conflicts)

- The NCS bullet "Tuned Kubernetes Horizontal Pod Autoscaler (HPA)" is truncated. No outcome, scale, or configuration is given. The system must not invent one.
- Three roles share the title Senior Software Engineer (Agoda, NCS, Alibaba Group). An underspecified "what did you do as a senior engineer?" must not collapse them into one job.
- Quoine is headed **Software Engineer** (10/2017 – 07/2019) and also states **Promoted to Mid-level Engineer (03/2019)**. "What was the title at Quoine?" should cover both wordings, not pick one.
- Adjacent month boundaries (Quoine/VinID 07/2019, VinID/Alibaba 03/2021, Alibaba/NCS 06/2022) are not date overlaps.
- No source states salary, visa status, headcount of direct reports, performance ratings, or a reason for leaving any employer. Those questions must refuse.
