## Comandos usados (A idéia é implementalos dentro do código para simulação)

Segmentar video:
`ffmpeg -i video.mp4 -codec: copy -start_number 0 -hls_time 5 -hls_list_size 0 -f hls videos/stream.m3u8`

Simular atraso e perda de pacotes:
`sudo tc qdisc add dev <nome-rede> root netem delay 100ms loss 10%`
`sudo tc qdisc add dev lo root netem rate 500kbit`
`sudo tc qdisc add dev lo root netem delay 300ms 100ms loss 10% rate 300kbit`
(Pode ser obtido pelo comando ip link show)

Remover simulação de atraso e perda:
`sudo tc qdisc del dev wlan0 root netem`
`sudo tc qdisc del dev lo root`