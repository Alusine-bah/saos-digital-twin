# Link benchmark: v1 vs v2 (simulated channel, real v2 codec)

Frame sizes: v1 = 205 B ASCII (representative of the 44-field frame; real size unverified), v2 = 32 B binary.
Mega main-loop period for command pick-up is an ASSUMED 4-40 ms and dominates command response time.

| Configuration | Bit error rate | Delivery % | Undetected damaged/wrong frames | Latency mean ms | p95 ms | Command success % | Response mean ms | p95 ms | Mega TX stall ms/s |
|---|---|---|---|---|---|---|---|---|---|
| v1 ASCII @9600 (as built) | 0 | 100.0 | 0 | 214.3 | 214.7 | 100.0 | 80.2 | 165.4 | 146.9 |
| v1 ASCII @9600 (as built) | 1e-05 | 98.5 | 109 | 214.3 | 214.7 | 99.7 | 81.1 | 171.2 | 146.9 |
| v1 ASCII @9600 (as built) | 0.0001 | 84.9 | 1084 | 214.3 | 214.7 | 96.7 | 80.1 | 163.5 | 146.9 |
| v1 ASCII @9600 (as built) | 0.001 | 19.1 | 5821 | 214.3 | 214.7 | 70.9 | 80.2 | 167.6 | 146.9 |
| v1 ASCII @9600 (as built) | 0.003 | 0.7 | 7153 | 214.3 | 214.7 | 34.7 | 79.3 | 158.7 | 146.9 |
| v2 binary @9600 | 0 | 100.0 | 0 | 34.1 | 34.5 | 100.0 | 52.5 | 68.9 | 0.0 |
| v2 binary @9600 | 1e-05 | 99.7 | 0 | 34.1 | 34.5 | 100.0 | 52.8 | 68.5 | 0.0 |
| v2 binary @9600 | 0.0001 | 97.3 | 0 | 34.1 | 34.5 | 100.0 | 56.7 | 69.7 | 0.0 |
| v2 binary @9600 | 0.001 | 76.6 | 0 | 34.1 | 34.5 | 99.6 | 93.4 | 299.5 | 0.0 |
| v2 binary @9600 | 0.003 | 44.7 | 0 | 34.1 | 34.5 | 92.3 | 161.8 | 493.5 | 0.0 |
| v2 binary @115200 | 0 | 100.0 | 0 | 3.5 | 3.9 | 100.0 | 25.8 | 42.2 | 0.0 |
| v2 binary @115200 | 1e-05 | 99.7 | 0 | 3.5 | 3.9 | 100.0 | 26.1 | 41.7 | 0.0 |
| v2 binary @115200 | 0.0001 | 97.3 | 0 | 3.5 | 3.9 | 100.0 | 29.9 | 43.0 | 0.0 |
| v2 binary @115200 | 0.001 | 76.6 | 0 | 3.5 | 3.9 | 99.6 | 66.7 | 272.8 | 0.0 |
| v2 binary @115200 | 0.003 | 44.7 | 0 | 3.5 | 3.9 | 92.3 | 135.1 | 466.8 | 0.0 |

Inference (not a measurement): the thesis delivery ratio of 93 % over a 205-byte frame would correspond to a
random bit error rate of about 4.4e-05 if all losses were bit errors on the wire.
