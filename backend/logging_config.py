import json
import logging
import os
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler


# ============================================================
# REQUEST ID
# ============================================================

request_id_context: ContextVar[str] = ContextVar(
    "request_id",
    default="-"
)


# ============================================================
# LOG DIRECTORY
# ============================================================

LOG_DIR = "logs"

os.makedirs(
    LOG_DIR,
    exist_ok=True
)


LOG_FILE = os.path.join(
    LOG_DIR,
    "workforce_management.log"
)


# ============================================================
# STRUCTURED JSON FORMATTER
# ============================================================

class StructuredJsonFormatter(
    logging.Formatter
):

    def format(
        self,
        record: logging.LogRecord
    ):

        log_entry = {
            "timestamp": self.formatTime(
                record,
                "%Y-%m-%dT%H:%M:%S"
            ),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_context.get(),
        }

        if hasattr(
            record,
            "request_method"
        ):
            log_entry["method"] = (
                record.request_method
            )

        if hasattr(
            record,
            "request_path"
        ):
            log_entry["path"] = (
                record.request_path
            )

        if hasattr(
            record,
            "status_code"
        ):
            log_entry["status_code"] = (
                record.status_code
            )

        if hasattr(
            record,
            "duration_seconds"
        ):
            log_entry["duration_seconds"] = (
                record.duration_seconds
            )

        if record.exc_info:
            log_entry["exception"] = (
                self.formatException(
                    record.exc_info
                )
            )

        return json.dumps(
            log_entry,
            ensure_ascii=False
        )


# ============================================================
# LOGGING SETUP
# ============================================================

def setup_logging():

    logger = logging.getLogger()

    logger.setLevel(
        logging.INFO
    )

    # Prevent duplicate handlers when
    # Uvicorn reloads the application.
    if logger.handlers:
        return

    formatter = (
        StructuredJsonFormatter()
    )

    # --------------------------------------------------------
    # CONSOLE HANDLER
    # --------------------------------------------------------

    console_handler = (
        logging.StreamHandler()
    )

    console_handler.setLevel(
        logging.INFO
    )

    console_handler.setFormatter(
        formatter
    )

    # --------------------------------------------------------
    # FILE HANDLER
    # --------------------------------------------------------

    file_handler = (
        RotatingFileHandler(
            LOG_FILE,
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8"
        )
    )

    file_handler.setLevel(
        logging.INFO
    )

    file_handler.setFormatter(
        formatter
    )

    # --------------------------------------------------------
    # REGISTER HANDLERS
    # --------------------------------------------------------

    logger.addHandler(
        console_handler
    )

    logger.addHandler(
        file_handler
    )

    logger.info(
        "Workforce Management Platform "
        "structured logging initialized"
    )