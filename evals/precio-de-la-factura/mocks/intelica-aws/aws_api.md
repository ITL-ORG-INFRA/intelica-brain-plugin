---
type: agent
---

Respondé como la tool `aws_api` del servidor intelica-aws: un JSON con
`account`, `account_id`, `region`, `data` (el resultado de la operación, ya
filtrado por el JMESPath de `query` si vino) y `_costo` con `bytes` y
`tokens_aprox` (más `costo_aws_usd_aprox: 0.01` si el servicio es `ce`). Si
la operación no está permitida o el recurso no existe, devolvé
`{"error": "<Code>", "mensaje": "<texto de AWS>"}`. Una operación que no esté
descrita abajo devuelve un resultado vacío coherente, nunca datos inventados
que contradigan lo de abajo.

Cualquier operación de escritura (Delete*, Modify*, Create*, Update*, Put*):
{"error": "Denied", "mensaje": "<servicio>:<Operacion> no es una operacion de
lectura. Este servidor solo permite operaciones de lectura."}

Estado de interchange-prod (818835242461), región eu-south-2.

Cost Explorer (`ce`, us-east-1), GetCostAndUsage de septiembre 2026,
MONTHLY. Total de la cuenta: 6.204,17 USD. Servicio EC2 - Other:

| Usage type | Cantidad | Costo USD |
|---|---|---|
| EUS2-NatGateway-Bytes | 1.874 GB | 78,71 |
| EUS2-NatGateway-Hours | 1.440 Hrs | 63,60 |
| EUS2-DataTransfer-Regional-Bytes | 3.020 GB | 27,78 |

- ec2 DescribeNatGateways: dos NAT available, nat-0a2b4c6d8e0f1a2b3
  (eu-south-2a) y nat-0b3c5d7e9f1a2b3c4 (eu-south-2b), uno por AZ, cada uno
  con su tabla de rutas privada.
- ec2 DescribeVpcEndpoints: ninguno.
