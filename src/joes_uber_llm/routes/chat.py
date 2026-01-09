"""Chat API routes."""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Annotated

from fastapi import APIRouter, Form, Header, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from joes_uber_llm.config import PROVIDER_MODELS
from joes_uber_llm.providers import AnthropicProvider, GoogleProvider, OpenAIProvider
from joes_uber_llm.providers.base import BaseProvider, Message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")
templates = Jinja2Templates(directory="src/joes_uber_llm/templates")

# In-memory conversation storage (keyed by session_id, then by provider)
# Structure: {session_id: {provider: [Message, ...]}}
conversations: dict[str, dict[str, list[Message]]] = {}

# Provider instances
PROVIDERS: dict[str, BaseProvider] = {
    "openai": OpenAIProvider(),
    "anthropic": AnthropicProvider(),
    "google": GoogleProvider(),
}


@dataclass
class ProviderResponse:
    """Response from a single provider."""

    provider: str
    model: str
    response: str
    elapsed_ms: int
    order: int = 0


def get_or_create_session(session_id: str | None) -> str:
    """Get existing session ID or create a new one.

    Args:
        session_id: Existing session ID or None.

    Returns:
        Valid session ID string.
    """
    if session_id and session_id in conversations:
        return session_id
    new_id = str(uuid.uuid4())
    conversations[new_id] = {}
    return new_id


def get_provider_conversation(session_id: str, provider: str) -> list[Message]:
    """Get or create conversation history for a specific provider.

    Args:
        session_id: Session identifier.
        provider: Provider name.

    Returns:
        List of messages for this provider's conversation.
    """
    if provider not in conversations[session_id]:
        conversations[session_id][provider] = []
    return conversations[session_id][provider]


@router.post("/chat", response_class=HTMLResponse)
async def chat(
    request: Request,
    message: Annotated[str, Form()],
    provider: Annotated[str, Form()],
    model: Annotated[str, Form()],
    x_api_key: Annotated[str | None, Header()] = None,
    x_session_id: Annotated[str | None, Header()] = None,
) -> HTMLResponse:
    """Process a chat message and return the response.

    Args:
        request: FastAPI request object.
        message: User's message content.
        provider: LLM provider name (openai, anthropic, google).
        model: Model identifier.
        x_api_key: API key from request header.
        x_session_id: Session ID from request header.

    Returns:
        HTML partial containing the user message and assistant response.

    Raises:
        HTTPException: If API key is missing or provider is invalid.
    """
    if not x_api_key:
        raise HTTPException(status_code=400, detail="API key required")

    if provider not in PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider. Use: {list(PROVIDERS.keys())}",
        )

    if model not in PROVIDER_MODELS.get(provider, []):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model for {provider}. Use: {PROVIDER_MODELS[provider]}",
        )

    session_id = get_or_create_session(x_session_id)
    conversation = conversations[session_id]

    # Add user message to conversation
    user_msg = Message(role="user", content=message)
    conversation.append(user_msg)

    # Get response from provider
    provider_instance = PROVIDERS[provider]
    try:
        response_text = await provider_instance.chat(
            messages=conversation,
            model=model,
            api_key=x_api_key,
        )
    except (ValueError, RuntimeError) as e:
        logger.error("Chat error: %s", e)
        # Remove user message on error
        conversation.pop()
        raise HTTPException(status_code=500, detail=str(e)) from e

    # Add assistant response to conversation
    assistant_msg = Message(role="assistant", content=response_text)
    conversation.append(assistant_msg)

    return templates.TemplateResponse(
        "partials/message.html",
        {
            "request": request,
            "user_message": message,
            "assistant_message": response_text,
            "session_id": session_id,
        },
    )


@router.post("/clear", response_class=HTMLResponse)
async def clear_conversation(
    request: Request,
    x_session_id: Annotated[str | None, Header()] = None,
) -> HTMLResponse:
    """Clear the conversation history.

    Args:
        request: FastAPI request object.
        x_session_id: Session ID from request header.

    Returns:
        Empty HTML response.
    """
    if x_session_id and x_session_id in conversations:
        # Clear all provider conversations for this session
        conversations[x_session_id] = {}

    return HTMLResponse(content="", status_code=200)


