import asyncio
import time

from aos.bus.dispatcher import EventDispatcher
from aos.bus.event_store import EventStore
from aos.bus.events import Event
from aos.db.engine import connect
from aos.db.migrations import MigrationManager
from aos.db.migrations.registry import MIGRATIONS


class NoOpHandler:
    async def handle(self, event: Event):
        pass

async def run_throughput_test(tmp_path, event_count=1000):
    """
    Measure how many events per second the kernel can ingest and persist.
    """
    db_path = tmp_path / "bench.db"
    conn = connect(str(db_path))
    MigrationManager(conn).apply_migrations(MIGRATIONS)
    conn.close()

    store = EventStore(str(db_path))
    await store.initialize()
    dispatcher = EventDispatcher(store)
    handler = NoOpHandler()
    dispatcher.subscribe("bench.event", handler.handle)

    start_time = time.time()

    # Burst 1000 events
    for i in range(event_count):
        event = Event(name="bench.event", payload={"i": i})
        await dispatcher.dispatch(event)

    duration = time.time() - start_time
    rate = event_count / duration

    await store.shutdown()
    return rate, duration

if __name__ == "__main__":
    # To run: python -m aos.tests.benchmarks.benchmark_kernel
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as td:
        rate, duration = asyncio.run(run_throughput_test(Path(td), 5000))
        print("--- KERNEL BENCHMARK ---")
        print("Events: 5000")
        print(f"Time:   {duration:.4f}s")
        print(f"Rate:   {rate:.2f} events/sec")
        print("Target: >1000 events/sec")
        print(f"Result: {'PASS' if rate > 1000 else 'FAIL'}")
        print("------------------------")
