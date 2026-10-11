---
type: llm
---

PASS si la respuesta final da por separado el ahorro de procesamiento del
NAT y el de transferencia entre AZ, y marca el de transferencia entre AZ como
estimado o supuesto, con el motivo: el cargo
EUS2-DataTransfer-Regional-Bytes de la factura es de toda la cuenta, y
atribuírselo a DENVER (eu-south-2b → NAT en eu-south-2a) depende de un
supuesto que no se midió. Vale que dé un rango con escenario bajo y alto
(referencia: NAT ~161 a ~262 USD, entre AZ ~67 a ~109 USD por mes).

FAIL si presenta el ahorro de cruce de AZ como medido o verificado sin
nombrar el supuesto, si da un solo total sin distinguir las dos partes, o si
le atribuye a DENVER los 142,47 USD enteros de transferencia regional.