@router.post("/validate-key")
async def validate_api_key(
    provider: Annotated[str, Form()],
    api_key: Annotated[str, Form()],
) -> dict[str, bool]:
    """Validate an API key for a provider.

    Args:
        provider: LLM provider name (openai, anthropic, google).
        api_key: API key to validate.

    Returns:
        Dictionary with valid boolean.
    """
    if provider not in PROVIDERS:
        return {"valid": False}

    if not api_key or len(api_key) < 10:
        return {"valid": False}

    provider_instance = PROVIDERS[provider]
    test_message = [Message(role="user", content="Hi")]

    try:
        # Make a minimal request to validate the key
        await provider_instance.chat(
            messages=test_message,
            model=provider_instance.available_models[0],
            api_key=api_key,
        )
        return {"valid": True}
    except (ValueError, RuntimeError) as e:
        logger.warning("API key validation failed for %s: %s", provider, e)
        return {"valid": False}


@router.get("/models/{provider}")
async def get_models(provider: str) -> dict[str, list[str]]:
    """Get available models for a provider.

    Args:
        provider: Provider name.

    Returns:
        Dictionary with models list.

    Raises:
        HTTPException: If provider is invalid.
    """
    if provider not in PROVIDER_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider. Use: {list(PROVIDER_MODELS.keys())}",
        )

    return {"models": PROVIDER_MODELS[provider]}


async def _call_provider(
    provider_name: str,
    model: str,
    api_key: str,
    session_id: str,
    user_message: str,
    start_time: float,
) -> ProviderResponse | None:
    """Call a single provider and return response with timing.

    Args:
        provider_name: Name of the provider.
        model: Model identifier.
        api_key: API key for the provider.
        session_id: Session identifier for conversation history.
        user_message: The user's message content.
        start_time: Start timestamp for elapsed time calculation.

    Returns:
        ProviderResponse if successful, None if failed.
    """
    provider_instance = PROVIDERS.get(provider_name)
    if not provider_instance:
        return None

    # Get this provider's conversation history
    conversation = get_provider_conversation(session_id, provider_name)

    # Add user message to this provider's conversation
    user_msg = Message(role="user", content=user_message)
    conversation.append(user_msg)

    try:
        response_text = await provider_instance.chat(
            messages=conversation,
            model=model,
            api_key=api_key,
        )

        # Add assistant response to this provider's conversation
        assistant_msg = Message(role="assistant", content=response_text)
        conversation.append(assistant_msg)

        elapsed_ms = int((time.time() - start_time) * 1000)
        return ProviderResponse(
            provider=provider_name,
            model=model,
            response=response_text,
            elapsed_ms=elapsed_ms,
        )
    except (ValueError, RuntimeError) as e:
        logger.error("Provider %s error: %s", provider_name, e)
        # Remove the user message if the call failed
        conversation.pop()
        return None


