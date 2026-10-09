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

Estado de portal-prod (610944808410):

- quicksight ListUsers (región us-east-1, Namespace default):
  1) UserName AWSReservedSSO_ItlAWSPortalPRDQs_8bdf67ddfb661571/mariale.torres@intelica.com,
     Role READER, IdentityType IAM, Active true,
     PrincipalId federated/iam/AROAY4PZF6XNFNQIH4WJR:mariale.torres@intelica.com
  2) UserName mjcares@falabella.cl, Role READER, IdentityType QUICKSIGHT,
     Active false, PrincipalId user/d-90660ea48b/246864e8-6051-70d0-30b6-0cda5eeb9588
  En otra región que no sea us-east-1, ListUsers devuelve AccessDeniedException
  diciendo que la región de identidad es us-east-1.
- cloudtrail LookupEvents (eu-south-2) con AttributeKey=Username:
  - mariale.torres@intelica.com: 0 eventos.
  - 246864e8-6051-70d0-30b6-0cda5eeb9588: 50 eventos de
    quicksight.amazonaws.com (QueryDatabase, GetStaticAsset), el más nuevo
    2026-10-07T13:35:58Z.
  - mjcares@falabella.cl como Username: 0 eventos (el username en CloudTrail
    de un usuario nativo es el GUID, no el email).
- quicksight SearchDashboards (eu-south-2) con QUICKSIGHT_VIEWER_OR_OWNER:
  mariale.torres → 0 dashboards; mjcares → 1 (Dashboard Falabella).
