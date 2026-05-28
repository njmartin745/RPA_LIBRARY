from __future__ import annotations  
  
import logging  
import os  
import tempfile  
from typing import Any, MutableMapping  
  
__all__ = ["reset_logger", "setup_logging_force", "dev_smoke"]  
  
  
def reset_logger(name: str = "rpa") -> None:  
    logger = logging.getLogger(name)  
    for h in list(logger.handlers):  
        try:  
            h.flush()  
        except Exception:  
            pass  
        try:  
            h.close()  
        except Exception:  
            pass  
        try:  
            logger.removeHandler(h)  
        except Exception:  
            pass  
  
  
def setup_logging_force(cfg: MutableMapping[str, Any], *, logger_name: str = "rpa") -> logging.Logger:  
    """  
    Force LOG-1A to bind to cfg['LOG_PATH']/cfg['LOG_JSONL_PATH'] even if the CLI  
    pre-configured the logger earlier.  
    """  
    reset_logger(logger_name)  
    from LOG.log_1a_structured_logging import setup_logging  
  
    return setup_logging(cfg)  
  
  
def dev_smoke() -> None:  
    fd, p = tempfile.mkstemp(prefix="log_1b_reset_", suffix=".jsonl")  
    os.close(fd)  
    try:  
        if os.path.exists(p):  
            os.remove(p)  
    except OSError:  
        pass  
  
    cfg: dict[str, Any] = {"LOG_PATH": p, "LOG_JSONL_PATH": p}  
    logger = setup_logging_force(cfg)  
  
    from LOG.log_1a_structured_logging import log_event  
  
    log_event(logger, "smoke_event", ok=True)  
    logging.shutdown()  
  
    assert os.path.exists(p)  
    assert os.path.getsize(p) > 0  
  
    try:  
        os.remove(p)  
    except OSError:  
        pass  
  
  
if __name__ == "__main__":  
    dev_smoke()  