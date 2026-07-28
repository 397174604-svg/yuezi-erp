import argparse
import csv
import json
import re
from datetime import date
from pathlib import Path


PHONE_RE = re.compile(r"1[3-9]\d{9}")
ID_RE = re.compile(r"\d{17}[0-9X]")

COMMON_FIELDS = [
    "employee_no",
    "staging_no",
    "store_code",
    "source_seq",
    "source_row_order",
    "department",
    "position",
    "name",
    "gender",
    "age_at_source",
    "education",
    "mobile",
    "id_no",
    "id_no_raw",
    "id_no_valid",
    "birth_date",
    "id_valid_until",
    "home_address",
    "emergency_contact_name",
    "emergency_contact_phone",
    "hire_date",
    "tenure_text",
    "promotion_history",
    "contract_years_text",
    "contract_start_date",
    "contract_end_date",
    "contract_expiry_reminder",
    "contract_sign_count",
    "salary_card_no",
    "employment_status",
    "source_status",
    "source_note",
    "source_file",
    "source_page",
    "review_status",
]


JS_BANDS = {
    "source_seq": (145, 240),
    "department": (240, 380),
    "position": (380, 530),
    "name": (530, 675),
    "gender": (675, 790),
    "age_at_source": (790, 930),
    "education": (930, 1070),
    "mobile": (1070, 1260),
    "id_no": (1260, 1600),
    "birth_date": (1600, 1810),
    "id_valid_until": (1810, 1995),
    "home_address": (1995, 2580),
    "emergency_contact_name": (2580, 2765),
    "emergency_contact_phone": (2765, 2995),
    "hire_date": (2995, 3165),
    "tenure_text": (3165, 3315),
    "promotion_history": (3315, 3610),
    "contract_years_text": (3610, 3815),
    "contract_start_date": (3815, 4005),
    "contract_end_date": (4005, 4215),
    "contract_sign_count": (4215, 4510),
    "salary_card_no": (4510, 5100),
    "source_note": (5100, 5800),
}

HHL_BANDS = {
    "source_seq": (130, 230),
    "department": (230, 370),
    "name": (370, 540),
    "gender": (540, 660),
    "mobile": (660, 850),
    "id_no": (850, 1150),
    "birth_date": (1150, 1320),
    "home_address": (1320, 1995),
    "emergency_contact_name": (1995, 2190),
    "emergency_contact_phone": (2190, 2415),
    "hire_date": (2415, 2555),
    "contract_years_text": (2555, 2685),
    "contract_end_date": (2685, 2870),
    "contract_expiry_reminder": (2870, 3005),
    "tenure_text": (3005, 3135),
    "source_status": (3135, 3255),
    "source_note": (3255, 3500),
}


def compact(value):
    return re.sub(r"\s+", "", value or "").strip()


def normalize_numeric_text(value):
    return (
        compact(value)
        .replace("O", "0")
        .replace("o", "0")
        .replace("I", "1")
        .replace("l", "1")
        .replace("ｘ", "X")
        .replace("x", "X")
    )


def parse_date(value):
    value = (
        value.replace("年", "-")
        .replace("月", "-")
        .replace("日", "")
        .replace("—", "-")
        .replace("–", "-")
        .replace("一", "-")
        .replace("/", "-")
        .replace(".", "-")
    )
    parts = re.findall(r"\d+", value)
    if len(parts) < 3:
        return ""
    year, month, day = map(int, parts[:3])
    if year < 1900 or year > 2100:
        return ""
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return ""


def normalize_id(value):
    compacted = re.sub(r"[^0-9X]", "", normalize_numeric_text(value).upper())
    match = ID_RE.search(compacted)
    return match.group(0) if match else ""


def id_checksum_valid(id_no):
    if not ID_RE.fullmatch(id_no):
        return False
    weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    mapping = "10X98765432"
    expected = mapping[sum(int(n) * w for n, w in zip(id_no[:17], weights)) % 11]
    return id_no[-1] == expected


def find_phone(value):
    digits = re.sub(r"\D", "", normalize_numeric_text(value))
    match = PHONE_RE.search(digits)
    return match.group(0) if match else ""


def parse_int(value):
    match = re.search(r"\d+", normalize_numeric_text(value))
    return match.group(0) if match else ""


