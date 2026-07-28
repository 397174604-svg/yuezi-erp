import argparse
import csv
import math
from pathlib import Path

from PIL import Image, ImageChops


def content_bbox(image: Image.Image):
    rgb = image.convert("RGB")
    white = Image.new("RGB", rgb.size, (255, 255, 255))
    return ImageChops.difference(rgb, white).getbbox() or (0, 0, *rgb.size)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    pages = [
        path
        for path in input_dir.glob("*.png")
        if "contact" not in path.stem
    ]
    groups = {}
    for path in pages:
        prefix, page_text = path.stem.rsplit("-", 1)
        if page_text.isdigit():
            groups.setdefault(prefix, []).append(path)

    group_codes = {}
    for prefix, paths in groups.items():
        widest = max(Image.open(path).width for path in paths)
        group_codes[prefix] = "JS" if widest > 10000 else "HHL"

    manifest_rows = []
    for prefix, paths in sorted(groups.items()):
        store_code = group_codes[prefix]
        for source_path in sorted(
            paths, key=lambda path: int(path.stem.rsplit("-", 1)[1])
        ):
            page_no = int(source_path.stem.rsplit("-", 1)[1])
            image = Image.open(source_path).convert("RGB")
            left, top, right, bottom = content_bbox(image)
            left = max(0, left - 20)
            top = max(0, top - 20)
            right = min(image.width, right + 20)
            bottom = min(image.height, bottom + 20)
            content_width = right - left
            content_height = bottom - top

            max_segment_width = 5800
            overlap = 160
            segment_count = max(
                1,
                math.ceil(
                    max(0, content_width - overlap)
                    / (max_segment_width - overlap)
                ),
            )

            for segment_index in range(segment_count):
                segment_left = left + segment_index * (max_segment_width - overlap)
                segment_right = min(right, segment_left + max_segment_width)
                segment = image.crop((segment_left, top, segment_right, bottom))

                scale = min(
                    2.2,
                    9000 / segment.width,
                    9000 / segment.height,
                )
                scale = max(1.0, scale)
                if scale != 1.0:
                    segment = segment.resize(
                        (
                            round(segment.width * scale),
                            round(segment.height * scale),
                        ),
                        Image.Resampling.LANCZOS,
                    )

                output_name = (
                    f"{store_code}-p{page_no:02d}-s{segment_index + 1:02d}.png"
                )
                output_path = output_dir / output_name
                segment.save(output_path)

                manifest_rows.append(
                    {
                        "store_code": store_code,
                        "source_name": source_path.name,
                        "page_no": page_no,
                        "segment_no": segment_index + 1,
                        "image_path": str(output_path.resolve()),
                        "scale": f"{scale:.8f}",
                        "x_offset": segment_left,
                        "y_offset": top,
                    }
                )

    manifest_path = Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=manifest_rows[0].keys())
        writer.writeheader()
        writer.writerows(manifest_rows)

    print(
        f"prepared_pages={len(pages)} "
        f"ocr_segments={len(manifest_rows)} "
        f"manifest={manifest_path.resolve()}"
    )


if __name__ == "__main__":
    main()
