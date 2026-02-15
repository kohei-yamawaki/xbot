"""Logger & State helpers."""

import json
import logging
import pathlib

STATE_PATH = pathlib.Path(__file__).resolve().parent.parent / "data" / "processed_ids.json"


def setup_logger(name: str = "xbot") -> logging.Logger:
    """アプリケーション共通のロガーを返す。"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def load_processed_ids() -> list[str]:
    """processed_ids.json を読み込んで ID リストを返す。"""
    if not STATE_PATH.exists():
        return []
    with open(STATE_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_processed_ids(ids: list[str]) -> None:
    """ID リストを processed_ids.json に書き出す。"""
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(ids, f, ensure_ascii=False, indent=2)


def is_duplicate(item_id: str, processed_ids: list[str]) -> bool:
    """item_id が既に処理済みかどうかを返す。"""
    return item_id in processed_ids
