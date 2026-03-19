from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import TypeVar

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ValidationError

import config

T = TypeVar("T", bound=BaseModel)


class StructuredLLMError(Exception):
    code = "structured_llm_error"
    user_message = "模型调用失败，请稍后重试。"

    def __init__(self, details: str = ""):
        super().__init__(details or self.user_message)
        self.details = details


# 这三类异常分别覆盖超时、结构化校验失败和 provider 调用失败。
class ModelTimeoutError(StructuredLLMError):
    code = "model_timeout"
    user_message = "模型响应超时，请稍后重试。"


class StructuredOutputError(StructuredLLMError):
    code = "structured_output_error"
    user_message = "模型返回格式异常，请稍后重试。"


class ProviderInvocationError(StructuredLLMError):
    code = "provider_invocation_error"
    user_message = "模型服务调用失败，请稍后重试。"


def should_use_openai_api() -> bool:
    return bool(config.OPENAI_API_KEY.strip())


async def invoke_structured(
    *,
    system_prompt: str,
    user_prompt: str,
    output_model: type[T],
) -> T:
    if should_use_openai_api():
        return await _invoke_with_openai(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            output_model=output_model,
        )

    return await _invoke_with_codex_cli(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        output_model=output_model,
    )


async def _invoke_with_openai(
    *,
    system_prompt: str,
    user_prompt: str,
    output_model: type[T],
) -> T:
    llm = ChatOpenAI(
        model=config.MODEL_NAME,
        api_key=config.OPENAI_API_KEY,
        base_url=config.OPENAI_API_BASE,
    )

    llm_with_structured_output = llm.with_structured_output(output_model)

    try:
        # 外层超时统一收口，避免单个 provider 卡住整个流式请求。
        return await asyncio.wait_for(
            llm_with_structured_output.ainvoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt),
                ]
            ),
            timeout=config.MODEL_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError as exc:
        raise ModelTimeoutError(
            f"OpenAI structured call exceeded {config.MODEL_TIMEOUT_SECONDS} seconds."
        ) from exc
    except ValidationError as exc:
        raise StructuredOutputError(
            f"OpenAI structured output validation failed: {exc}"
        ) from exc
    except StructuredLLMError:
        raise
    except Exception as exc:
        raise ProviderInvocationError(f"OpenAI invocation failed: {exc}") from exc


async def _invoke_with_codex_cli(
    *,
    system_prompt: str,
    user_prompt: str,
    output_model: type[T],
) -> T:
    schema_path = ""
    output_path = ""

    try:
        # 先让 Codex CLI 产出 JSON，再交给 Pydantic 做最终结构校验。
        # Codex CLI 对 JSON Schema 的要求更严格，object 节点要显式禁止额外字段。
        schema_path = _write_temp_json(_normalize_schema(output_model.model_json_schema()))
        output_path = _create_temp_output_file()

        prompt = _build_codex_prompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        codex_command = [
            _resolve_codex_cli_path(),
            "exec",
            "--skip-git-repo-check",
            "--ephemeral",
            "--color",
            "never",
            "--sandbox",
            "read-only",
            "--output-schema",
            schema_path,
            "-o",
            output_path,
            "-",
        ]

        if config.CODEX_MODEL_NAME:
            codex_command.extend(["--model", config.CODEX_MODEL_NAME])

        process_command = _build_process_command(codex_command)

        process = await asyncio.create_subprocess_exec(
            *process_command,
            cwd=str(Path(__file__).resolve().parents[1]),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(prompt.encode("utf-8")),
                timeout=config.MODEL_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError as exc:
            process.kill()
            await process.wait()
            raise ModelTimeoutError(
                f"Codex CLI call exceeded {config.MODEL_TIMEOUT_SECONDS} seconds."
            ) from exc

        if process.returncode != 0:
            error_message = stderr.decode("utf-8", errors="ignore").strip()
            stdout_message = stdout.decode("utf-8", errors="ignore").strip()
            raise ProviderInvocationError(
                "Codex CLI 调用失败。"
                f"\nstderr: {error_message or '<empty>'}"
                f"\nstdout: {stdout_message or '<empty>'}"
            )

        raw_output = Path(output_path).read_text(encoding="utf-8").strip()
        if not raw_output:
            raise StructuredOutputError("Codex CLI 没有写出结构化结果。")

        try:
            return output_model.model_validate_json(raw_output)
        except ValidationError as exc:
            raise StructuredOutputError(
                f"Codex CLI structured output validation failed: {exc}"
            ) from exc
    finally:
        _remove_file(schema_path)
        _remove_file(output_path)


def _build_codex_prompt(*, system_prompt: str, user_prompt: str) -> str:
    # 把系统提示词和用户输入拼成 Codex CLI 可直接消费的提示。
    return (
        "你正在为一个应用后端生成结构化数据。\n"
        "请严格遵守给定的 system instruction 和 user message。\n"
        "不要输出 Markdown，不要解释，不要补充 schema 之外的字段。\n\n"
        "[System Instruction]\n"
        f"{system_prompt}\n\n"
        "[User Message]\n"
        f"{user_prompt}\n"
    )


def _write_temp_json(payload: dict) -> str:
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".json",
        delete=False,
    ) as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        return file.name


def _normalize_schema(schema: dict) -> dict:
    if not isinstance(schema, dict):
        return schema

    normalized = {}
    for key, value in schema.items():
        if isinstance(value, dict):
            normalized[key] = _normalize_schema(value)
        elif isinstance(value, list):
            normalized[key] = [
                _normalize_schema(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            normalized[key] = value

    if normalized.get("type") == "object":
        # Codex CLI 不接受开放对象，必须显式关闭额外字段。
        normalized.setdefault("additionalProperties", False)

    return normalized


def _create_temp_output_file() -> str:
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as file:
        return file.name


def _remove_file(path: str) -> None:
    if path and os.path.exists(path):
        os.remove(path)


def _build_process_command(codex_command: list[str]) -> list[str]:
    if os.name != "nt":
        return codex_command

    # Windows 上用 `cmd.exe` 包一层调用 `codex.cmd`，避免直接执行脚本入口时报权限错误。
    return [
        "cmd.exe",
        "/d",
        "/s",
        "/c",
        subprocess.list2cmdline(codex_command),
    ]


def _resolve_codex_cli_path() -> str:
    configured_path = config.CODEX_CLI_PATH.strip()

    if configured_path:
        preferred_exe = shutil.which(configured_path)
        if preferred_exe:
            return preferred_exe

        if not configured_path.lower().endswith((".exe", ".cmd")):
            cmd_candidate = shutil.which(f"{configured_path}.cmd")
            if cmd_candidate:
                return cmd_candidate

            exe_candidate = shutil.which(f"{configured_path}.exe")
            if exe_candidate:
                return exe_candidate

        return configured_path

    fallback_cmd = shutil.which("codex.cmd")
    if fallback_cmd:
        return fallback_cmd

    fallback_exe = shutil.which("codex.exe")
    if fallback_exe:
        return fallback_exe

    fallback_path = shutil.which("codex")
    if fallback_path:
        return fallback_path

    return "codex"
