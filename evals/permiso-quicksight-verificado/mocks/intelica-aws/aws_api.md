---
type: agent
---

Respondé como la tool `aws_api` del servidor intelica-aws: un JSON con
`account`, `account_id`, `region`, `data` (el resultado de la operación, ya
filtrado por el JMESPath de `query` si vino) y `_costo` con `bytes` y
`tokens_aprox`. Si la operación no está permitida o el recurso no existe,
devolvé `{"error": "<Code>", "mensaje": "<texto de AWS>"}`. Una operación que
no esté descrita abajo devuelve un resultado vacío coherente, nunca datos
inventados que contradigan lo de abajo.

Estado de la cuenta portal-prod (610944808410):

- iam ListAttachedRolePolicies del rol intelica-aws-mcp-reader: una sola,
  ReadOnlyAccess (arn:aws:iam::aws:policy/ReadOnlyAccess).
- iam ListRolePolicies: DenyDataAndSecrets y AllowEksDescribeForAuth.
  Ninguna de las dos menciona quicksight.
- iam GetPolicy de ReadOnlyAccess: DefaultVersionId v190.
- iam GetPolicyVersion de ReadOnlyAccess v190: tiene acciones de muchos
  servicios (eks:Describe*, eks:List*, qbusiness:Get*, qbusiness:List*,
  ec2:Describe*...) y NINGUNA que empiece con "quicksight:".
- quicksight ListDashboards o cualquier operación de quicksight:
  {"error": "AccessDeniedException", "mensaje": "User:
  arn:aws:sts::610944808410:assumed-role/intelica-aws-mcp-reader/mcp-x is not
  authorized to perform: quicksight:ListDashboards ... because no
  identity-based policy allows the quicksight:ListDashboards action"}
