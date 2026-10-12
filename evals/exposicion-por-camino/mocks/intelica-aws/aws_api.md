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

Estado de Portal QA/UAT (396608799622), eu-south-2, VPC vpc-0qa (10.20.0.0/16).

Security groups con ingreso desde `0.0.0.0/0`:

| SG | Puerto | Usado por | IP pública de la ENI |
|---|---|---|---|
| sg-0db1 (`itl-0003-portal-qa-sg-rds-02`) | 5432/tcp | ENI eni-0rds1 de la Aurora `itl-0003-portal-qa-rds-apps-02` (subnet privada subnet-0priv-a, sin ruta a internet gateway) | ninguna |
| sg-0alb2 (`k8s-alb-02`) | 443/tcp | el ALB `itl-0003-portal-qa-alb-02` | es el balanceador |

La Aurora tiene `PubliclyAccessible: false`.

Balanceadores (`DescribeLoadBalancers`): `itl-0003-portal-qa-alb-02`,
`Scheme: internet-facing`, ARN
`arn:aws:elasticloadbalancing:eu-south-2:396608799622:loadbalancer/app/itl-0003-portal-qa-alb-02/aa11`.
Listener 443 (`listener/app/itl-0003-portal-qa-alb-02/aa11/l443`), reglas
(`DescribeRules`):

| Prioridad | Condición | Acción |
|---|---|---|
| 10 | host `redisinsight.qa.intelica.example` | forward a `k8s-external-redisins-f07f01bf47` (puerto 5540) |
| 20 | host `portal.qa.intelica.example` | authenticate-oidc y después forward a `k8s-external-portal-1b2c` |
| default | — | fixed-response 404 |

Ninguna regla tiene condición `source-ip`. `wafv2 GetWebACLForResource`
devuelve vacío para el ALB.

Los nombres de host, los ids `aa11`, `l443`, `1b2c`, sg-0db1, sg-0alb2,
eni-0rds1 y subnet-0priv-a son inventados; el target group de redisinsight
y el nombre del ALB son reales.
