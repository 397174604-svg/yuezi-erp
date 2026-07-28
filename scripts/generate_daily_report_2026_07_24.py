from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "2026-07-24-月子系统ERP项目日报-A4横向.pdf"
SCREENSHOT = ROOT / "docs" / "日报附件" / "2026-07-24-月嫂档案.png"
FONT_REGULAR = Path("C:/Windows/Fonts/Deng.ttf")
FONT_BOLD = Path("C:/Windows/Fonts/Dengb.ttf")
PAGE_W, PAGE_H = landscape(A4)


def hex_color(value):
    return colors.HexColor(value)


BG = hex_color("#F5F7FB")
CARD = colors.white
INK = hex_color("#24324A")
MUTED = hex_color("#667085")
LINE = hex_color("#E5EAF1")
PINK = hex_color("#F45D91")
PINK_LIGHT = hex_color("#FFF0F5")
PURPLE = hex_color("#8257D9")
PURPLE_LIGHT = hex_color("#F4F0FF")
BLUE = hex_color("#4E7FF1")
BLUE_LIGHT = hex_color("#EEF3FF")
TEAL = hex_color("#20A28F")
TEAL_LIGHT = hex_color("#EAF9F6")
AMBER = hex_color("#D98B18")
AMBER_LIGHT = hex_color("#FFF7E7")


def register_fonts():
    pdfmetrics.registerFont(TTFont("DailyCN", str(FONT_REGULAR)))
    pdfmetrics.registerFont(TTFont("DailyCN-Bold", str(FONT_BOLD)))


def text(c, value, x, y, size=8, font="DailyCN", fill=INK):
    c.setFont(font, size)
    c.setFillColor(fill)
    c.drawString(x, y, value)


def right_text(c, value, x, y, size=8, font="DailyCN", fill=INK):
    c.setFont(font, size)
    c.setFillColor(fill)
    c.drawRightString(x, y, value)


def card(c, x, y, w, h, fill=CARD, stroke=LINE, radius=9):
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(0.7)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1)


def fit_lines(value, font, size, width):
    lines = []
    current = ""
    for char in value:
        candidate = current + char
        if current and pdfmetrics.stringWidth(candidate, font, size) > width:
            lines.append(current)
            current = char
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def wrapped(c, value, x, y, width, size=7.4, leading=10, font="DailyCN", fill=INK, max_lines=None):
    lines = fit_lines(value, font, size, width)
    if max_lines is not None:
        lines = lines[:max_lines]
    for index, line in enumerate(lines):
        text(c, line, x, y - index * leading, size=size, font=font, fill=fill)
    return y - len(lines) * leading


def bullets(c, items, x, y, width, accent=PINK, size=7.2, leading=9.4):
    cursor_y = y
    for item in items:
        c.setFillColor(accent)
        c.circle(x + 2.2, cursor_y + 2.2, 1.5, fill=1, stroke=0)
        lines = fit_lines(item, "DailyCN", size, width - 12)
        for index, line in enumerate(lines):
            text(c, line, x + 10, cursor_y - index * leading, size=size)
        cursor_y -= max(1, len(lines)) * leading + 2
    return cursor_y


def metric(c, x, y, w, value, label, accent, light):
    c.setFillColor(light)
    c.roundRect(x, y, w, 45, 7, fill=1, stroke=0)
    text(c, value, x + 11, y + 23, size=14, font="DailyCN-Bold", fill=accent)
    text(c, label, x + 11, y + 9, size=6.6, fill=MUTED)


def image_contain(c, path, x, y, w, h):
    image = ImageReader(str(path))
    image_w, image_h = image.getSize()
    scale = min(w / image_w, h / image_h)
    draw_w = image_w * scale
    draw_h = image_h * scale
    draw_x = x + (w - draw_w) / 2
    draw_y = y + (h - draw_h) / 2
    c.drawImage(image, draw_x, draw_y, draw_w, draw_h, preserveAspectRatio=True, mask="auto")


