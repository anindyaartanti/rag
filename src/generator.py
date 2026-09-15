import time
import warnings

warnings.filterwarnings("ignore", message=".*HF Hub.*")
warnings.filterwarnings("ignore", message=".*automatic function calling.*")
warnings.filterwarnings("ignore", category=FutureWarning)

from google import genai
from google.genai.types import GenerateContentConfig, AutomaticFunctionCallingConfig

from config import GOOGLE_API_KEY, GEMINI_MODEL, TEMPERATURE

MAX_RETRIES = 3
RETRY_DELAY_BASE = 15


class GeminiGenerator:
    def __init__(
        self,
        model_name: str = GEMINI_MODEL,
        temperature: float = TEMPERATURE,
        api_key: str | None = None,
    ):
        key = api_key or GOOGLE_API_KEY

        if not key or key == "YOUR_API_KEY_HERE":
            raise ValueError(
                "GOOGLE_API_KEY belum diatur. "
                "Buat API key di https://aistudio.google.com/apikey "
                "lalu isi di file .env"
            )

        self.model_name = model_name
        self.temperature = temperature
        self._client = genai.Client(api_key=key)

    def generate(self, prompt: str) -> str:
        config = GenerateContentConfig(
            temperature=self.temperature,
            automatic_function_calling=AutomaticFunctionCallingConfig(disable=True),
        )

        for attempt in range(MAX_RETRIES):
            try:
                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=config,
                )
                return response.text
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    delay = RETRY_DELAY_BASE * (2 ** attempt)
                    print(f"  [Rate limit] Retry {attempt + 1}/{MAX_RETRIES} dalam {delay}s...")
                    time.sleep(delay)
                    continue
                raise

        raise RuntimeError(f"Gagal setelah {MAX_RETRIES} retries: {error_msg}")
