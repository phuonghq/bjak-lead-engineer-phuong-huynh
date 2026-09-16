---
id: cv
type: cv
as_of: 2026-08
provenance: Converted from the candidate CV file PHUONG HUYNH_8.2026.docx (August 2026). The docx is not committed. Phone, email, WhatsApp/Zalo contact, and neighborhood-level address were redacted. No employers, titles, or dates were added beyond that file.
---

# Phuong Huynh

## Summary

Senior Software Engineer with 8+ years of experience building high-throughput, distributed backend systems for fintech, payments, loyalty/rewards platforms across Southeast Asia. Experienced in event-driven architectures (Kafka), transactional correctness (idempotency, concurrency control) and observability. Latest role is Senior Software Engineer at Agoda from 07/2023 (end date blank).

## Senior Software Engineer — Agoda

Singapore | 07/2023 –

Supply Platform (Supplier onboarding & platform services)

- Optimized SQL Server hot-path queries for high-volume onboarding APIs, reducing database CPU utilization by 25% and improving API throughput by 2x.
- Built comprehensive observability for Scala microservices using Prometheus/Micrometer and Grafana, establishing critical SLO alerts integrated directly into Slack.
- Implemented resilient traffic-management patterns, including rate limiting and circuit breakers, preventing cascading failures across downstream partner services.
- Delivered compliance-grade audit trails and real-time supplier notification pipelines handling millions of system events daily.

## Senior Software Engineer — NCS

Singapore | 06/2022 – 06/2023

Rewards Platform

- Technically owned the loyalty campaign platform across Kafka consumers and scheduled jobs, defining strict correctness guarantees for at-least-once delivery (idempotency, replay safety, and multi-topic concurrency models).
- Improved consumer resilience and eliminated batch-stall behaviors by re-architecting the acknowledgment and retry strategy, ensuring predictable recovery under partial failures.
- Designed a cross-pod, per-user serialization mechanism using distributed locks and database safety nets, preventing duplicate mission states and eliminating race conditions.
- Built and operated end-to-end observability dashboards using Prometheus + ELK to monitor consumer lag, throughput, and error rates, reducing incident triage time by 40%.
- Tuned Kubernetes Horizontal Pod Autoscaler (HPA)
- Mentored engineers through technical training, code reviews, and pair programming, knowledge sharing.

## Senior Software Engineer — Alibaba Group

Vietnam | 03/2021 – 06/2022

AliPay Integration for Lazada / DARAZ (6 SEA markets)

- Designed and integrated core payment APIs (createOrder, queryBalance, payment, refund) across 6 Southeast Asian markets, handling high-TPS transaction volumes.
- Implemented strict retry and idempotency patterns for timeouts and network replays, reducing duplicate-processing risks and financial discrepancies to zero in core payment flows.
- Modeled complex transaction states and asynchronous settlement workflows to ensure seamless third-party payment integration and eventual consistency.
- Collaborated with cross-functional teams to translate business requirements into technical roadmaps.

## Backend Developer — VinID

Vietnam | 07/2019 – 03/2021

Distributed Resident-Service Platform

- Built distributed backend services supporting resident-service platforms and operational workflows, successfully scaling the system to support hundreds of thousands of daily active users.
- Implemented ChatOps automation via Slack-based operational notifications and automated service-monitoring integrations to accelerate infrastructure alerting.
- Supported Kubernetes deployments, Helm chart management, and production environment configurations.

## Software Engineer — Quoine

Vietnam | 10/2017 – 07/2019

Crypto Exchange Platform

- Implemented high-security exchange APIs and operational tooling for KYC, automated risk rating, and maker-checker approval flows for financial deposits and withdrawals.
- Built robust reconciliation systems validating internal subledger balances against on-chain blockchain states to ensure absolute custody integrity.
- Delivered asynchronous settlement and tamper-proof audit-trail workflows for operationally sensitive digital wallet processing.
- Promoted to Mid-level Engineer (03/2019)

## Skills

- Languages: Java 21, Scala, Ruby, Node.js
- Backend: Spring Boot, Spring Cloud, Spring Batch, Akka, Ruby on Rails
- Data & Databases: Redis, MongoDB, Elasticsearch, PostgreSQL, MySQL/MariaDB, SQL Server, BigQuery
- Messaging & Event-Driven: Kafka, RabbitMQ
- Infrastructure: Docker, Kubernetes, AWS, GCP, OpenShift
- Observability: Prometheus, Grafana, ELK Stack, New Relic, ES
- CI/CD: GitHub Actions, GitLab CI, Jenkins, CircleCI

## Education

Degree: B.S.E. in Computer Science & Engineering (studied at HCM University of Technology (VNU), Ho Chi Minh City). 09/2013 – 12/2017. GPA: 8.14 / 10.
