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
from profile_system.kernel_specimen import render_kernel_specimen
from profile_system.manifest import render_profile_manifest
from profile_system.model import (
    ProfileDataError,
    load_profile_snapshot,
)
from profile_system.observatory_scene import render_observatory_scene
from profile_system.probes import (
    ProbeDataError,
    load_svg_probe_snapshot,
)
from profile_system.scene import SceneDataError, load_observatory_scene
from profile_system.svg_document import render_svg_probe
from profile_system.svg_kernel import SvgKernelError
from profile_system.visual_grammar import render_visual_grammar


def _write_atomic(
    path: Path,
    content: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        text=True,
    )
    temporary_path = Path(temporary_name)

    try:
        with os.fdopen(
            descriptor,
            mode="w",
            encoding="utf-8",
            newline="\n",
        ) as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())

        os.replace(
            temporary_path,
            path,
        )
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


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

    kernel_parser = subparsers.add_parser("kernel")
    kernel_parser.add_argument(
        "--tokens",
        required=True,
        type=Path,
    )
    kernel_parser.add_argument(
        "--output",
        required=True,
        type=Path,
    )

    scene_parser = subparsers.add_parser("scene")
    scene_parser.add_argument(
        "--source",
        required=True,
        type=Path,
    )
    scene_parser.add_argument(
        "--tokens",
        required=True,
        type=Path,
    )
    scene_parser.add_argument(
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

        if arguments.command == "tokens":
            token_snapshot = load_design_token_snapshot(arguments.source)
            document = render_visual_grammar(token_snapshot)

            _write_atomic(
                arguments.output,
                document,
            )
            return 0

        if arguments.command == "kernel":
            token_snapshot = load_design_token_snapshot(arguments.tokens)
            document = render_kernel_specimen(token_snapshot)

            _write_atomic(
                arguments.output,
                document,
            )
            return 0

        if arguments.command == "scene":
            scene_snapshot = load_observatory_scene(arguments.source)
            token_snapshot = load_design_token_snapshot(arguments.tokens)
            document = render_observatory_scene(
                scene_snapshot,
                token_snapshot,
            )

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
        ProbeDataError,
        ProfileDataError,
        SceneDataError,
        SvgKernelError,
    ) as error:
        print(
            f"profile-system: {error}",
            file=sys.stderr,
        )
        return 2

    return 2
