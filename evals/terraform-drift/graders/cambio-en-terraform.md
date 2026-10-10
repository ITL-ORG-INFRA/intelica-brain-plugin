---
type: llm
---

PASS si la respuesta final, para vol-0a3f5c7e9b1d2f406 y
vol-0b4e6d8f0a2c3e517 (tags ManagedBy=terraform, Repository=portal-infra),
dice que el cambio a gp3 va en el código de Terraform (el atributo de tipo
del volumen en el módulo) y advierte que un `aws ec2 modify-volume` por CLI
lo revierte o lo pone en drift el próximo apply. Para vol-0c5f7e9a1b3d4f628,
sin tags de IaC, vale el comando de CLI.

FAIL si para los dos volúmenes con tags de Terraform entrega solo
`aws ec2 modify-volume` sin decir que tiene que ir por Terraform.
