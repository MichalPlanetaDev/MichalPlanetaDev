from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

from profile_system.design_tokens import (
    DesignTokenError,
    load_design_token_snapshot,
)
from profile_system.frontend_design_tokens import (
    render_frontend_design_css,
    render_frontend_design_typescript,
    resolve_frontend_design_tokens,
)
from profile_system.frontend_snapshot import render_frontend_snapshot
from profile_system.manifest import render_profile_manifest
from profile_system.model import (
    ProfileDataError,
    load_profile_snapshot,
)
from profile_system.probes import (
    ProbeDataError,
    load_svg_probe_snapshot,
)
from profile_system.svg_document import render_svg_probe
from profile_system.visual_grammar import render_visual_grammar


class OutputTransactionError(ValueError):
    """Raised when related generated outputs cannot be updated consistently."""


def _prepare_sibling_file(
    path: Path,
    content: bytes,
    *,
    purpose: str,
) -> Path:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.{purpose}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)

    try:
        with os.fdopen(
            descriptor,
            mode="wb",
        ) as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise

    return temporary_path


def _write_atomic(
    path: Path,
    content: str,
) -> None:
    temporary_path = _prepare_sibling_file(
        path,
        content.encode("utf-8"),
        purpose="write",
    )

    try:
        os.replace(
            temporary_path,
            path,
        )
    finally:
        temporary_path.unlink(missing_ok=True)


def _restore_destination(
    path: Path,
    rollback_path: Path | None,
    *,
    existed: bool,
) -> None:
    if existed:
        if rollback_path is None:
            raise OutputTransactionError(
                f"Missing rollback file for existing output: {path}"
            )
        os.replace(rollback_path, path)
        return

    path.unlink(missing_ok=True)


def _require_distinct_output_paths(
    first_path: Path,
    second_path: Path,
) -> None:
    if first_path.resolve() == second_path.resolve():
        raise OutputTransactionError(
            "Frontend token CSS and TypeScript outputs must use distinct paths: "
            f"{first_path}"
        )


def _write_atomic_pair(
    first_path: Path,
    first_content: str,
    second_path: Path,
    second_content: str,
) -> None:
    _require_distinct_output_paths(first_path, second_path)

    first_existed = first_path.exists()
    second_existed = second_path.exists()
    first_temporary: Path | None = None
    second_temporary: Path | None = None
    first_rollback: Path | None = None
    second_rollback: Path | None = None
    first_replaced = False
    second_replaced = False

    try:
        first_temporary = _prepare_sibling_file(
            first_path,
            first_content.encode("utf-8"),
            purpose="write",
        )
        second_temporary = _prepare_sibling_file(
            second_path,
            second_content.encode("utf-8"),
            purpose="write",
        )

        if first_existed:
            first_rollback = _prepare_sibling_file(
                first_path,
                first_path.read_bytes(),
                purpose="rollback",
            )
        if second_existed:
            second_rollback = _prepare_sibling_file(
                second_path,
                second_path.read_bytes(),
                purpose="rollback",
            )

        os.replace(first_temporary, first_path)
        first_temporary = None
        first_replaced = True

        os.replace(second_temporary, second_path)
        second_temporary = None
        second_replaced = True
    except BaseException as write_error:
        rollback_errors: list[str] = []

        if second_replaced:
            try:
                _restore_destination(
                    second_path,
                    second_rollback,
                    existed=second_existed,
                )
                second_rollback = None
            except BaseException as rollback_error:
                rollback_errors.append(f"{second_path}: {rollback_error}")

        if first_replaced:
            try:
                _restore_destination(
                    first_path,
                    first_rollback,
                    existed=first_existed,
                )
                first_rollback = None
            except BaseException as rollback_error:
                rollback_errors.append(f"{first_path}: {rollback_error}")

        if rollback_errors:
            details = "; ".join(rollback_errors)
            raise OutputTransactionError(
                "Frontend token generation failed during output replacement "
                f"({write_error}); rollback was incomplete: {details}"
            ) from write_error

        raise
    finally:
        for temporary_path in (
            first_temporary,
            second_temporary,
            first_rollback,
            second_rollback,
        ):
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="profile-system")
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    build_parser = subparsers.add_parser("build")
    build_parser.add_argument(
        "--source",
        required=True,
        type=Path,
    )
    build_parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
    )

    frontend_parser = subparsers.add_parser("frontend")
    frontend_parser.add_argument(
        "--source",
        required=True,
        type=Path,
    )
    frontend_parser.add_argument(
        "--output",
        required=True,
        type=Path,
    )

    frontend_tokens_parser = subparsers.add_parser("frontend-tokens")
    frontend_tokens_parser.add_argument(
        "--source",
        required=True,
        type=Path,
    )
    frontend_tokens_parser.add_argument(
        "--css-output",
        required=True,
        type=Path,
    )
    frontend_tokens_parser.add_argument(
        "--typescript-output",
        required=True,
        type=Path,
    )

    tokens_parser = subparsers.add_parser("tokens")
    tokens_parser.add_argument(
        "--source",
        required=True,
        type=Path,
    )
    tokens_parser.add_argument(
        "--output",
        required=True,
        type=Path,
    )

    probe_parser = subparsers.add_parser("probe")
    probe_parser.add_argument(
        "--source",
        required=True,
        type=Path,
    )
    probe_parser.add_argument(
        "--output",
        required=True,
        type=Path,
    )

    return parser


def main(
    argv: Sequence[str] | None = None,
) -> int:
    arguments = _parser().parse_args(argv)

    try:
        if arguments.command == "build":
            profile_snapshot = load_profile_snapshot(arguments.source)
            manifest = render_profile_manifest(profile_snapshot)

            _write_atomic(
                arguments.output_dir / "profile-manifest.json",
                manifest,
            )
            return 0

        if arguments.command == "frontend":
            profile_snapshot = load_profile_snapshot(arguments.source)
            document = render_frontend_snapshot(profile_snapshot)

            _write_atomic(
                arguments.output,
                document,
            )
            return 0

        if arguments.command == "frontend-tokens":
            _require_distinct_output_paths(
                arguments.css_output,
                arguments.typescript_output,
            )
            token_snapshot = load_design_token_snapshot(arguments.source)
            frontend_tokens = resolve_frontend_design_tokens(token_snapshot)
            css_document = render_frontend_design_css(frontend_tokens)
            typescript_document = render_frontend_design_typescript(frontend_tokens)

            _write_atomic_pair(
                arguments.css_output,
                css_document,
                arguments.typescript_output,
                typescript_document,
            )
            return 0

        if arguments.command == "tokens":
            token_snapshot = load_design_token_snapshot(arguments.source)
            document = render_visual_grammar(token_snapshot)

            _write_atomic(
                arguments.output,
                document,
            )
            return 0

        if arguments.command == "probe":
            probe_snapshot = load_svg_probe_snapshot(arguments.source)
            document = render_svg_probe(probe_snapshot)

            _write_atomic(
                arguments.output,
                document,
            )
            return 0

    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        DesignTokenError,
        OutputTransactionError,
        ProbeDataError,
        ProfileDataError,
    ) as error:
        print(
            f"profile-system: {error}",
            file=sys.stderr,
        )
        return 2

    return 2