@router.post("/chat-multi", response_class=HTMLResponse)
async def chat_multi(
    request: Request,
    message: Annotated[str, Form()],
    providers: Annotated[str, Form()],
    models: Annotated[str, Form()],
    api_keys: Annotated[str, Form()],
    x_session_id: Annotated[str | None, Header()] = None,
) -> HTMLResponse:
    """Process a chat message to multiple providers in parallel.

    Args:
        request: FastAPI request object.
        message: User's message content.
        providers: Comma-separated list of provider names.
        models: Comma-separated list of model identifiers (same order as providers).
        api_keys: Comma-separated list of API keys (same order as providers).
        x_session_id: Session ID from request header.

    Returns:
        HTML partial containing the user message and all assistant responses.
    """
    provider_list = [p.strip() for p in providers.split(",") if p.strip()]
    model_list = [m.strip() for m in models.split(",") if m.strip()]
    api_key_list = [k.strip() for k in api_keys.split(",") if k.strip()]

    if not provider_list:
        raise HTTPException(status_code=400, detail="No active providers")

    if len(provider_list) != len(model_list) or len(provider_list) != len(api_key_list):
        raise HTTPException(status_code=400, detail="Mismatched provider/model/key lists")

    session_id = get_or_create_session(x_session_id)

    # Create tasks for all providers (each manages its own conversation)
    start_time = time.time()
    tasks = [
        _call_provider(provider, model, api_key, session_id, message, start_time)
        for provider, model, api_key in zip(provider_list, model_list, api_key_list)
    ]

    # Run all tasks concurrently
    results = await asyncio.gather(*tasks)

    # Filter successful results and sort by elapsed time (fastest first)
    responses: list[ProviderResponse] = [r for r in results if r is not None]
    responses.sort(key=lambda x: x.elapsed_ms)

    # Assign order based on response time
    for i, resp in enumerate(responses):
        resp.order = i + 1

    # If all providers failed, return error
    if not responses:
        raise HTTPException(status_code=500, detail="All providers failed to respond")

    response = templates.TemplateResponse(
        "partials/multi_response.html",
        {
            "request": request,
            "user_message": message,
            "responses": responses,
            "session_id": session_id,
        },
    )
    response.headers["X-Session-ID"] = session_id
    return response


AGGREGATOR_SYSTEM_PROMPT = """You are an expert answer aggregator. You will be given a user's question and multiple responses from different AI assistants.

Your task is to:
1. Synthesize the best parts of all responses into one superior, comprehensive answer
2. Give more weight to higher quality responses when combining
3. Rate each response from 1-10 based on accuracy, completeness, and helpfulness
4. Identify any responses that contain hallucinations or wildly inconsistent information

Format your response EXACTLY as follows:

## Uber Answer
[Your synthesized, superior answer that combines the best elements from all responses. This should be comprehensive and well-formatted.]

## Response Ratings
- [Provider 1]: [X/10] - [Brief reason]
- [Provider 2]: [X/10] - [Brief reason]
- [Provider 3]: [X/10] - [Brief reason]

## Hallucination Check
[Note any responses with potentially false or inconsistent information, or state "No hallucinations detected"]"""


@router.post("/aggregate")
async def aggregate_responses(
    request: Request,
    user_question: Annotated[str, Form()],
    responses_json: Annotated[str, Form()],
    aggregator_provider: Annotated[str, Form()],
    aggregator_model: Annotated[str, Form()],
    aggregator_api_key: Annotated[str, Form()],
) -> dict:
    """Aggregate multiple LLM responses into one superior answer.

    Args:
        request: FastAPI request object.
        user_question: The original user question.
        responses_json: JSON string of provider responses.
        aggregator_provider: Provider to use for aggregation.
        aggregator_model: Model to use for aggregation.
        aggregator_api_key: API key for the aggregator provider.

    Returns:
        Dictionary with the aggregated response.
    """
    import json

    try:
        responses_data = json.loads(responses_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid responses JSON")

    if aggregator_provider not in PROVIDERS:
        raise HTTPException(status_code=400, detail="Invalid aggregator provider")

    # Build the prompt for the aggregator
    responses_text = ""
    for resp in responses_data:
        responses_text += f"\n### {resp['provider'].upper()} ({resp['model']}):\n{resp['response']}\n"

    aggregator_prompt = f"""User's Question: {user_question}

Here are the responses from different AI assistants:
{responses_text}

Please analyze these responses and provide your aggregated answer following the format specified."""

    # Call the aggregator LLM
    provider_instance = PROVIDERS[aggregator_provider]
    messages = [
        Message(role="system", content=AGGREGATOR_SYSTEM_PROMPT),
        Message(role="user", content=aggregator_prompt),
    ]

    try:
        aggregated_response = await provider_instance.chat(
            messages=messages,
            model=aggregator_model,
            api_key=aggregator_api_key,
        )
        return {"success": True, "response": aggregated_response}
    except (ValueError, RuntimeError) as e:
        logger.error("Aggregator error: %s", e)
        return {"success": False, "error": str(e)}
