#!/usr/bin/env python3
"""Export the repository's 3MF enclosure mesh as binary STL and faceted STEP.

The 3MF also contains board-context geometry for visualisation.  By default,
the exporter selects its dedicated 94 x 63 x 5 mm enclosure body (object 57),
not that full assembly.  This keeps the downstream fabrication exports
reproducible without changing the 3MF source.  The STEP output is intentionally
faceted: it preserves the exact triangulated geometry for CAD viewing and
reference, rather than claiming to recreate unavailable parametric features.
"""

from __future__ import annotations

import argparse
import math
import struct
import xml.etree.ElementTree as ET
import zipfile
from collections.abc import Iterable
from pathlib import Path


CORE_NS = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
NS = {"m": CORE_NS}


def matrix_from_transform(value: str | None) -> tuple[float, ...]:
    """Return a row-major affine 3MF transform matrix."""
    if not value:
        return (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
    result = tuple(float(item) for item in value.split())
    if len(result) != 12:
        raise ValueError(f"Expected 12 transform values, received {len(result)}")
    return result


def multiply(left: tuple[float, ...], right: tuple[float, ...]) -> tuple[float, ...]:
    """Compose two 3x4 affine matrices (left * right)."""
    values: list[float] = []
    for row in range(3):
        base = row * 4
        for column in range(4):
            if column == 3:
                values.append(
                    left[base] * right[3]
                    + left[base + 1] * right[7]
                    + left[base + 2] * right[11]
                    + left[base + 3]
                )
            else:
                values.append(
                    left[base] * right[column]
                    + left[base + 1] * right[column + 4]
                    + left[base + 2] * right[column + 8]
                )
    return tuple(values)


def transform_point(point: tuple[float, float, float], matrix: tuple[float, ...]) -> tuple[float, float, float]:
    x, y, z = point
    return (
        matrix[0] * x + matrix[1] * y + matrix[2] * z + matrix[3],
        matrix[4] * x + matrix[5] * y + matrix[6] * z + matrix[7],
        matrix[8] * x + matrix[9] * y + matrix[10] * z + matrix[11],
    )


def load_triangles(
    source: Path, object_ids: set[str] | None = None
) -> list[tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]]:
    with zipfile.ZipFile(source) as archive:
        document = ET.fromstring(archive.read("3D/3dmodel.model"))

    objects = {node.attrib["id"]: node for node in document.findall(".//m:resources/m:object", NS)}
    triangles: list[tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]] = []

    def visit(object_id: str, transform: tuple[float, ...]) -> None:
        node = objects[object_id]
        mesh = node.find("m:mesh", NS)
        if mesh is not None:
            vertices = [
                (float(vertex.attrib["x"]), float(vertex.attrib["y"]), float(vertex.attrib["z"]))
                for vertex in mesh.findall("m:vertices/m:vertex", NS)
            ]
            for triangle in mesh.findall("m:triangles/m:triangle", NS):
                index = (int(triangle.attrib["v1"]), int(triangle.attrib["v2"]), int(triangle.attrib["v3"]))
                triangles.append(tuple(transform_point(vertices[item], transform) for item in index))
        for component in node.findall("m:components/m:component", NS):
            visit(component.attrib["objectid"], multiply(transform, matrix_from_transform(component.get("transform"))))

    if object_ids is None:
        for item in document.findall("m:build/m:item", NS):
            visit(item.attrib["objectid"], matrix_from_transform(item.get("transform")))
    else:
        unknown = object_ids.difference(objects)
        if unknown:
            raise ValueError(f"Unknown 3MF object ID(s): {', '.join(sorted(unknown))}")
        for object_id in object_ids:
            visit(object_id, matrix_from_transform(None))
    return triangles


def normal(triangle: tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]) -> tuple[float, float, float]:
    first, second, third = triangle
    ax, ay, az = (second[index] - first[index] for index in range(3))
    bx, by, bz = (third[index] - first[index] for index in range(3))
    cross = (ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx)
    length = math.sqrt(sum(item * item for item in cross))
    return (0.0, 0.0, 0.0) if length == 0 else tuple(item / length for item in cross)


def write_stl(destination: Path, triangles: Iterable[tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]]) -> None:
    faces = list(triangles)
    with destination.open("wb") as handle:
        handle.write(b"Digital ID Card V1 enclosure - exported from case.3mf".ljust(80, b"\0"))
        handle.write(struct.pack("<I", len(faces)))
        for face in faces:
            handle.write(struct.pack("<3f", *normal(face)))
            for vertex in face:
                handle.write(struct.pack("<3f", *vertex))
            handle.write(struct.pack("<H", 0))


def step_number(value: float) -> str:
    return f"{value:.6f}".rstrip("0").rstrip(".") or "0"


