from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "2026-07-23-月子系统ERP项目日报-A4横向.pdf"
ROOM_IMAGE = ROOT / "docs" / "日报附件" / "2026-07-23-房态图.png"
SYSTEM_IMAGE = ROOT / "docs" / "日报附件" / "2026-07-23-系统设置工作台.png"

FONT_REGULAR = Path("C:/Windows/Fonts/Deng.ttf")
FONT_BOLD = Path("C:/Windows/Fonts/Dengb.ttf")

PAGE_W, PAGE_H = landscape(A4)


def color(hex_value):
    return colors.HexColor(hex_value)


BG = color("#F4F7FB")
CARD = colors.white
TEXT = color("#1F2937")
MUTED = color("#667085")
PINK = color("#F35B8D")
PINK_LIGHT = color("#FFF0F5")
TEAL = color("#24A89A")
TEAL_LIGHT = color("#EAF9F6")
BLUE = color("#4E7FF1")
BLUE_LIGHT = color("#EEF3FF")
PURPLE = color("#7A5AF8")
PURPLE_LIGHT = color("#F3F0FF")
AMBER = color("#F5A524")
AMBER_LIGHT = color("#FFF7E6")
BORDER = color("#E5EAF1")


def register_fonts():
    pdfmetrics.registerFont(TTFont("DailyCN", str(FONT_REGULAR)))
    pdfmetrics.registerFont(TTFont("DailyCN-Bold", str(FONT_BOLD)))


def draw_card(c, x, y, w, h, fill=CARD, stroke=BORDER, radius=8):
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(0.6)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1)


def draw_text(c, text, x, y, size=8, font="DailyCN", fill=TEXT):
    c.setFont(font, size)
    c.setFillColor(fill)
    c.drawString(x, y, text)


def draw_right(c, text, x, y, size=8, font="DailyCN", fill=TEXT):
    c.setFont(font, size)
    c.setFillColor(fill)
    c.drawRightString(x, y, text)


def fit_text_lines(text, font, size, max_width):
    lines = []
    current = ""
    for char in text:
        if char == "\n":
            lines.append(current)
            current = ""
            continue
        candidate = current + char
        if current and pdfmetrics.stringWidth(candidate, font, size) > max_width:
            lines.append(current)
            current = char
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def draw_wrapped(c, text, x, y, max_width, size=8, leading=11, font="DailyCN", fill=TEXT, max_lines=None):
    lines = fit_text_lines(text, font, size, max_width)
    if max_lines:
        lines = lines[:max_lines]
    for index, line in enumerate(lines):
        draw_text(c, line, x, y - index * leading, size=size, font=font, fill=fill)
    return y - len(lines) * leading


def draw_bullets(c, items, x, y, max_width, size=7.4, leading=10.2, bullet_color=PINK):
    current_y = y
    for item in items:
        c.setFillColor(bullet_color)
        c.circle(x + 2.5, current_y + 2.2, 1.6, fill=1, stroke=0)
        lines = fit_text_lines(item, "DailyCN", size, max_width - 12)
        for line_index, line in enumerate(lines):
            draw_text(
                c,
                line,
                x + 10,
                current_y - line_index * leading,
                size=size,
                fill=TEXT,
            )
        current_y -= max(1, len(lines)) * leading + 1.6
    return current_y


def draw_image_contain(c, image_path, x, y, w, h):
    image = ImageReader(str(image_path))
    image_w, image_h = image.getSize()
    scale = min(w / image_w, h / image_h)
    draw_w = image_w * scale
    draw_h = image_h * scale
    draw_x = x + (w - draw_w) / 2
    draw_y = y + (h - draw_h) / 2
    c.drawImage(image, draw_x, draw_y, draw_w, draw_h, preserveAspectRatio=True, mask="auto")


def draw_metric(c, x, y, w, h, value, label, accent, light):
    c.setFillColor(light)
    c.setStrokeColor(light)
    c.roundRect(x, y, w, h, 6, fill=1, stroke=0)
    draw_text(c, value, x + 10, y + h - 17, size=14, font="DailyCN-Bold", fill=accent)
    draw_text(c, label, x + 10, y + 8, size=6.8, fill=MUTED)


