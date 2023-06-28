import logging
import time

log = logging.getLogger(__name__)

class FrameLimiter():
    def __init__(self, limit) -> None:
        self.limit = limit
        self.old = time.time()
        self.elapsed = 0
        self.frames = 0

    def tick(self) -> float:
        # calculate deltatime
        now = time.time()
        dt = now - self.old

        # sleep to reach frame rate limit
        time.sleep(max(1 / self.limit - dt, 0))

        # calculate deltatime
        now = time.time()
        dt = now - self.old
        self.old = now

        self.elapsed += dt
        self.frames += 1

        # debugging message every second
        if self.elapsed >= 1:
            log.debug(self.frames)
            self.elapsed = 0
            self.frames = 0

        return max(1 / self.limit, dt)
