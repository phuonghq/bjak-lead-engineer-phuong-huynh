---
id: projects
type: projects
as_of: 2026-08
provenance: Project names and bullets copied from PHUONG HUYNH_8.2026.docx only. Not a separate portfolio. Nothing was added that the CV did not state.
---

# Projects (from the CV)

## Supply Platform (Agoda)

Supplier onboarding & platform services. Optimized SQL Server hot-path queries for high-volume onboarding APIs, reducing database CPU utilization by 25% and improving API throughput by 2x. Built observability for Scala microservices using Prometheus/Micrometer and Grafana with SLO alerts in Slack. Implemented rate limiting and circuit breakers. Delivered compliance-grade audit trails and real-time supplier notification pipelines handling millions of system events daily.

## Rewards Platform (NCS)

Loyalty campaign platform across Kafka consumers and scheduled jobs, with correctness guarantees for at-least-once delivery (idempotency, replay safety, and multi-topic concurrency models). Re-architected acknowledgment and retry strategy. Cross-pod, per-user serialization using distributed locks and database safety nets. Observability dashboards with Prometheus + ELK. Tuned Kubernetes Horizontal Pod Autoscaler (HPA).

## AliPay Integration for Lazada / DARAZ (Alibaba Group)

AliPay integration for Lazada / DARAZ across 6 SEA markets. Core payment APIs: createOrder, queryBalance, payment, refund. Retry and idempotency for timeouts and network replays. Complex transaction states and asynchronous settlement workflows for third-party payment integration and eventual consistency.

## Distributed Resident-Service Platform (VinID)

Distributed backend services for resident-service platforms and operational workflows, scaled to hundreds of thousands of daily active users. ChatOps via Slack-based operational notifications. Kubernetes deployments, Helm chart management, and production environment configurations.

## Crypto Exchange Platform (Quoine)

High-security exchange APIs and operational tooling for KYC, automated risk rating, and maker-checker approval flows for financial deposits and withdrawals. Reconciliation of internal subledger balances against on-chain blockchain states. Asynchronous settlement and tamper-proof audit-trail workflows for digital wallet processing.
