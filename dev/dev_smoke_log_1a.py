from __future__ import annotations

from pathlib import Path
import sys
 
ROOT = Path(__file__).resolve().parents[1]
 
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
     
from LOG.log_1a_structured_logging import (
    setup_logging,
    bind_context,
    clear_context,
    log_event,
    log_exception,
)
 
 
def main() -> None:
    cfg = {
        "LOG_LEVEL": "INFO",
        "LOG_JSON": "true",
        "QUIET_CONSOLE": "false",
        # optional file output:
        # "LOG_PATH": "data_smoke/rpa.log.jsonl",
        # "LOG_MAX_BYTES": 500_000,
        # "LOG_BACKUPS": 2,
    }
 
    logger = setup_logging(cfg)
 
    # Run-level context
    bind_context(cfg, run_id=cfg.get("RUN_ID"), current_id=None, item_index=None, total_items=None)
    log_event(logger, "smoke_start", message="LOG-1A smoke starting")
 
    # Per-item context (simulate LOOP injecting these)
    bind_context(cfg, current_id="ABC123", item_index=1, total_items=3)
    log_event(logger, "item_begin", message="Processing item", url="https://example.com")
 
    # Redaction demo
    log_event(
        logger,
        "secrets_demo",
        message="Should redact secrets",
        password="supersecret",
        api_key="ABC-DEF-123",
        authorization="Bearer reallySensitiveTokenValue",
    )
 
    # Exception demo
    try:
        raise RuntimeError("Boom (expected for smoke)")
    except Exception as e:
        log_exception(logger, e, step_id="S1", milestone="LOG-1A", tag="smoke")
 
    log_event(logger, "smoke_done", message="LOG-1A smoke complete")
    clear_context()
 
 
if __name__ == "__main__":
    main()