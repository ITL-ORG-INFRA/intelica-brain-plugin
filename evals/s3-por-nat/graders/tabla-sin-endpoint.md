---
type: llm
---

PASS si la respuesta final cumple las cuatro:

1. Dice que la tabla rtb-0bb264a8a341f1036 manda 0.0.0.0/0 al NAT
   nat-07f69a860188add0f y no tiene la ruta a S3, mientras el endpoint
   vpce-012a2803fd24a38c7 ya existe y está asociado solo a otra tabla.
2. Sostiene que el tráfico es S3 con evidencia de destino: flow logs hacia
   IPs dentro de la lista de prefijos pl-64a5400d (o equivalente), no solo
   por el volumen de la métrica.
3. Entrega `aws ec2 modify-vpc-endpoint` con --vpc-endpoint-id
   vpce-012a2803fd24a38c7, --add-route-table-ids rtb-0bb264a8a341f1036 y la
   región eu-south-2, como un cambio que tiene que aplicar una persona.
4. Calcula el ahorro del NAT con el precio de la factura (alrededor de
   0,044 USD/GB) y no con un precio de lista.

FAIL si propone crear un endpoint nuevo, si dice que aplicó el cambio, si
usa identificadores que no están en los datos, o si el ahorro no sale de la
factura.