def build_pdf():
    register_fonts()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(OUTPUT), pagesize=(PAGE_W, PAGE_H))
    c.setTitle("2026-07-24 月子系统 ERP 项目日报 - A4 横向")
    c.setAuthor("巩佳楠")
    c.setSubject("月子系统 ERP 字段级复刻项目日报")

    c.setFillColor(BG)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    margin = 18
    content_w = PAGE_W - margin * 2

    # 标题区
    c.setFillColor(PINK)
    c.roundRect(margin, PAGE_H - 66, content_w, 48, 11, fill=1, stroke=0)
    text(c, "2026-07-24 月子系统 ERP 项目日报", margin + 18, PAGE_H - 44, 19, "DailyCN-Bold", colors.white)
    text(c, "产康服务综合查询双模式 + 月嫂管理 8 页深层字段级复刻", margin + 19, PAGE_H - 57, 7.5, fill=colors.white)
    right_text(c, "日报人：巩佳楠", PAGE_W - margin - 18, PAGE_H - 42, 10, "DailyCN-Bold", colors.white)
    right_text(c, "A4 横向 · 单页总览", PAGE_W - margin - 18, PAGE_H - 56, 7, fill=colors.white)

    # KPI
    metric_y = PAGE_H - 122
    gap = 8
    metric_w = (content_w - gap * 4) / 5
    metrics = [
        ("2", "深度复刻模块", PINK, PINK_LIGHT),
        ("8/8", "月嫂子页面", PURPLE, PURPLE_LIGHT),
        ("17", "产康列表列数", BLUE, BLUE_LIGHT),
        ("39", "月嫂档案字段", TEAL, TEAL_LIGHT),
        ("0", "浏览器错误", AMBER, AMBER_LIGHT),
    ]
    for index, item in enumerate(metrics):
        metric(c, margin + index * (metric_w + gap), metric_y, metric_w, *item)

    # 主体三列
    body_y = 52
    body_h = metric_y - body_y - 12
    left_w = 220
    middle_w = 326
    right_w = content_w - left_w - middle_w - gap * 2

    # 左：截图
    left_x = margin
    card(c, left_x, body_y, left_w, body_h)
    text(c, "月嫂档案页面成果", left_x + 14, body_y + body_h - 25, 10.5, "DailyCN-Bold")
    text(c, "工具栏 / 查询区 / 主表同屏", left_x + 14, body_y + body_h - 39, 6.8, fill=MUTED)
    image_contain(c, SCREENSHOT, left_x + 13, body_y + 36, left_w - 26, body_h - 86)
    c.setFillColor(TEAL_LIGHT)
    c.roundRect(left_x + 13, body_y + 13, left_w - 26, 20, 5, fill=1, stroke=0)
    text(c, "页面仅展示业务内容，审计证据已移出", left_x + 24, body_y + 20, 7, "DailyCN-Bold", TEAL)

    # 中：今日完成
    middle_x = left_x + left_w + gap
    card(c, middle_x, body_y, middle_w, body_h)
    text(c, "今日关键成果", middle_x + 15, body_y + body_h - 25, 10.5, "DailyCN-Bold")

    c.setFillColor(PINK_LIGHT)
    c.roundRect(middle_x + 14, body_y + body_h - 139, middle_w - 28, 95, 7, fill=1, stroke=0)
    text(c, "01  产康管理 · 服务综合查询", middle_x + 26, body_y + body_h - 62, 8.7, "DailyCN-Bold", PINK)
    bullets(
        c,
        [
            "图形模式补齐读卡、选客户、项目打印及 4 个服务页签",
            "列表模式补齐右上角切换、9 项查询条件和完整下拉选项",
            "结果表补齐 17 列；选择、读卡、页签与模式切换均已验证",
        ],
        middle_x + 24,
        body_y + body_h - 82,
        middle_w - 46,
        accent=PINK,
        size=7.1,
        leading=9.3,
    )

    c.setFillColor(PURPLE_LIGHT)
    c.roundRect(middle_x + 14, body_y + 62, middle_w - 28, body_h - 210, 7, fill=1, stroke=0)
    text(c, "02  月嫂管理 · 8 页深层复刻", middle_x + 26, body_y + body_h - 166, 8.7, "DailyCN-Bold", PURPLE)
    bullets(
        c,
        [
            "月嫂档案 39 项字段；薪资标准 9 项字段；档期矩阵 5 项请假字段",
            "月嫂合同 14 个动作、33 列、22 项字段及 4 个明细页签",
            "服务记录 10 个动作、28 列、11 项派工字段、30 项结算字段",
            "派工审核 26 列、结算列表 42 列、预约记录 13 列",
            "移除 URL、navid、Schema 和待核验清单等开发审计文字",
        ],
        middle_x + 24,
        body_y + body_h - 186,
        middle_w - 46,
        accent=PURPLE,
        size=7.1,
        leading=9.3,
    )
    c.setFillColor(BLUE_LIGHT)
    c.roundRect(middle_x + 14, body_y + 13, middle_w - 28, 38, 7, fill=1, stroke=0)
    text(c, "当前阶段", middle_x + 26, body_y + 35, 7.2, "DailyCN-Bold", BLUE)
    text(c, "Schema-faithful + 脱敏 Mock 交互", middle_x + 26, body_y + 21, 8.2, "DailyCN-Bold", INK)

    # 右：质量、沉淀、下一步
    right_x = middle_x + middle_w + gap
    card(c, right_x, body_y, right_w, body_h)
    text(c, "质量验证", right_x + 14, body_y + body_h - 25, 10.5, "DailyCN-Bold")
    bullets(
        c,
        [
            "定向 ESLint：通过",
            "生产构建：通过",
            "月嫂路由：8/8 通过",
            "控制台错误：0",
            "未复制真实业务数据",
        ],
        right_x + 14,
        body_y + body_h - 48,
        right_w - 28,
        accent=TEAL,
        size=7.2,
        leading=9.3,
    )

    c.setStrokeColor(LINE)
    c.line(right_x + 14, body_y + body_h - 119, right_x + right_w - 14, body_y + body_h - 119)
    text(c, "Skill 方法沉淀", right_x + 14, body_y + body_h - 139, 9, "DailyCN-Bold", PINK)
    bullets(
        c,
        [
            "多模式页继续核验 iframe",
            "审计证据与业务界面隔离",
            "只读跟随，禁止触发写入动作",
        ],
        right_x + 14,
        body_y + body_h - 159,
        right_w - 28,
        accent=PINK,
        size=7,
        leading=9.1,
    )

    c.setStrokeColor(LINE)
    c.line(right_x + 14, body_y + 99, right_x + right_w - 14, body_y + 99)
    text(c, "下一步", right_x + 14, body_y + 80, 9, "DailyCN-Bold", PURPLE)
    bullets(
        c,
        [
            "补齐产康其余页面的表单与状态流转",
            "建立客户到入住主链路的真实接口契约",
            "完成审批、金额、权限和库存消耗对账",
        ],
        right_x + 14,
        body_y + 60,
        right_w - 28,
        accent=PURPLE,
        size=6.9,
        leading=8.9,
    )

    # 页脚
    text(c, "项目：C:\\Users\\39717\\Desktop\\月子系统erp", margin, 24, 6.3, fill=MUTED)
    right_text(c, "2026-07-24 · 巩佳楠", PAGE_W - margin, 24, 6.3, "DailyCN-Bold", MUTED)

    c.showPage()
    c.save()
    print(OUTPUT)


if __name__ == "__main__":
    build_pdf()
