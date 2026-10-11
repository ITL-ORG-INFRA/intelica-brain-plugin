---
type: llm
---

PASS si la respuesta final cumple las cuatro:

1. Da como causa que al security group de la RDS, sg-0f9e8d7c6b5a40321, le
   falta la entrada tcp 5432 desde el security group de los nodos,
   sg-0a1b2c3d4e5f60718.
2. Lo sostiene con evidencia concreta: el evento de CloudTrail
   RevokeSecurityGroupIngress del 2026-10-09 ~14:52Z (con quién lo hizo), o
   los flow logs que pasan de ACCEPT a REJECT, o los dos.
3. Descarta las otras capas con su dato: NACL, rutas, estado de la RDS,
   identidad/IAM o la app (no tiene que nombrarlas todas, pero al menos dos).
4. Entrega el arreglo sin aplicarlo: `aws ec2 authorize-security-group-ingress`
   con los dos IDs y el puerto, o restaurarlo con Terraform (el SG tiene
   ManagedBy=terraform, Repository=portal-infra). Suma si dice que, por ser
   un recurso de Terraform, un `terraform plan` debería mostrar el drift.

FAIL si da otra causa, si presenta la causa como deducida sin evidencia, si
dice haber aplicado el arreglo, o si devuelve un informe por hipótesis sin
una conclusión consolidada.
