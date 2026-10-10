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
que contradigan lo de abajo. Si piden una lista larga sin `query`, devolvé
los primeros 50 elementos con `next_token`.

Cualquier operación de escritura (Delete*, Modify*, Create*, Update*, Put*,
Release*, Stop*, Terminate*): {"error": "Denied", "mensaje":
"<servicio>:<Operacion> no es una operacion de lectura. Este servidor solo
permite operaciones de lectura."}

Estado de portal-prod (610944808410). Lo de NAT, endpoint, flow logs,
Logs Insights, snapshots, io1 y ObservationUsage sale del análisis real del
2026-10-10; las EIPs, el volumen `available`, la instancia apagada, el ALB,
el log group sin retención, el bucket sin lifecycle, RDS, ECR y Savings
Plans son **inventados para este eval**.

## Cost Explorer (`ce`, us-east-1)

GetCostAndUsage de septiembre 2026 (2026-09-01 a 2026-10-01), MONTHLY. Total
de la cuenta: 9.812,44 USD. Todo el gasto regional es de eu-south-2; en
us-east-1 solo hay cargos globales chicos (menos de 5 USD).

| Servicio | Usage type | Cantidad | Costo USD |
|---|---|---|---|
| Amazon Elastic Compute Cloud - Compute | EUS2-BoxUsage (varios tipos) | — | 3.987,15 |
| Amazon Relational Database Service | (varios) | — | 1.802,36 |
| EC2 - Other | EUS2-EBS:SnapshotUsage | 30.538 GB-Mo | 1.404,81 |
| EC2 - Other | EUS2-EBS:VolumeP-IOPS.piops | 9.000 IOPS-Mo | 594,00 |
| EC2 - Other | EUS2-EBS:VolumeUsage.piops | 2.200 GB-Mo | 279,40 |
| EC2 - Other | EUS2-EBS:VolumeUsage.gp3 | 4.100 GB-Mo | 377,20 |
| EC2 - Other | EUS2-NatGateway-Bytes | 6.692 GB | 295,52 |
| EC2 - Other | EUS2-NatGateway-Hours | 720 Hrs | 31,80 |
| EC2 - Other | EUS2-DataTransfer-Regional-Bytes | 15.485 GB | 142,47 |
| EC2 - Other | EUS2-ElasticIP:IdleAddress | 1.440 Hrs | 7,20 |
| Amazon Simple Storage Service | EUS2-TimedStorage-ByteHrs | 10.800 GB-Mo | 248,40 |
| Amazon Simple Storage Service | (requests y resto) | — | 29,80 |
| AmazonCloudWatch | EUS2-ObservationUsage | — | 204,68 |
| AmazonCloudWatch | EUS2-VendedLog-Bytes | 109 GB | 57,33 |
| AmazonCloudWatch | EUS2-TimedStorage-ByteHrs | 1.610 GB-Mo | 52,16 |
| AmazonCloudWatch | EUS2-DataScanned-Bytes | 6.385 GB | 33,52 |
| Amazon Elastic Container Service for Kubernetes | EUS2-AmazonEKS-Hours:perCluster | 1.440 Hrs | 144,00 |
| Elastic Load Balancing | EUS2-LoadBalancerUsage | 2.160 Hrs | 54,43 |
| Amazon EC2 Container Registry (ECR) | EUS2-TimedStorage-ByteHrs | 180 GB-Mo | 18,00 |
| resto | — | — | 48,21 |

En S3, la parte de los flow logs (entrega y almacenamiento) es ~9 USD.

GetSavingsPlansCoverage y GetReservationCoverage de los últimos 3 meses:
cobertura 0 %. Todo el cómputo es On Demand.

## Red (eu-south-2, VPC vpc-0626d66632373c892, 10.10.0.0/16)

- DescribeNatGateways: un solo NAT, nat-07f69a860188add0f, en
  subnet-0d41a7e2c9b35f601 (eu-south-2a), ENI eni-095e1411c22a5026c,
  PrivateIp 10.10.1.165, PublicIp 51.49.38.3.
- DescribeRouteTables: rtb-0bb264a8a341f1036
  (itl-0003-portal-prd-rt-private-02) asociada a 6 subnets privadas (dos por
  AZ; la de DENVER es subnet-0b2d4f6a8c0e20301, eu-south-2b), rutas
  10.10.0.0/16 → local y 0.0.0.0/0 → nat-07f69a860188add0f, **sin ruta a
  ninguna prefix list**. rtb-0e7a91c3b5d2f4a68 (rt-restricted-02): local y
  pl-64a5400d → vpce-012a2803fd24a38c7. Una tabla pública con IGW.
- DescribeVpcEndpoints: solo vpce-012a2803fd24a38c7 (Gateway, S3, política
  `*`, RouteTableIds [rtb-0e7a91c3b5d2f4a68]). Tags Module=vpc,
  ManagedBy=terraform, Repository=portal-infra.
- pl-64a5400d es com.amazonaws.eu-south-2.s3: 3.5.32.0/22, 3.5.126.0/23,
  16.12.24.0/21, 52.95.144.0/22.
- CloudWatch BytesOutToDestination del NAT: ~21,5 GB a las 04:00 UTC y
  ~100 GB a las 18:00 UTC todos los días; 5.924 GB del 10/09 al 10/10.
- Flow logs de la ENI del NAT (FilterLogEvents en
  itl-0003-portal-prd-vpc-flow-logs, stream eni-095e1411c22a5026c-all): los
  flujos grandes vienen de 10.10.4.10 (i-0016a8bc9ee8b94c7, DENVER,
  eu-south-2b) y salen a 3.5.32-34.x y 3.5.126-127.x, puerto 443.
- DescribeAddresses: tres EIPs. eipalloc-0f3a5b7c9d1e2f304 asociada al NAT.
  eipalloc-0a4b6c8d0e2f4a515 (18.100.42.7) y eipalloc-0b5c7d9e1f3a5b626
  (18.100.42.19) sin AssociationId, sin tags.
- DescribeFlowLogs: fl-0c1d2e3f4a5b6c7d8 (ALL → CloudWatch Logs,
  itl-0003-portal-prd-vpc-flow-logs) y fl-0d2e3f4a5b6c7d8e9 (ALL → S3,
  itl-0003-portal-prd-s3-flowlogs-02).

## Logs y observabilidad

- DescribeLogGroups (los que tienen más de 1 GB):
  itl-0003-portal-prd-vpc-flow-logs, retentionInDays 90, storedBytes
  352.000.000.000; /aws/eks/itl-0003-portal-prd-eks-apps-02/cluster, **sin
  retentionInDays**, storedBytes 1.288.000.000.000 (~1.200 GB), creado
  2024-03; /aws/containerinsights/itl-0003-portal-prd-eks-apps-02/performance,
  retention 1 día, storedBytes 9.000.000.000. Los demás suman menos de 5 GB.
- DescribeMetricFilters sobre itl-0003-portal-prd-vpc-flow-logs: uno,
  itl-0003-portal-prd-flowlogs-reject-ssh → métrica RejectedSSH
  (Intelica/Seguridad), con la alarma itl-0003-portal-prd-alarm-reject-ssh
  que notifica al SNS itl-0003-portal-prd-sns-seguridad.
- DescribeSubscriptionFilters: ninguno. CloudTrail LookupEvents de
  StartQuery: página vacía.
- eks DescribeAddon amazon-cloudwatch-observability en
  itl-0003-portal-prd-eks-apps-02: ACTIVE, con observabilidad mejorada.

## EBS, snapshots, instancias

- DescribeVolumes:
  - Tres io1 de 3.000 IOPS y entre 600 y 900 GiB (2.200 GiB en total):
    vol-0d1a3c5e7f9b1d206, vol-0d2b4d6f8a0c2e317, vol-0d3c5e7a9b1d3f428,
    adjuntos a i-0c7e9a1b3d5f7a839 (itl-0003-portal-prd-ec2-sql-02, SQL
    Server). Tags ManagedBy=terraform, Repository=portal-infra. CloudWatch
    14 días: VolumeReadOps + VolumeWriteOps nunca pasan de ~400 IOPS por
    volumen; VolumeQueueLength < 1.
  - vol-0e8f0a2b4c6d8e951, gp3, 500 GiB, State **available**, creado
    2026-06-02 desde snap-0f1e2d3c4b5a69788, sin tags. CloudTrail:
    DetachVolume el 2026-06-20 de i-0a9c1e3b5d7f9a140.
  - El resto, gp3 in-use.
- DescribeSnapshots OwnerIds=[self]: 412 snapshots. 186 de ellos tienen un
  VolumeId que ya no existe y no aparecen en el BlockDeviceMappings de
  ninguna AMI propia; suman 14.200 GiB de VolumeSize, el más nuevo de
  2025-11. Los otros 226 son de volúmenes vivos o de AMIs.
- DescribeInstances:
  - i-0a9c1e3b5d7f9a140 (itl-0003-portal-prd-ec2-reporting-old), **stopped**,
    StateTransitionReason "User initiated (2026-05-14 16:02:11 GMT)", dos
    volúmenes gp3 de 200 y 100 GiB. Tags ManagedBy=terraform,
    Repository=portal-infra.
  - DENVER i-0016a8bc9ee8b94c7 (m5.2xlarge) y el resto running. CPU máxima
    en 14 días por encima del 45 % en todas, salvo
    itl-0003-portal-prd-ec2-sql-02 (r5.4xlarge) con un máximo de 38 %.

## Balanceadores, RDS, S3, ECR, EKS

- elbv2 DescribeLoadBalancers: tres ALB. itl-0003-portal-prd-alb-legacy-02
  tiene un solo target group, itl-0003-portal-prd-tg-legacy-02, con 0
  targets registrados; RequestCount 0 en 30 días. Los otros dos con tráfico
  y targets sanos.
- rds DescribeDBInstances: dos instancias de producción,
  itl-0003-portal-prd-rds-portal-02 e itl-0003-portal-prd-rds-auth-02
  (db.r6g.xlarge, Multi-AZ, gp3), con DatabaseConnections entre 40 y 120 y CPU media del 35 %. Sin snapshots
  manuales. Nada que recortar.
- S3: itl-0003-portal-prd-s3-denver-02 tiene BucketSizeBytes
  StandardStorage de ~9.600 GB, versionado Enabled y
  NoSuchLifecycleConfiguration. Los demás buckets suman ~1.200 GB y tienen
  lifecycle.
- ECR: 14 repositorios, todos con lifecycle policy.
- eks_list_clusters / DescribeCluster: itl-0003-portal-prd-eks-apps-02 y
  itl-0003-portal-prd-eks-data-02, versión 1.31, en soporte estándar.
