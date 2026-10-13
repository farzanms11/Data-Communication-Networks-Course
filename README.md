# Data Communication Networks

**Sharif University of Technology · Department of Electrical Engineering**  
**Farzan Aghaei**

Practical coursework and a final programming project for the Data Communication Networks course. The repository includes OMNeT++/INET network simulations, experimental reports, and a Python HTTP proxy server.

## Practical coursework

| Assignment | Implementation | Files |
| --- | --- | --- |
| **HW2 · Data Link Layer** | Network topologies, configured traffic scenarios, and simulation analysis | [Simulations](assignments/02-data-link-layer/simulations/) · [Report](assignments/02-data-link-layer/practical-report.pdf) |
| **HW3 · MAC Sublayer** | Ethernet traffic experiments, CSMA/CD configurations, and VLAN scenarios | [Simulations](assignments/03-mac-sublayer/simulations/) · [Report](assignments/03-mac-sublayer/practical-report.pdf) |
| **HW4 · Network Layer** | AODV routing and mobile-network simulation | [Simulation](assignments/04-network-layer/simulations/AODV/) · [Report](assignments/04-network-layer/practical-report.pdf) |

Each simulation directory contains the available OMNeT++ configuration (`omnetpp.ini`), network definitions (`.ned`), project configuration files, and supplied analysis/scalar-result files (`.anf`/`.sca`). The reports contain the corresponding experimental procedures and results.

### Running the simulations

Open a simulation directory as an OMNeT++ project and configure the INET framework dependency (named `inet` in the included project settings). Run a configuration from `omnetpp.ini` to reproduce its scenario. The required OMNeT++/INET version depends on the original project configuration; compatibility has not been independently verified.

## Final project · HTTP Proxy Server

[**Source code, usage, and project report →**](final-project/)

A Python HTTP forward proxy built with sockets and concurrent request handling. Its Tkinter interface supports starting and stopping the server, URL filtering, an in-memory response cache, traffic statistics, request logs, and traceroute diagnostics. The application listens on `127.0.0.1` and handles plain HTTP requests; HTTPS `CONNECT` tunnelling is not supported.

Run from the repository root:

```bash
python final-project/proxy_server.py
```

Run the local integration tests:

```bash
python -m unittest discover -s tests -v
```

**Requirements:** Python 3.9+ with Tkinter. OMNeT++/INET is required only for the network simulation exercises.