def load_words(path):
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    return [word for line in payload["lines"] for word in line["words"]]


def word_center_y(word):
    return word["y"] + word["height"] / 2


def serial_anchors(words, serial_band, expected_sequences=None):
    start, end = serial_band
    candidates = []
    for word in words:
        if not start <= word["x"] < end:
            continue
        text = re.sub(r"\D", "", normalize_numeric_text(word["text"]))
        if not text or len(text) > 3:
            continue
        number = int(text)
        if number < 1 or number > 999:
            continue
        candidates.append((word_center_y(word), number))

    anchors = []
    for center_y, number in sorted(candidates):
        if anchors and abs(anchors[-1][0] - center_y) <= 8:
            continue
        anchors.append((center_y, number))

    if expected_sequences:
        by_sequence = {
            sequence: center_y
            for center_y, sequence in anchors
            if sequence in expected_sequences
        }
        for sequence in expected_sequences:
            if sequence in by_sequence:
                continue
            previous = [
                (known, center_y)
                for known, center_y in by_sequence.items()
                if known < sequence
            ]
            following = [
                (known, center_y)
                for known, center_y in by_sequence.items()
                if known > sequence
            ]
            if previous and following:
                previous_sequence, previous_y = max(previous)
                following_sequence, following_y = min(following)
                ratio = (sequence - previous_sequence) / (
                    following_sequence - previous_sequence
                )
                by_sequence[sequence] = previous_y + ratio * (
                    following_y - previous_y
                )
        anchors = sorted(
            (center_y, sequence) for sequence, center_y in by_sequence.items()
        )
    return anchors


def group_words_by_rows(words, serial_band, expected_sequences=None):
    anchors = serial_anchors(words, serial_band, expected_sequences)
    if not anchors:
        return []
    rows = []
    for index, (center_y, source_seq) in enumerate(anchors):
        lower = (
            (anchors[index - 1][0] + center_y) / 2
            if index
            else center_y - 45
        )
        upper = (
            (center_y + anchors[index + 1][0]) / 2
            if index + 1 < len(anchors)
            else center_y + 45
        )
        row_words = [
            word for word in words if lower <= word_center_y(word) < upper
        ]
        rows.append(
            {
                "source_seq": source_seq,
                "center_y": center_y,
                "words": row_words,
            }
        )
    return rows


def field_text(row_words, band):
    start, end = band
    words = [
        word
        for word in row_words
        if start <= word["x"] + word["width"] / 2 < end
    ]
    if not words:
        return ""

    lines = []
    for word in sorted(words, key=lambda item: (word_center_y(item), item["x"])):
        center_y = word_center_y(word)
        if not lines or abs(lines[-1]["center_y"] - center_y) > 8:
            lines.append({"center_y": center_y, "words": [word]})
        else:
            lines[-1]["words"].append(word)
    values = []
    for line in lines:
        value = "".join(
            word["text"] for word in sorted(line["words"], key=lambda item: item["x"])
        )
        if compact(value):
            values.append(compact(value))
    return " / ".join(values)


def extract_row(row, bands):
    return {
        name: field_text(row["words"], band)
        for name, band in bands.items()
        if name != "source_seq"
    }


def normalize_common_record(record):
    record["source_seq"] = int(record["source_seq"])
    record["source_row_order"] = int(record["source_row_order"])
    record["age_at_source"] = parse_int(record.get("age_at_source", ""))
    record["mobile"] = find_phone(record.get("mobile", ""))
    record["id_no_raw"] = compact(
        record.get("id_no_raw", "") or record.get("id_no", "")
    )
    record["id_no"] = normalize_id(record["id_no_raw"])
    record["id_no_valid"] = "1" if id_checksum_valid(record["id_no"]) else "0"

    if record["id_no"]:
        record["birth_date"] = (
            f"{record['id_no'][6:10]}-"
            f"{record['id_no'][10:12]}-"
            f"{record['id_no'][12:14]}"
        )
    else:
        record["birth_date"] = parse_date(record.get("birth_date", ""))
    for field in (
        "id_valid_until",
        "hire_date",
        "contract_start_date",
        "contract_end_date",
    ):
        record[field] = parse_date(record.get(field, ""))

    record["contract_sign_count"] = parse_int(
        record.get("contract_sign_count", "")
    )
    record["salary_card_no"] = re.sub(
        r"\D", "", normalize_numeric_text(record.get("salary_card_no", ""))
    )
    for field in COMMON_FIELDS:
        record.setdefault(field, "")
    return {field: record[field] for field in COMMON_FIELDS}


