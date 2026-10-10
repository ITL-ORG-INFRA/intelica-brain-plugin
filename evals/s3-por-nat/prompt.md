---
name: s3-por-nat
description: Encuentra la tabla de rutas sin el endpoint de S3, verifica que el tráfico del NAT es S3 y entrega el cambio sin aplicarlo
tags: [smith]
max_turns: 8
timeout_seconds: 1500
allowed_tools: [Agent]
---

Usá el subagente intelica-arca:smith: el NAT Gateway de portal-prod nos
parece caro. Revisalo buscando ahorro.