def draw_module_table(c, x, y, w, h):
    draw_card(c, x, y, w, h)
    draw_text(c, "10 个并行模块 / 167 个子菜单", x + 14, y + h - 22, 10, "DailyCN-Bold")
    draw_text(c, "菜单标题、顺序、URL 与 navid 已只读核验", x + 14, y + h - 36, 6.8, fill=MUTED)

    modules = [
        ("护理管理", "17", "商城管理", "13"),
        ("产康管理", "10", "风控服务", "1"),
        ("月嫂管理", "8", "查询报表", "42"),
        ("膳食管理", "13", "基础资料", "19"),
        ("仓存管理", "24", "系统设置", "20"),
    ]
    table_x = x + 14
    table_y = y + h - 56
    row_h = 22
    col_widths = [78, 34, 78, 34]
    total_w = sum(col_widths)

    c.setFillColor(PURPLE_LIGHT)
    c.roundRect(table_x, table_y - row_h + 4, total_w, row_h, 4, fill=1, stroke=0)
    headers = ["模块 A", "数量", "模块 B", "数量"]
    cursor = table_x
    for header, col_w in zip(headers, col_widths):
        draw_text(c, header, cursor + 7, table_y - 11, 7, "DailyCN-Bold", fill=PURPLE)
        cursor += col_w

    for row_index, row in enumerate(modules):
        row_top = table_y - (row_index + 1) * row_h - 3
        if row_index % 2 == 1:
            c.setFillColor(color("#FAFBFD"))
            c.rect(table_x, row_top - row_h + 8, total_w, row_h, fill=1, stroke=0)
        cursor = table_x
        for cell_index, (cell, col_w) in enumerate(zip(row, col_widths)):
            fill = TEXT if cell_index % 2 == 0 else PINK
            font = "DailyCN" if cell_index % 2 == 0 else "DailyCN-Bold"
            draw_text(c, cell, cursor + 7, row_top - 7, 7.3, font, fill)
            cursor += col_w

    draw_text(c, "报表纠偏：实际 42 项，不虚构第 43 项。", x + 14, y + 12, 7, "DailyCN-Bold", AMBER)


