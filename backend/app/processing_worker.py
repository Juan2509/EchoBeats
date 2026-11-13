"""Un trabajador local con exclusión PostgreSQL; las tareas no viven solo en memoria."""
import logging
from threading import Event, Thread
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.services import processing

logger = logging.getLogger(__name__)


class ProcessingWorker:
    def __init__(self, engine, interval=1):
        self.engine, self.interval = engine, interval
        self.stop_event = Event()
        self.thread = Thread(target=self.run, name='echobeats-processing', daemon=True)

    def start(self):
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        self.thread.join(timeout=5)

    def run(self):
        while not self.stop_event.is_set():
            try:
                # Sesión dedicada en autocommit: bloqueo de sesión, sin transacción larga.
                with self.engine.connect().execution_options(isolation_level='AUTOCOMMIT') as owner:
                    if not owner.scalar(text('SELECT pg_try_advisory_lock(180018, 1)')):
                        self.stop_event.wait(self.interval)
                        continue
                    try:
                        processing.recover(self.engine)
                        while not self.stop_event.is_set():
                            owner.execute(text('SELECT 1'))
                            claimed = processing.claim(self.engine)
                            if claimed is None:
                                self.stop_event.wait(self.interval)
                                continue
                            try:
                                result = processing.prepare(self.engine, claimed)
                            except Exception:
                                processing.finish(self.engine, claimed, failed=True)
                            else:
                                processing.finish(self.engine, claimed, result)
                    finally:
                        if not owner.invalidated:
                            owner.execute(text('SELECT pg_advisory_unlock(180018, 1)'))
            except SQLAlchemyError:
                logger.warning('Procesamiento temporalmente no disponible; se conserva la cola persistida.')
                self.stop_event.wait(max(self.interval, 3))
