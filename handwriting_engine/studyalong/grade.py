"""Grade a student's ink in a blank region.

Primary path: optional vision model if ANTHROPIC_API_KEY is set.
Fallback: normalize text guess from the client, or reveal-answer mode.
Never invent graph answers — always compare against the code-computed key.
"""
from __future__ import annotations

import base64
import json
import os
import re
import urllib.error
import urllib.request
from typing import Any


def _norm(s: str) -> str:
    s = s.strip().lower()
    s = s.replace("→", "->").replace("—", "-").replace("–", "-")
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^\w\s\-\+\=\.\,/]", "", s)
    return s.strip()


def _equivalent(read: str, answer: str) -> bool:
    a, b = _norm(read), _norm(answer)
    if not a:
        return False
    if a == b:
        return True
    # numeric tolerance
    try:
        return abs(float(a) - float(b)) < 1e-6
    except ValueError:
        pass
    # allow "r2" vs "R2", and path forms
    if a.replace(" ", "") == b.replace(" ", ""):
        return True
    # next-hop often written as "next hop R2" 
    if b in a.split() or a in b.split():
        return True
    return False


def grade_text(read: str, answer: str, hint: str = "") -> dict[str, Any]:
    ok = _equivalent(read, answer)
    return {
        "read": read,
        "correct": ok,
        "hint": "" if ok else (hint or f"Look again — expected something like “{answer}”"),
        "answer": answer if not ok else None,
        "method": "text",
    }


def grade_ink_png(
    png_bytes: bytes,
    answer: str,
    hint: str = "",
    client_read: str | None = None,
) -> dict[str, Any]:
    """Grade a cropped blank. Prefer client_read (from simple OCR/hand entry), then vision, then fail soft."""
    if client_read is not None and client_read.strip():
        result = grade_text(client_read, answer, hint)
        result["method"] = "client_read"
        return result

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        try:
            return _grade_vision(png_bytes, answer, hint, api_key)
        except Exception as e:
            return {
                "read": "",
                "correct": False,
                "hint": hint or "Could not read that ink. Try writing clearer, or use Reveal.",
                "error": str(e),
                "method": "vision_error",
                "answer": None,
            }

    # No API key: ask the UI to collect a typed guess, or use reveal
    return {
        "read": "",
        "correct": False,
        "hint": hint or "Type what you wrote (or set ANTHROPIC_API_KEY for auto-read), then Check again.",
        "needs_read": True,
        "method": "needs_read",
        "answer": None,
    }


def _grade_vision(png_bytes: bytes, answer: str, hint: str, api_key: str) -> dict[str, Any]:
    b64 = base64.standard_b64encode(png_bytes).decode("ascii")
    body = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 200,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": "image/png", "data": b64},
                    },
                    {
                        "type": "text",
                        "text": (
                            "Read the handwriting in this cropped note blank. "
                            'Reply ONLY with JSON: {"read": "..."}. Do not judge correctness or infer an answer from the hint. '
                            f"Context hint: {hint}"
                        ),
                    },
                ],
            }
        ],
    }
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(body).encode(),
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode())
    text = payload["content"][0]["text"]
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return grade_text(text, answer, hint) | {"method": "vision_raw"}
    data = json.loads(m.group(0))
    read = str(data.get("read", ""))
    # The model only transcribes; answer correctness is determined by code.
    ok = _equivalent(read, answer)
    return {
        "read": read,
        "correct": ok,
        "hint": "" if ok else (data.get("hint") or hint or "Try again"),
        "method": "vision",
        "answer": None if ok else answer,
    }
