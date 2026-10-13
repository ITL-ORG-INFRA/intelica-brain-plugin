---
name: guardduty-triaje
description: Decide si cada alerta de GuardDuty es brecha o falso positivo, con el dato que lo decide, y propone la contención sin aplicarla
tags: [seraph]
max_turns: 16
timeout_seconds: 1200
allowed_tools: [Agent]
---

Usá el subagente intelica-arca:seraph en modo triaje de GuardDuty: revisá
los findings activos 1a2b3c4d5e6f00000000000000000001 y
1a2b3c4d5e6f00000000000000000002 del detector
0de7ec70ra0000000000000000eva1 de la cuenta audit (eu-south-2) y decime
si son una brecha o un falso positivo.
