import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

# Tiered models. Cheap ones do the easy work, the strong one handles
# planning and code generation. Override any of these in .env.
#
# These three all sit inside the Gemini free tier. The Pro models are
# better at the "high" jobs but the free tier rate limits them, so they
# are only worth setting once the key has billing on it.
MODELS = {
    "low": os.getenv("LLM_MODEL_LOW", "gemini-3.5-flash-lite"),
    "medium": os.getenv("LLM_MODEL_MEDIUM", "gemini-3.5-flash"),
    "high": os.getenv("LLM_MODEL_HIGH", "gemini-3.5-flash"),
}


def pick_llm(level: str):
    """
    Picks the appropriate LLM based on the level of the question.

    Args:
        level (str): The level of the question, can be "low", "medium", or "high".

    Returns:
        ChatGoogleGenerativeAI: The LLM instance to be used.
    """
    level = level.lower()

    if level not in MODELS:
        raise ValueError(f"Unsupported level: {level}")

    return ChatGoogleGenerativeAI(
        model=MODELS[level],
        google_api_key=os.environ["GOOGLE_API_KEY"],
    )


if __name__ == "__main__":
    for tier in MODELS:
        print(tier, "->", MODELS[tier], "->", pick_llm(tier).invoke("Say OK only.").text)