def build_pdf():
    register_fonts()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(OUTPUT), pagesize=(PAGE_W, PAGE_H))
    c.setTitle("2026-07-23 月子系统 ERP 项目日报 - A4 横向")
    c.setAuthor("Codex")
    c.setSubject("月子系统 ERP 字段级复刻项目日报")

    c.setFillColor(BG)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    margin = 18
    content_w = PAGE_W - margin * 2

    # Header
    c.setFillColor(PINK)
    c.roundRect(margin, PAGE_H - 66, content_w, 48, 10, fill=1, stroke=0)
    draw_text(c, "2026-07-23 月子系统 ERP 项目日报", margin + 18, PAGE_H - 45, 19, "DailyCN-Bold", colors.white)
    draw_right(c, "A4 横向 · 一页总览", PAGE_W - margin - 18, PAGE_H - 42, 9, "DailyCN-Bold", colors.white)
    draw_text(c, "房态图深度复刻 + 10 个业务模块并行落地 + 统一工程接入与回归", margin + 19, PAGE_H - 58, 7.6, fill=colors.white)

    # Main visual: one screenshot and four metrics
    image_y = 288
    image_h = 226
    image_w = 430
    draw_card(c, margin, image_y, image_w, image_h)
    draw_image_contain(c, ROOM_IMAGE, margin + 8, image_y + 29, image_w - 16, image_h - 39)
    draw_text(c, "房态图：住户剩余天数、入住区间与详情入口", margin + 12, image_y + 11, 7.4, "DailyCN-Bold", TEXT)

    metric_x = margin + image_w + 10
    metric_w = content_w - image_w - 10
    draw_card(c, metric_x, image_y, metric_w, image_h)
    draw_text(c, "今日关键结果", metric_x + 16, image_y + image_h - 28, 12, "DailyCN-Bold")
    metrics = [
        ("10", "并行模块", PINK, PINK_LIGHT),
        ("167", "子菜单承接", PURPLE, PURPLE_LIGHT),
        ("10/10", "首菜单路由", BLUE, BLUE_LIGHT),
        ("PASS", "ESLint / Build", TEAL, TEAL_LIGHT),
    ]
    box_gap = 9
    box_w = (metric_w - 32 - box_gap) / 2
    box_h = 57
    start_y = image_y + image_h - 100
    for index, (value, label, accent, light) in enumerate(metrics):
        col = index % 2
        row = index // 2
        draw_metric(
            c,
            metric_x + 16 + col * (box_w + box_gap),
            start_y - row * (box_h + 9),
            box_w,
            box_h,
            value,
            label,
            accent,
            light,
        )
    c.setFillColor(AMBER_LIGHT)
    c.roundRect(metric_x + 16, image_y + 16, metric_w - 32, 31, 6, fill=1, stroke=0)
    draw_text(c, "查询报表实际 42 项；浏览器控制台错误 0。", metric_x + 28, image_y + 27, 8, "DailyCN-Bold", AMBER)

    # Bottom summary cards
    bottom_y = 53
    bottom_h = 218
    gap = 10
    card_w = (content_w - gap * 2) / 3

    done_x = margin
    draw_card(c, done_x, bottom_y, card_w, bottom_h)
    draw_text(c, "今天完成", done_x + 16, bottom_y + bottom_h - 27, 11, "DailyCN-Bold")
    draw_bullets(
        c,
        [
            "201 房住户可打开客户明细",
            "客户详情承接原系统 17 个页签",
            "订房详情及三组房间记录完成",
            "10 个业务模块完成独立工作台接入",
            "菜单标题、顺序、URL 与 navid 已核验",
        ],
        done_x + 16,
        bottom_y + bottom_h - 51,
        card_w - 32,
        size=8,
        leading=11.4,
        bullet_color=TEAL,
    )
    c.setFillColor(TEAL_LIGHT)
    c.roundRect(done_x + 16, bottom_y + 16, card_w - 32, 33, 6, fill=1, stroke=0)
    draw_text(c, "房态交互与表头回归通过", done_x + 28, bottom_y + 28, 8.2, "DailyCN-Bold", TEAL)

    module_x = done_x + card_w + gap
    draw_card(c, module_x, bottom_y, card_w, bottom_h)
    draw_text(c, "模块覆盖", module_x + 16, bottom_y + bottom_h - 27, 11, "DailyCN-Bold")
    module_lines = [
        "护理 17 · 产康 10 · 月嫂 8",
        "膳食 13 · 仓存 24 · 商城 13",
        "风控 1 · 报表 42",
        "基础资料 19 · 系统设置 20",
    ]
    for index, line in enumerate(module_lines):
        fill = [PINK, PURPLE, BLUE, TEAL][index]
        light = [PINK_LIGHT, PURPLE_LIGHT, BLUE_LIGHT, TEAL_LIGHT][index]
        row_y = bottom_y + bottom_h - 64 - index * 33
        c.setFillColor(light)
        c.roundRect(module_x + 16, row_y, card_w - 32, 25, 5, fill=1, stroke=0)
        draw_text(c, line, module_x + 28, row_y + 8, 8.3, "DailyCN-Bold", fill)
    draw_text(c, "合计 167 个现有子菜单", module_x + 16, bottom_y + 18, 8.2, "DailyCN-Bold", TEXT)

    next_x = module_x + card_w + gap
    draw_card(c, next_x, bottom_y, card_w, bottom_h)
    draw_text(c, "边界与下一步", next_x + 16, bottom_y + bottom_h - 27, 11, "DailyCN-Bold")
    draw_wrapped(
        c,
        "除房态详情外，10 个模块当前主要为 Visible / Mock；页面内部字段、下拉、按钮、弹窗和状态机仍需逐页核验。",
        next_x + 16,
        bottom_y + bottom_h - 52,
        card_w - 32,
        size=7.7,
        leading=10.8,
        max_lines=4,
    )
    c.setStrokeColor(BORDER)
    c.line(next_x + 16, bottom_y + 111, next_x + card_w - 16, bottom_y + 111)
    draw_text(c, "下一步", next_x + 16, bottom_y + 93, 8.2, "DailyCN-Bold", PINK)
    draw_bullets(
        c,
        [
            "护理、产康逐页字段取证",
            "膳食执行与库存扣减联动",
            "审批、金额、权限与历史数据对账",
        ],
        next_x + 16,
        bottom_y + 75,
        card_w - 32,
        size=7.5,
        leading=10.4,
        bullet_color=PINK,
    )

    # Footer
    draw_text(c, "项目：C:\\Users\\39717\\Desktop\\月子系统erp", margin, 25, 6.4, fill=MUTED)
    draw_right(c, "详细日报与横向 Canvas 已同步至 Obsidian", PAGE_W - margin, 25, 6.4, fill=MUTED)

    c.showPage()
    c.save()
    print(OUTPUT)


if __name__ == "__main__":
    build_pdf()
