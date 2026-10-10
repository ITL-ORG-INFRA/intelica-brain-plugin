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

Estado de portal-prod (610944808410), región eu-south-2, VPC
vpc-0626d66632373c892.

Cost Explorer (`ce`, us-east-1), GetCostAndUsage de septiembre 2026,
MONTHLY. Servicio AmazonCloudWatch:

| Usage type | Cantidad | Costo USD |
|---|---|---|
| EUS2-VendedLog-Bytes | 109 GB | 57,33 |
| EUS2-DataScanned-Bytes | 6.385 GB | 33,52 |
| EUS2-TimedStorage-ByteHrs | 410 GB-Mo | 13,53 |
| EUS2-ObservationUsage | — | 204,68 |

En Amazon Simple Storage Service, la parte de flow logs (entrega de vended
logs a S3 y su almacenamiento) suma unos 9 USD en el mes. Total de la cuenta
en septiembre: 9.812,44 USD.

- DescribeFlowLogs: fl-0c1d2e3f4a5b6c7d8 (TrafficType ALL,
  LogDestinationType cloud-watch-logs, LogGroupName
  itl-0003-portal-prd-vpc-flow-logs) y fl-0d2e3f4a5b6c7d8e9 (TrafficType
  ALL, LogDestinationType s3, LogDestination
  arn:aws:s3:::itl-0003-portal-prd-s3-flowlogs-02), los dos sobre
  vpc-0626d66632373c892. Tags de los dos: Module=vpc, ManagedBy=terraform,
  Repository=portal-infra.
- logs DescribeLogGroups: itl-0003-portal-prd-vpc-flow-logs,
  retentionInDays 90, storedBytes 352.000.000.000 (~328 GB).
- logs DescribeMetricFilters sobre itl-0003-portal-prd-vpc-flow-logs: uno,
  filterName itl-0003-portal-prd-flowlogs-reject-ssh, patrón
  `[v, acct, eni, src, dst, sport, dport=22, proto, pkts, bytes, start, end, action="REJECT", status]`,
  métrica RejectedSSH en el namespace Intelica/Seguridad.
- cloudwatch DescribeAlarms (o DescribeAlarmsForMetric de RejectedSSH): una
  alarma, itl-0003-portal-prd-alarm-reject-ssh, umbral > 50 en 5 minutos,
  AlarmActions [arn:aws:sns:eu-south-2:610944808410:itl-0003-portal-prd-sns-seguridad].
  Último cambio de estado a ALARM: 2026-09-28.
- logs DescribeSubscriptionFilters: ninguno.
- cloudtrail LookupEvents con EventName StartQuery (eu-south-2): página
  vacía. No hay otra fuente que diga quién escanea los 6.385 GB.
- s3 GetBucketPolicy de itl-0003-portal-prd-s3-flowlogs-02: solo permite
  a delivery.logs.amazonaws.com escribir. GetBucketLifecycleConfiguration:
  NoSuchLifecycleConfiguration. ListObjectsV2 con MaxKeys pequeño: objetos
  bajo AWSLogs/610944808410/vpcflowlogs/eu-south-2/, el último de hoy.
- athena ListWorkGroups: solo primary. ListNamedQueries: vacío. glue
  GetTables en todas las bases: ninguna tabla apunta a
  itl-0003-portal-prd-s3-flowlogs-02.
