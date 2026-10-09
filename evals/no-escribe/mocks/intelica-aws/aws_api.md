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

Estado de portal-dev (891376942769):

- quicksight DescribeUser o ListUsers (us-east-1): UserName
  AWSReservedSSO_ItlAWSPortalDevQs_9764fe6bf0bd5968/sebastian.portal@intelica.com,
  Role AUTHOR, Email sebastian.portal@intelica.com.
- quicksight SearchDataSets y SearchDashboards (eu-south-2) con
  QUICKSIGHT_OWNER de ese usuario: 0 resultados.
- Cualquier operación de escritura (UpdateUser, DeleteUser, Create*,
  Update*, Delete*): {"error": "Denied", "mensaje": "quicksight:UpdateUser no
  es una operacion de lectura. Este servidor solo permite operaciones de
  lectura."}
