---
type: agent
---

Respondé como la tool del servidor intelica-aws que te toque, con el formato
de esa tool: JSON con los datos y `_costo` con `bytes` y `tokens_aprox`. Si
la operación no está permitida o el recurso no existe, devolvé
`{"error": "<Code>", "mensaje": "<texto>"}`. Lo que no esté descrito abajo
devuelve un resultado vacío coherente, nunca datos que contradigan lo de
abajo. Este estado es **inventado para este eval**.

Cualquier escritura (Authorize*, Revoke*, Modify*, Create*, Delete*,
Update*): {"error": "Denied", "mensaje": "<servicio>:<Operacion> no es una
operacion de lectura. Este servidor solo permite operaciones de lectura."}

Hoy es 2026-10-10. Estado de portal-prod (610944808410), eu-south-2, VPC
vpc-0626d66632373c892 (10.10.0.0/16).

## EKS y la aplicación

- Cluster itl-0003-portal-prd-eks-apps-02, versión 1.31. Los nodos son
  instancias EC2 con el tag eks:cluster-name=itl-0003-portal-prd-eks-apps-02,
  en subnets privadas de las tres AZ, con el security group de nodos
  sg-0a1b2c3d4e5f60718 (itl-0003-portal-prd-eks-apps-02-node-sg). Los pods
  usan IPs de la VPC (VPC CNI, sin security groups por pod).
- Namespace portal, deployment portal-api, 3 réplicas Running, 0 reinicios
  en las últimas 24 h (la app no se cae: reintenta). Imagen sin cambios
  desde 2026-09-30.
- Logs de portal-api (k8s_logs): desde 2026-10-09T14:53Z, cada 30 s,
  "ERROR db pool: connect ETIMEDOUT 10.10.5.20:5432
  (itl-0003-portal-prd-rds-portal-02.cxyz.eu-south-2.rds.amazonaws.com)".
  Antes de esa hora, nada de errores de base.
- Eventos del namespace (k8s_events): solo Normal, nada de Warnings.

## RDS

- rds DescribeDBInstances: itl-0003-portal-prd-rds-portal-02, postgres 16,
  available, Multi-AZ, endpoint
  itl-0003-portal-prd-rds-portal-02.cxyz.eu-south-2.rds.amazonaws.com:5432,
  IP privada 10.10.5.20, VpcSecurityGroups [sg-0f9e8d7c6b5a40321],
  IAMDatabaseAuthenticationEnabled false. Sin eventos de RDS (DescribeEvents)
  en las últimas 48 h salvo backups.
- CloudWatch DatabaseConnections: ~45 estable hasta 2026-10-09 14:50Z, cae a
  2 (las de un bastión) desde 14:53Z.

## Red

- ec2 DescribeSecurityGroups sg-0f9e8d7c6b5a40321
  (itl-0003-portal-prd-rds-portal-sg, tags ManagedBy=terraform,
  Module=rds, Repository=portal-infra): entrada solo tcp 5432 desde
  sg-0c4d5e6f7a8b90123 (el del bastión). **No tiene regla desde
  sg-0a1b2c3d4e5f60718.** Salida: todo.
- sg-0a1b2c3d4e5f60718 (nodos): salida todo.
- NACLs de las subnets de nodos y de la RDS: la default, acl-0d1e2f3a4b5c6d7e8,
  regla 100 allow all en entrada y salida.
- Tablas de rutas de las subnets de nodos y de la RDS: 10.10.0.0/16 → local.
- Flow logs (FilterLogEvents en itl-0003-portal-prd-vpc-flow-logs) hacia
  10.10.5.20 puerto 5432 desde IPs 10.10.2.x/10.10.3.x/10.10.4.x (nodos):
  ACCEPT hasta 14:52Z del 9/10; REJECT desde 14:53Z.
- cloudtrail LookupEvents (eu-south-2) con EventName
  RevokeSecurityGroupIngress o ResourceName sg-0f9e8d7c6b5a40321: un evento,
  2026-10-09T14:52:41Z, RevokeSecurityGroupIngress sobre
  sg-0f9e8d7c6b5a40321, ipPermissions tcp 5432 desde
  sg-0a1b2c3d4e5f60718, usuario
  AWSReservedSSO_ItlAWSAllAdm_3f2a1b0c9d8e7f6a/martin.rios@intelica.com,
  desde la consola. Ningún otro cambio de red en 48 h.

## Identidad

- La app usa usuario y contraseña de Postgres (no IAM auth); la contraseña
  está en Secrets Manager (no se puede leer, ni hace falta). La service
  account portal-api tiene IRSA con un rol que solo lee ese secreto; sin
  cambios en IAM en 48 h (CloudTrail).