def write_step(destination: Path, triangles: Iterable[tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]]) -> None:
    """Write a broadly supported AP214 faceted B-rep STEP file."""
    faces = list(triangles)
    points: dict[tuple[float, float, float], int] = {}
    identifiers = 16

    def point_id(point: tuple[float, float, float]) -> int:
        nonlocal identifiers
        key = tuple(round(value, 6) for value in point)
        if key not in points:
            points[key] = identifiers
            identifiers += 1
        return points[key]

    face_points = [tuple(point_id(vertex) for vertex in face) for face in faces]
    bounds: list[int] = []
    with destination.open("w", encoding="ascii", newline="\n") as handle:
        handle.write("ISO-10303-21;\nHEADER;\n")
        handle.write("FILE_DESCRIPTION(('Faceted enclosure export from case.3mf'),'2;1');\n")
        handle.write("FILE_NAME('case.step','2026-07-21T00:00:00',(''),(''),'Digital ID Card V1','','');\n")
        handle.write("FILE_SCHEMA(('AUTOMOTIVE_DESIGN_CC2'));\nENDSEC;\nDATA;\n")
        handle.write("#1=APPLICATION_CONTEXT('automotive design');\n")
        handle.write("#2=APPLICATION_PROTOCOL_DEFINITION('international standard','automotive_design',2010,#1);\n")
        handle.write("#3=PRODUCT_CONTEXT('',#1,'mechanical');\n#4=PRODUCT('case','Digital ID Card V1 enclosure','',(#3));\n")
        handle.write("#5=PRODUCT_DEFINITION_FORMATION('','',#4);\n#6=PRODUCT_DEFINITION('design','',#5,#7);\n")
        handle.write("#7=PRODUCT_DEFINITION_CONTEXT('part definition',#1,'design');\n#8=PRODUCT_DEFINITION_SHAPE('','',#6);\n")
        handle.write("#10=(GEOMETRIC_REPRESENTATION_CONTEXT(3) GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT((#11)) GLOBAL_UNIT_ASSIGNED_CONTEXT((#12,#13,#14)) REPRESENTATION_CONTEXT('Context','3D'));\n")
        handle.write("#11=UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(1.E-6),#12,'distance_accuracy_value','');\n")
        handle.write("#12=(LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.MILLI.,.METRE.));\n#13=(PLANE_ANGLE_UNIT() NAMED_UNIT(*) SI_UNIT($,.RADIAN.));\n#14=(SOLID_ANGLE_UNIT() NAMED_UNIT(*) SI_UNIT($,.STERADIAN.));\n")
        for point, identifier in points.items():
            handle.write(f"#{identifier}=CARTESIAN_POINT('',({','.join(step_number(value) for value in point)}));\n")
        for face in face_points:
            loop_id, bound_id, face_id = identifiers, identifiers + 1, identifiers + 2
            identifiers += 3
            handle.write(f"#{loop_id}=POLY_LOOP('',(#{face[0]},#{face[1]},#{face[2]}));\n")
            handle.write(f"#{bound_id}=FACE_OUTER_BOUND('',#{loop_id},.T.);\n")
            handle.write(f"#{face_id}=FACETED_FACE('',(#{bound_id}));\n")
            bounds.append(face_id)
        shell_id, brep_id, shape_id = identifiers, identifiers + 1, identifiers + 2
        handle.write(f"#{shell_id}=CLOSED_SHELL('',({','.join(f'#{item}' for item in bounds)}));\n")
        handle.write(f"#{brep_id}=FACETED_BREP('Digital ID Card V1 enclosure',#{shell_id});\n")
        handle.write(f"#15=SHAPE_REPRESENTATION('case', (#{brep_id}), #10);\n")
        handle.write(f"#{shape_id}=SHAPE_DEFINITION_REPRESENTATION(#8,#15);\n")
        handle.write("ENDSEC;\nEND-ISO-10303-21;\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path, default=Path(__file__).with_name("case.3mf"))
    parser.add_argument("--stl", type=Path, default=Path(__file__).with_name("case.stl"))
    parser.add_argument("--step", type=Path, default=Path(__file__).with_name("case.step"))
    parser.add_argument(
        "--object-id",
        action="append",
        default=None,
        help="3MF object ID to export; may be supplied more than once (default: 57, the enclosure body).",
    )
    parser.add_argument(
        "--all-build-items",
        action="store_true",
        help="Export the full 3MF assembly instead of only the enclosure body.",
    )
    args = parser.parse_args()

    if args.all_build_items and args.object_id:
        parser.error("--all-build-items cannot be combined with --object-id")
    object_ids = None if args.all_build_items else set(args.object_id or ["57"])
    faces = load_triangles(args.source, object_ids)
    if not faces:
        raise SystemExit("No build triangles found in the supplied 3MF file.")
    write_stl(args.stl, faces)
    write_step(args.step, faces)
    print(f"Exported {len(faces)} triangles to {args.stl} and {args.step}.")


if __name__ == "__main__":
    main()
