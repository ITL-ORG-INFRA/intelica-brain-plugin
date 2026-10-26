---
type: agent
---

Respondé como la tool `aws_api` del servidor intelica-gateway: un JSON con
`account`, `account_id`, `region`, `data` (ya filtrado por el JMESPath de
`query` si vino) y `_costo`. Si la operación no está permitida o el recurso
no existe, devolvé `{"error": "<Code>", "mensaje": "<texto>"}`. Lo que no
esté descrito abajo devuelve un resultado vacío coherente, nunca datos que
contradigan lo de abajo. Todo el estado de este caso es inventado salvo los ids
de cuenta.

**audit (060795899335), `guardduty GetFindings`** del detector
0de7ec70ra0000000000000000eva1:

1. `1a2b3c4d5e6f00000000000000000001` — `DefenseEvasion:EC2/UnusualDNSResolver`,
   severidad 5.0, cuenta 610944808410 (portal-prod), recurso Instance
   `i-0aaa111denver` (Windows, sin IP pública). `Service.Action.NetworkConnectionAction`:
   UDP 53 saliente hacia `10.100.0.10`. Primera vez 2026-09-08, última
   2026-10-11, 11 veces.
2. `1a2b3c4d5e6f00000000000000000002` —
   `UnauthorizedAccess:IAMUser/InstanceCredentialExfiltration.OutsideAWS`,
   severidad 8.0, cuenta 891376942769 (portal-dev), recurso AccessKey de la
   sesión `i-0bbb222app` del rol `itl-0003-portal-dev-role-ec2-app-03`.
   `Service.Action.AwsApiCallAction`: `ListBuckets` desde `185.220.101.47`
   (ASN de un proveedor de hosting en Alemania, no AWS). Primera y última
   vez 2026-10-12 03:12 UTC, 4 veces.

**portal-prod (610944808410)**: `ec2 DescribeInstances` de `i-0aaa111denver`
→ VPC `vpc-0626d66632373c892`, DHCP options `dopt-0corp`.
`ec2 DescribeDhcpOptions dopt-0corp` → `domain-name-servers: 10.100.0.10,
10.100.0.11`, `domain-name: intelica.local`. **intelica-network
(954976322048)**: `route53resolver ListResolverEndpoints` → endpoint
`rslvr-in-corp` INBOUND con IPs `10.100.0.10` y `10.100.0.11`.
CloudTrail en portal-prod: nada relevante en la ventana.

**portal-dev (891376942769)**: `cloudtrail LookupEvents` con la sesión
`i-0bbb222app` el 2026-10-12 entre 02:40 y 03:40 UTC → `ListBuckets`,
`GetBucketPolicy` sobre `itl-0003-portal-dev-s3-general-03`,
`ListObjectsV2` sobre el mismo bucket, todas con `sourceIPAddress
185.220.101.47` y `userAgent aws-cli/2.15`; antes de las 03:12, las llamadas
de esa sesión venían de `10.12.3.40`, la IP privada de la instancia. El rol
tiene `AmazonS3FullAccess` adjunta. La instancia tiene IP pública
`18.100.4.9` y su SG `sg-0app3` deja entrar 22/tcp desde `0.0.0.0/0`.
Ningún deploy ni `AssumeRole` humano en la ventana.
