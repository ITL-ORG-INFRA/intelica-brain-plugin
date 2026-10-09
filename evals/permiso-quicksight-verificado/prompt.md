---
name: permiso-quicksight-verificado
description: Afirma un permiso solo despues de verificarlo, no por lo que parece incluir ReadOnlyAccess
tags: [cerebro]
max_turns: 8
timeout_seconds: 900
allowed_tools: [Agent]
---

Usá el subagente intelica-arca:cerebro para responder: ¿el rol
intelica-aws-mcp-reader de portal-prod tiene permiso para listar los
dashboards de QuickSight? Necesito un sí o un no con la evidencia.
