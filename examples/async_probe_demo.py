"""Compare sequential and concurrent simulated device probes."""

import asyncio
from time import perf_counter

from app.services.probe import simulate_device_probe


async def main() -> None:
	device_ids = ["RTR-101", "SW-102", "SRV-103"]
	start = perf_counter()
	sequential = [await simulate_device_probe(device_id) for device_id in device_ids]
	sequential_seconds = perf_counter() - start

	start = perf_counter()
	concurrent = await asyncio.gather(
		*(simulate_device_probe(device_id) for device_id in device_ids)
	)
	concurrent_seconds = perf_counter() - start

	print(f"Sequential: {sequential} ({sequential_seconds:.3f} seconds)")
	print(f"Concurrent: {concurrent} ({concurrent_seconds:.3f} seconds)")


if __name__ == "__main__":
	asyncio.run(main())