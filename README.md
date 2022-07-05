# besu
This reproducible respository contains the source codes, scripts, and experiment results for the paper "Performance Analysis of Hyperledger Besu in Private Blockchain"

## Content
* [caliper-benchmarks](/caliper-benchmarks): scripts for running tests with Caliper
* [data](/data): the test results discussed in the paper. The Besu DEBUG logs analyzed in the paper are publicly available on [Zenodo](https://zenodo.org/record/6578138#.Yo1QUuxMFQJ).
* [deploy](/deploy): scripts for deploying the Besu network on OpenStack
* [load-balancing](/load-balancing): load balancer configurations
* [src](/src): scripts for analyzing the results

## Requirements
* Python >= 3.9.0
* Docker Engine >= 20.10.14

All scripts are designed to be run on Ubuntu 20.04.

The file [`requirements.txt`](./requirements.txt) contains the Python packages used in this project. Please use the following command to install all the required dependencies.

```
pip install -r requirements.txt
```

## Usage
* Clone the reproducible repository.
* Download the Besu logs from [Zenodo](https://zenodo.org/record/6578138#.Yo1QUuxMFQJ) and place them in [`data`](/data).
* The directories [`caliper-benchmarks`](/caliper-benchmarks) and [`src`](/src) contain self-explanatory Jupyter Notebooks. Please follow the instructions in the notebooks to reproduce the results.

## Abstract
In this work, we present a set of comprehensive experimental studies on Hyperledger Besu in private blockchain. We aim to exhibit its performance characteristics in terms of transaction throughput, latency, resource utilization, and scalability, from the application perspective by adding a load balancer middleware. We have carefully designed a set of comparative experiments and judiciously selected typical parameters, including transaction send rate, network size, node flavor, load balancing, consensus, and block time. In particular, three proof of authority consensus algorithms, Clique, IBFT 2.0, and QBFT, are investigated. Through extensive experimental evaluations using the Hyperledger Caliper benchmark tool, we analyze how these parameters impact the performance of a private Besu blockchain. Our studies reveal several interesting findings: 1) Blockchain parameters, e.g., block time and block size, are the most significant factors in determining Besu performance; 2) The performance of Besu is bottlenecked by transaction execution and blockchain state updates, which are determined by parameters such as node computation power, transaction complexity, and load balancing; 3) A Besu network with QBFT consensus can scale up to 14 validators without noticeable performance loss.
Our findings shed some light on further performance improvement of Hyperledger Besu. The identified bottlenecks and root cause analysis provide insightful suggestions for blockchain practitioners to build performant enterprise applications.

## Citation
Removed for the double blind review process

## Acknowledgement
This research was partially supported by the Digital Research Alliance of Canada (alliancecan.ca) and Cybera (cybera.ca) through their cloud services.

## License
Removed for the double blind review process
