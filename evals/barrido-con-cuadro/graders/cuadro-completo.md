---
type: llm
---

PASS si la respuesta final tiene un cuadro de oportunidades de portal-prod
con al menos 8 de estos 11 hallazgos, cada uno con el ID del recurso (o la
cantidad, si es un grupo), un ahorro mensual, si es medido o estimado, y un
accionable concreto:

1. S3 por el NAT: rtb-0bb264a8a341f1036 sin la ruta al endpoint
   vpce-012a2803fd24a38c7.
2. Snapshots huérfanos (186).
3. Volúmenes io1 con IOPS de sobra (vol-0d1a3c5e7f9b1d206 y los otros dos).
4. Savings Plans o reservas: cobertura 0 % del cómputo.
5. Bucket itl-0003-portal-prd-s3-denver-02 sin lifecycle.
6. ObservationUsage / observabilidad mejorada.
7. Flow logs duplicados.
8. Log group /aws/eks/itl-0003-portal-prd-eks-apps-02/cluster sin retención.
9. Volumen vol-0e8f0a2b4c6d8e951 available, o la instancia apagada
   i-0a9c1e3b5d7f9a140 (cualquiera de los dos cuenta).
10. ALB itl-0003-portal-prd-alb-legacy-02 sin targets.
11. EIPs sin asociar.

Además: el cuadro está ordenado por ahorro de mayor a menor, y la respuesta
termina preguntando por cuál empezar (vale con una recomendación).

FAIL si el cuadro trae menos de 8 de esos hallazgos, si falta la columna de
accionable o la de medido/estimado, si el accionable de los flow logs es
borrar la copia de CloudWatch sin mencionar el metric filter o la alarma, o
si dice haber aplicado algún cambio.
