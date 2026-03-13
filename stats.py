def compute_stats(results):

    sent = len(results)
    received = len([r for r in results if r is not None])

    loss = ((sent - received) / sent) * 100

    rtts = [r for r in results if r]

    avg = sum(rtts) / len(rtts) if rtts else 0

    return {
        "sent": sent,
        "received": received,
        "loss": loss,
        "avg_rtt": avg
    }
