import random


def simulate_network_metrics():
    """Simulate network metrics for QoS testing."""

    scenario = random.choice(["GOOD", "MEDIUM", "BAD"])

    if scenario == "GOOD":
        latency_ms = random.uniform(20, 100)
        packet_loss = random.uniform(0, 2)

    elif scenario == "MEDIUM":
        latency_ms = random.uniform(100, 250)
        packet_loss = random.uniform(2, 10)

    else:
        latency_ms = random.uniform(250, 500)
        packet_loss = random.uniform(10, 30)

    return {
        "network_scenario": scenario,
        "latency_ms": round(latency_ms, 2),
        "packet_loss": round(packet_loss, 2),
    }


def assign_qos(decision, network_metrics):
    """Assign QoS level based on network condition."""

    if decision == "DROP":
        return 0

    latency = network_metrics["latency_ms"]
    loss = network_metrics["packet_loss"]

    if latency < 100 and loss < 2:
        return 2

    if latency < 250 and loss < 10:
        return 1

    return 0