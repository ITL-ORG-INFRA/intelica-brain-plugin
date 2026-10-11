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

Estado de portal-prod (610944808410), región eu-south-2.

Cost Explorer (`ce`, us-east-1), GetCostAndUsage de septiembre 2026,
MONTHLY, servicio EC2 - Other, usage types de EBS:

| Usage type | Cantidad | Costo USD |
|---|---|---|
| EUS2-EBS:VolumeUsage.gp2 | 1.000 GB-Mo | 115,00 |
| EUS2-EBS:VolumeUsage.gp3 | 4.100 GB-Mo | 377,20 |
| EUS2-EBS:VolumeP-Throughput.gp3 | 0 | 0,00 |

ec2 DescribeVolumes con Filters volume-type=gp2: tres volúmenes, todos
in-use.

- vol-0a3f5c7e9b1d2f406, 500 GiB, adjunto a i-0016a8bc9ee8b94c7 (DENVER).
  Tags: Name=itl-0003-portal-prd-ebs-denver-data-02, Module=ec2-denver,
  ManagedBy=terraform, Repository=portal-infra.
- vol-0b4e6d8f0a2c3e517, 200 GiB, adjunto a i-0e5a7c9b1d3f5a628
  (itl-0003-portal-prd-ec2-airflow-02). Tags:
  Name=itl-0003-portal-prd-ebs-airflow-02, Module=ec2-airflow,
  ManagedBy=terraform, Repository=portal-infra.
- vol-0c5f7e9a1b3d4f628, 300 GiB, adjunto a i-0f6b8d0c2e4a6b739 (Name=jump-temporal).
  Sin más tags.

CloudWatch AWS/EBS, últimos 14 días:

- vol-0a3f5c7e9b1d2f406: VolumeWriteBytes llega a ~180 MiB/s durante unos
  10 minutos todos los días a las 18:00 UTC; el resto del día por debajo de
  10 MiB/s. IOPS máximo ~1.100.
- vol-0b4e6d8f0a2c3e517: por debajo de 20 MiB/s e ~300 IOPS todo el tiempo.
- vol-0c5f7e9a1b3d4f628: prácticamente sin actividad.
