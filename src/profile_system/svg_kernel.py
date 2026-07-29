from __future__ import annotations

import copy
import math
import re
import xml.etree.ElementTree as element_tree
from collections.abc import Mapping
from dataclasses import dataclass

SVG_NAMESPACE = "http://www.w3.org/2000/svg"
element_tree.register_namespace("", SVG_NAMESPACE)

IDENTIFIER_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
REFERENCE_PATTERN = re.compile(r"url\(#([a-z0-9-]+)\)")
STOP_OFFSET_PATTERN = re.compile(r"(?:0|[1-9][0-9]?|100)%")

SAFE_ELEMENTS = frozenset(
    {
        "circle",
        "clipPath",
        "defs",
        "desc",
        "feGaussianBlur",
        "feMerge",
        "feMergeNode",
        "filter",
        "g",
        "line",
        "linearGradient",
        "mask",
        "path",
        "radialGradient",
        "rect",
        "stop",
        "text",
        "title",
    }
)

SAFE_ATTRIBUTES = frozenset(
    {
        "aria-hidden",
        "aria-labelledby",
        "clip-path",
        "cx",
        "cy",
        "d",
        "dominant-baseline",
        "fill",
        "filter",
        "font-family",
        "font-size",
        "font-weight",
        "height",
        "id",
        "in",
        "letter-spacing",
        "mask",
        "maskContentUnits",
        "offset",
        "opacity",
        "r",
        "result",
        "role",
        "rx",
        "ry",
        "stdDeviation",
        "stop-color",
        "stop-opacity",
        "stroke",
        "stroke-dasharray",
        "stroke-linecap",
        "stroke-linejoin",
        "stroke-opacity",
        "stroke-width",
        "text-anchor",
        "transform",
        "vector-effect",
        "viewBox",
        "width",
        "x",
        "x1",
        "x2",
        "y",
        "y1",
        "y2",
    }
)


class SvgKernelError(ValueError):
    """Raised when renderer code violates the static SVG contract."""


@dataclass(frozen=True, slots=True)
class GradientStop:
    offset: str
    color: str
    opacity: float = 1.0


AttributeValue = str | int | float


def _tag(name: str) -> str:
    return f"{{{SVG_NAMESPACE}}}{name}"


def _attribute_value(value: object, context: str) -> str:
    if isinstance(value, bool):
        raise SvgKernelError(f"{context} must not contain a boolean")

    if isinstance(value, (int, float)):
        numeric = float(value)

        if not math.isfinite(numeric):
            raise SvgKernelError(f"{context} must contain a finite number")

        if isinstance(value, int) or numeric.is_integer():
            return str(int(numeric))

        return format(numeric, ".6g")

    if isinstance(value, str) and value:
        return value

    raise SvgKernelError(f"{context} must contain a non-empty scalar value")


