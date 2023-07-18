# Federated Fog Simulation Based on Latency with the Auction Algorithm

### Project Description
This project is a simulation written in Python and using Docker containers to evaluate the impact of the auction algorithm to build fog federations on the edge based on their latencies.

### Components
- **fog**: represents the fog node that is located on the edge. This component is where the auction algorithm is running. In the configuration file of the simulation it's possible to choose the quantity of fog nodes in the simulation. Each fog node is a docker container.

- **client**: represents the clients that send the requests to be processed on the federation and receive the responses. In the configuration file it's possible to choose the quantity of clients in the simulation. Each client is represented by a thread in the client process, which runs on a single docker container.

- **cloud**: represents the cloud in the simulation, the cloud is responsible for processing the request when the fog nodes can't do it.

- **data collector**: this component is the manager of the simulation, it sends messages for the other containers to start the simulation and collects and aggregates all the data that is generated in the simulation.

### Benefit table equation
Let i be the index for the message that it's going to be processed and j be the index of the the fog node, the calculations to generate the benefit relation a_ij are shown below:

```py
normalized_actual_latency = 100 * actual_latency_table[j] / max_actual_latency
normalized_cpu = 100 * federation_info['cpu_usage'][j] / max_cpu_usage
normalized_function_repeat = 100 * auction_messages[i]['function_repeat'] / max_function_repeat
current_benefit = normalized_actual_latency + abs(normalized_cpu - normalized_function_repeat)
```

The 'function_repeat' attribute of the message is representing the amount of processing neeeded for that message.

### Data acquisition
Concerning the CPU and Memory Usage, this information is retrieved from the Docker API that's exposed by the Docker Daemon. The latency is calculated sending pings between the fogs.


### Running the simulation
To start the containers type the command below:

```
docker compose up -d --build
```
To stop the containers type the command below:

```
docker compose down
```

### Simulation configuration
The simulation can be configured in the env file.

### Generating the figures
To generate the figures, it must use the tools in the figure_generation folder. The generate.py script receives the path to the folder with the csv files and generate the figures in the same folder.