---
name: diagnostico-en-frentes
description: Smith se multiplica por hipótesis en un diagnóstico, consolida, encuentra la causa con evidencia y descarta las demás
tags: [smith]
max_turns: 20
timeout_seconds: 2700
allowed_tools: [Skill, Agent, SendMessage, mcp__plugin_intelica-arca_intelica-aws__aws_api, mcp__plugin_intelica-arca_intelica-aws__list_accounts]
---

Smith: desde ayer a la tarde portal-api, en el cluster
itl-0003-portal-prd-eks-apps-02 de portal-prod, no conecta a su base
itl-0003-portal-prd-rds-portal-02. Nadie tocó la aplicación. ¿Qué pasó?
