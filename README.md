## Comandos usados

Simular atraso e perda de pacotes:
- `sudo tc qdisc add dev lo root netem rate 700kbit`
- `sudo tc qdisc add dev lo root netem delay 300ms 100ms loss 10% rate 700kbit`

Remover simulação de atraso e perda:
`sudo tc qdisc del dev lo root`