def build_js_records(ocr_dir, manual_path):
    manual = {}
    with manual_path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            manual[int(row["source_seq"])] = row

    extracted_by_seq = {}
    for page_no in (1, 2):
        path = ocr_dir / f"JS-p{page_no:02d}-s01.json"
        words = load_words(path)
        expected_sequences = (
            list(range(1, 26)) if page_no == 1 else list(range(26, 47))
        )
        for row_order, row in enumerate(
            group_words_by_rows(
                words, JS_BANDS["source_seq"], expected_sequences
            ),
            1,
        ):
            seq = row["source_seq"]
            if seq not in manual:
                continue
            extracted_by_seq[seq] = {
                **extract_row(row, JS_BANDS),
                "source_page": page_no,
                "source_row_order": row_order,
            }

    records = []
    for seq in sorted(manual):
        core = manual[seq]
        extracted = extracted_by_seq.get(seq, {})
        mobile = core["mobile_override"] or extracted.get("mobile", "")
        raw_id = extracted.get("id_no", "")
        review_status = (
            "CORE_VERIFIED"
            if find_phone(mobile) and id_checksum_valid(raw_id)
            else "NEEDS_ID_REVIEW"
        )
        records.append(
            normalize_common_record(
                {
                    "employee_no": f"JS{seq:04d}",
                    "staging_no": "",
                    "store_code": "JS",
                    "source_seq": seq,
                    "source_row_order": extracted.get("source_row_order", seq),
                    "department": core["department"],
                    "position": core["position"],
                    "name": core["name"],
                    "gender": core["gender"],
                    "age_at_source": core["age"],
                    "education": core["education"],
                    "mobile": mobile,
                    "id_no": raw_id,
                    "id_no_raw": raw_id,
                    "birth_date": extracted.get("birth_date", ""),
                    "id_valid_until": extracted.get("id_valid_until", ""),
                    "home_address": extracted.get("home_address", ""),
                    "emergency_contact_name": extracted.get(
                        "emergency_contact_name", ""
                    ),
                    "emergency_contact_phone": extracted.get(
                        "emergency_contact_phone", ""
                    ),
                    "hire_date": extracted.get("hire_date", ""),
                    "tenure_text": extracted.get("tenure_text", ""),
                    "promotion_history": extracted.get("promotion_history", ""),
                    "contract_years_text": extracted.get(
                        "contract_years_text", ""
                    ),
                    "contract_start_date": extracted.get(
                        "contract_start_date", ""
                    ),
                    "contract_end_date": extracted.get("contract_end_date", ""),
                    "contract_expiry_reminder": "",
                    "contract_sign_count": extracted.get(
                        "contract_sign_count", ""
                    ),
                    "salary_card_no": extracted.get("salary_card_no", ""),
                    "employment_status": "ACTIVE",
                    "source_status": "在职",
                    "source_note": extracted.get("source_note", ""),
                    "source_file": "建设路店花名册.pdf",
                    "source_page": extracted.get(
                        "source_page", 1 if seq <= 25 else 2
                    ),
                    "review_status": review_status,
                }
            )
        )
    return records