class SvgDocument:
    def __init__(
        self,
        *,
        width: int,
        height: int,
        title: str,
        description: str,
    ) -> None:
        if width <= 0 or height <= 0:
            raise SvgKernelError("SVG dimensions must be positive integers")
        if not title.strip() or not description.strip():
            raise SvgKernelError("SVG title and description must be non-empty")

        self._identifiers: set[str] = set()
        self._references: set[str] = set()
        self._root = element_tree.Element(
            _tag("svg"),
            {
                "aria-labelledby": (
                    "renderer-kernel-title renderer-kernel-description"
                ),
                "height": str(height),
                "role": "img",
                "viewBox": f"0 0 {width} {height}",
                "width": str(width),
            },
        )
        self._register_identifier("renderer-kernel-title")
        self._register_identifier("renderer-kernel-description")
        title_node = element_tree.SubElement(
            self._root,
            _tag("title"),
            {"id": "renderer-kernel-title"},
        )
        title_node.text = title.strip()
        description_node = element_tree.SubElement(
            self._root,
            _tag("desc"),
            {"id": "renderer-kernel-description"},
        )
        description_node.text = description.strip()
        self._defs = element_tree.SubElement(
            self._root,
            _tag("defs"),
        )

    @property
    def root(self) -> element_tree.Element:
        return self._root

    @property
    def definitions(self) -> element_tree.Element:
        return self._defs

    def _register_identifier(self, identifier: str) -> None:
        if IDENTIFIER_PATTERN.fullmatch(identifier) is None:
            raise SvgKernelError("SVG identifiers must use lowercase kebab-case")
        if identifier in self._identifiers:
            raise SvgKernelError(f"Duplicate SVG identifier: {identifier}")

        self._identifiers.add(identifier)

    def element(
        self,
        parent: element_tree.Element,
        name: str,
        attributes: Mapping[str, AttributeValue] | None = None,
        *,
        text: str | None = None,
    ) -> element_tree.Element:
        if name not in SAFE_ELEMENTS:
            raise SvgKernelError(f"Unsupported SVG element: {name}")

        prepared: dict[str, str] = {}
        source_attributes: Mapping[str, AttributeValue] = (
            attributes if attributes is not None else {}
        )

        for attribute_name in sorted(source_attributes):
            raw_value = source_attributes[attribute_name]
            local_name = attribute_name.rsplit("}", 1)[-1]

            if local_name.lower().startswith("on"):
                raise SvgKernelError(
                    f"SVG event attributes are not permitted: {local_name}"
                )
            if local_name == "href":
                raise SvgKernelError("SVG href attributes are not permitted")
            if local_name not in SAFE_ATTRIBUTES and not local_name.startswith("data-"):
                raise SvgKernelError(f"Unsupported SVG attribute: {local_name}")

            value = _attribute_value(
                raw_value,
                f"SVG attribute {local_name}",
            )

            if local_name == "id":
                self._register_identifier(value)

            self._references.update(REFERENCE_PATTERN.findall(value))
            prepared[attribute_name] = value

        node = element_tree.SubElement(
            parent,
            _tag(name),
            prepared,
        )

        if text is not None:
            if not text:
                raise SvgKernelError("SVG text content must not be empty")
            node.text = text

        return node

    def define_linear_gradient(
        self,
        identifier: str,
        *,
        stops: tuple[GradientStop, ...],
        x1: str = "0%",
        y1: str = "0%",
        x2: str = "100%",
        y2: str = "0%",
    ) -> element_tree.Element:
        gradient = self.element(
            self._defs,
            "linearGradient",
            {
                "id": identifier,
                "x1": x1,
                "x2": x2,
                "y1": y1,
                "y2": y2,
            },
        )
        self._append_stops(gradient, stops)
        return gradient

    def define_radial_gradient(
        self,
        identifier: str,
        *,
        stops: tuple[GradientStop, ...],
        cx: str = "50%",
        cy: str = "50%",
        radius: str = "50%",
    ) -> element_tree.Element:
        gradient = self.element(
            self._defs,
            "radialGradient",
            {
                "cx": cx,
                "cy": cy,
                "id": identifier,
                "r": radius,
            },
        )
        self._append_stops(gradient, stops)
        return gradient

    def _append_stops(
        self,
        gradient: element_tree.Element,
        stops: tuple[GradientStop, ...],
    ) -> None:
        if len(stops) < 2:
            raise SvgKernelError("SVG gradients require at least two stops")

        offsets: list[int] = []

        for stop in stops:
            if STOP_OFFSET_PATTERN.fullmatch(stop.offset) is None:
                raise SvgKernelError(
                    "Gradient stop offset must use an integer percentage"
                )
            if not 0 <= stop.opacity <= 1:
                raise SvgKernelError(
                    "Gradient stop opacity must be between zero and one"
                )

            offsets.append(int(stop.offset[:-1]))
            self.element(
                gradient,
                "stop",
                {
                    "offset": stop.offset,
                    "stop-color": stop.color,
                    "stop-opacity": stop.opacity,
                },
            )

        if offsets != sorted(offsets) or len(offsets) != len(set(offsets)):
            raise SvgKernelError("Gradient stop offsets must be unique and increasing")

    def define_clip_rect(
        self,
        identifier: str,
        *,
        x: AttributeValue,
        y: AttributeValue,
        width: AttributeValue,
        height: AttributeValue,
        radius: AttributeValue,
    ) -> element_tree.Element:
        clip_path = self.element(
            self._defs,
            "clipPath",
            {"id": identifier},
        )
        self.element(
            clip_path,
            "rect",
            {
                "height": height,
                "rx": radius,
                "width": width,
                "x": x,
                "y": y,
            },
        )
        return clip_path

    def define_alpha_mask(
        self,
        identifier: str,
        *,
        gradient_id: str,
    ) -> element_tree.Element:
        mask = self.element(
            self._defs,
            "mask",
            {
                "id": identifier,
                "maskContentUnits": "objectBoundingBox",
            },
        )
        self.element(
            mask,
            "rect",
            {
                "fill": f"url(#{gradient_id})",
                "height": 1,
                "width": 1,
                "x": 0,
                "y": 0,
            },
        )
        return mask

    def define_glow_filter(
        self,
        identifier: str,
        *,
        blur: AttributeValue,
    ) -> element_tree.Element:
        filter_node = self.element(
            self._defs,
            "filter",
            {
                "height": "200%",
                "id": identifier,
                "width": "200%",
                "x": "-50%",
                "y": "-50%",
            },
        )
        self.element(
            filter_node,
            "feGaussianBlur",
            {
                "result": "kernel-blur",
                "stdDeviation": blur,
            },
        )
        merge = self.element(filter_node, "feMerge")
        self.element(
            merge,
            "feMergeNode",
            {"in": "kernel-blur"},
        )
        self.element(
            merge,
            "feMergeNode",
            {"in": "SourceGraphic"},
        )
        return filter_node

    def serialize(self) -> str:
        unresolved = sorted(self._references - self._identifiers)

        if unresolved:
            raise SvgKernelError("Unresolved SVG references: " + ", ".join(unresolved))

        root_copy = copy.deepcopy(self._root)
        element_tree.indent(root_copy, space="  ")
        return (
            element_tree.tostring(
                root_copy,
                encoding="unicode",
                short_empty_elements=True,
            )
            + "\n"
        )
