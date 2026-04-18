"""Gemini engine for text report + styling image generation."""
import json
import logging
import os
import re
import time
from io import BytesIO
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

from .prompts import build_before_image_prompt, build_image_prompt, build_text_report_prompt

load_dotenv(override=True)

logger = logging.getLogger("sketch.ai_engine")


def _center_crop_portrait(img: Image.Image, target_ratio: float = 2 / 3) -> Image.Image:
    """Crop to portrait aspect (w/h) around center to reduce side background."""
    w, h = img.size
    cur = w / h
    if cur <= target_ratio:
        return img
    new_w = int(h * target_ratio)
    left = (w - new_w) // 2
    return img.crop((left, 0, left + new_w, h))

TEXT_MODELS = ["gemini-3-flash-preview", "gemini-3.1-pro-preview", "gemini-2.5-flash", "gemini-2.5-pro"]
IMAGE_MODEL = "gemini-3.1-flash-image-preview"


class GeminiEngine:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY 환경변수가 필요합니다.")
        api_key = api_key.strip().strip('"').strip("'")
        self.client = genai.Client(api_key=api_key)
        logger.info("GeminiEngine initialized (key len=%d, prefix=%s)", len(api_key), api_key[:6])

    def generate_report(self, age: str, job: str, desired_keywords: str,
                        before_image: Optional[Image.Image] = None,
                        ref_images: Optional[List[Image.Image]] = None,
                        extra_text: str = "") -> dict:
        prompt = build_text_report_prompt(
            age, job, desired_keywords,
            extra_text=extra_text,
            has_image=before_image is not None,
        )
        parts = [prompt]
        if before_image is not None:
            parts.append(before_image)
        for ref in ref_images or []:
            parts.append(ref)

        from google.genai import errors as genai_errors
        logger.info("generate_report start: age=%s job=%s goal=%s has_image=%s refs=%d",
                    age, job, desired_keywords, before_image is not None, len(ref_images or []))
        last_err = None
        for attempt in range(3):
            for model in TEXT_MODELS:
                t0 = time.time()
                try:
                    logger.info("calling %s (attempt=%d)", model, attempt + 1)
                    response = self.client.models.generate_content(
                        model=model,
                        contents=parts,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.7,
                        ),
                    )
                    logger.info("%s ok in %.2fs", model, time.time() - t0)
                    return self._parse_json(response.text)
                except genai_errors.ServerError as e:
                    last_err = e
                    logger.warning("%s failed (%.2fs): %s", model, time.time() - t0, e)
                    time.sleep(2 ** attempt)
        logger.error("all text model attempts failed")
        raise last_err

    def generate_before_image(self, age: str, job: str, desired_keywords: str,
                              extra_text: str, out_path: Path) -> Optional[Path]:
        prompt = build_before_image_prompt(age, job, desired_keywords, extra_text)
        t0 = time.time()
        logger.info("generate_before_image -> %s", out_path.name)
        cfg = types.GenerateContentConfig(
            http_options=types.HttpOptions(timeout=90_000),
        )
        last_err = None
        for attempt in range(2):
            try:
                response = self.client.models.generate_content(
                    model=IMAGE_MODEL,
                    contents=[prompt],
                    config=cfg,
                )
                for part in response.candidates[0].content.parts:
                    if getattr(part, "inline_data", None) and part.inline_data.data:
                        img = Image.open(BytesIO(part.inline_data.data))
                        img = _center_crop_portrait(img, target_ratio=2 / 3)
                        out_path.parent.mkdir(parents=True, exist_ok=True)
                        img.save(out_path)
                        logger.info("before image saved %s in %.2fs (attempt=%d)",
                                    out_path, time.time() - t0, attempt + 1)
                        return out_path
                logger.warning("no before image returned (attempt=%d)", attempt + 1)
                return None
            except Exception as e:
                last_err = e
                logger.warning("before image attempt %d failed (%.1fs): %s",
                               attempt + 1, time.time() - t0, e)
        raise last_err

    def generate_styling_image(self, age: str, desired_keywords: str,
                               before_image: Image.Image,
                               out_path: Path,
                               look_index: int = 0,
                               custom_prompt: Optional[str] = None) -> Optional[Path]:
        if custom_prompt and custom_prompt.strip():
            base = build_image_prompt(age, desired_keywords, look_index=look_index)
            prompt = base + "\n\n[사용자 추가 지시]\n" + custom_prompt.strip()
        else:
            prompt = build_image_prompt(age, desired_keywords, look_index=look_index)
        t0 = time.time()
        logger.info("generate_styling_image -> %s", out_path.name)
        cfg = types.GenerateContentConfig(
            http_options=types.HttpOptions(timeout=60_000),  # ms — fail fast + retry
        )
        last_err = None
        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model=IMAGE_MODEL,
                    contents=[prompt, before_image],
                    config=cfg,
                )
                for part in response.candidates[0].content.parts:
                    if getattr(part, "inline_data", None) and part.inline_data.data:
                        img = Image.open(BytesIO(part.inline_data.data))
                        img = _center_crop_portrait(img, target_ratio=2 / 3)
                        out_path.parent.mkdir(parents=True, exist_ok=True)
                        img.save(out_path)
                        logger.info("image saved %s in %.2fs (attempt=%d)",
                                    out_path, time.time() - t0, attempt + 1)
                        return out_path
                logger.warning("no image returned for %s (attempt=%d)", out_path.name, attempt + 1)
                return None
            except Exception as e:
                last_err = e
                logger.warning("image gen attempt %d failed (%.1fs): %s",
                               attempt + 1, time.time() - t0, e)
        raise last_err

    @staticmethod
    def _parse_json(text: str) -> dict:
        text = text.strip()
        # strip accidental code fences
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # fallback: extract first {...} block
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                return json.loads(m.group(0))
            raise