def build_hhl_records(ocr_dir):
    active = []
    offboarded = []
    active_counter = 0
    staging_counter = 0

    for page_no in range(1, 5):
        path = ocr_dir / f"HHL-p{page_no:02d}-s01.json"
        words = load_words(path)
        rows = group_words_by_rows(words, HHL_BANDS["source_seq"])
        for row_order, row in enumerate(rows, 1):
            extracted = extract_row(row, HHL_BANDS)
            department = compact(extracted.get("department", ""))
            name = compact(extracted.get("name", ""))
            if not department or not name:
                continue

            status_text = compact(extracted.get("source_status", ""))
            if "离职" in status_text:
                employment_status = "OFFBOARDED"
            elif "在职" in status_text:
                employment_status = "ACTIVE"
            elif page_no <= 2:
                employment_status = "ACTIVE"
            else:
                employment_status = "OFFBOARDED"

            raw_id = extracted.get("id_no", "")
            mobile = find_phone(extracted.get("mobile", ""))
            review_status = (
                "CORE_VERIFIED"
                if employment_status == "ACTIVE"
                and mobile
                and id_checksum_valid(raw_id)
                else (
                    "NEEDS_ID_REVIEW"
                    if employment_status == "ACTIVE"
                    else "NEEDS_IDENTITY_REVIEW"
                )
            )
            if employment_status == "ACTIVE":
                active_counter += 1
                employee_no = f"HHL{active_counter:04d}"
                staging_no = ""
            else:
                staging_counter += 1
                employee_no = ""
                staging_no = f"HHL-OFF-{staging_counter:04d}"

            record = normalize_common_record(
                {
                    "employee_no": employee_no,
                    "staging_no": staging_no,
                    "store_code": "HHL",
                    "source_seq": row["source_seq"],
                    "source_row_order": row_order,
                    "department": department,
                    "position": "",
                    "name": name,
                    "gender": compact(extracted.get("gender", "")),
                    "age_at_source": "",
                    "education": "",
                    "mobile": mobile,
                    "id_no": raw_id,
                    "id_no_raw": raw_id,
                    "birth_date": extracted.get("birth_date", ""),
                    "id_valid_until": "",
                    "home_address": extracted.get("home_address", ""),
                    "emergency_contact_name": extracted.get(
                        "emergency_contact_name", ""
                    ),
                    "emergency_contact_phone": extracted.get(
                        "emergency_contact_phone", ""
                    ),
                    "hire_date": extracted.get("hire_date", ""),
                    "tenure_text": extracted.get("tenure_text", ""),
                    "promotion_history": "",
                    "contract_years_text": extracted.get(
                        "contract_years_text", ""
                    ),
                    "contract_start_date": "",
                    "contract_end_date": extracted.get("contract_end_date", ""),
                    "contract_expiry_reminder": extracted.get(
                        "contract_expiry_reminder", ""
                    ),
                    "contract_sign_count": "",
                    "salary_card_no": "",
                    "employment_status": employment_status,
                    "source_status": status_text,
                    "source_note": extracted.get("source_note", ""),
                    "source_file": "黄河路花名册.pdf",
                    "source_page": page_no,
                    "review_status": review_status,
                }
            )
            if employment_status == "ACTIVE":
                active.append(record)
            else:
                offboarded.append(record)
    return active, offboarded


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=COMMON_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ocr-dir", required=True)
    parser.add_argument("--js-core", required=True)
    parser.add_argument("--active-output", required=True)
    parser.add_argument("--offboarded-output", required=True)
    args = parser.parse_args()

    ocr_dir = Path(args.ocr_dir)
    js_records = build_js_records(ocr_dir, Path(args.js_core))
    hhl_active, hhl_offboarded = build_hhl_records(ocr_dir)
    active = js_records + hhl_active

    employee_nos = [row["employee_no"] for row in active]
    mobiles = [row["mobile"] for row in active if row["mobile"]]
    if len(employee_nos) != len(set(employee_nos)):
        raise ValueError("Duplicate employee number detected")
    if len(mobiles) != len(set(mobiles)):
        raise ValueError("Duplicate active employee mobile detected")
    if len(active) != 94:
        raise ValueError(f"Expected 94 active employees, got {len(active)}")

    write_csv(Path(args.active_output), active)
    write_csv(Path(args.offboarded_output), hhl_offboarded)

    print(
        f"active={len(active)} "
        f"js_active={len(js_records)} "
        f"hhl_active={len(hhl_active)} "
        f"offboarded_staging={len(hhl_offboarded)} "
        f"active_missing_mobile={sum(not row['mobile'] for row in active)} "
        f"active_id_captured={sum(bool(row['id_no']) for row in active)} "
        f"active_id_raw_captured={sum(bool(row['id_no_raw']) for row in active)} "
        f"active_valid_id={sum(row['id_no_valid'] == '1' for row in active)} "
        f"active_address_captured={sum(bool(row['home_address']) for row in active)} "
        f"active_emergency_phone_captured="
        f"{sum(bool(row['emergency_contact_phone']) for row in active)}"
    )


if __name__ == "__main__":
    main()
