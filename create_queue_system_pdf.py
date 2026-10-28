from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, Flowable
)


OUT = Path("output") / "pdf" / "葉神經科候診叫號系統第一階段導入規劃.pdf"
FONT_FILE = r"C:\Windows\Fonts\NotoSansTC-VF.ttf"
FONT = "NotoTC"
NAVY = HexColor("#123B54")
TEAL = HexColor("#237D83")
INK = HexColor("#1F2933")
MUTED = HexColor("#5F6B76")
PALE = HexColor("#EAF3F4")
PALE_BLUE = HexColor("#EDF4F8")
LINE = HexColor("#D6E0E5")
WHITE = colors.white


def P(text, style):
    return Paragraph(text, style)


class ProcessDiagram(Flowable):
    def __init__(self):
        super().__init__()
        self.width = 174 * mm
        self.height = 40 * mm

    def draw(self):
        c = self.canv
        y, w, h = 12 * mm, 32 * mm, 17 * mm
        x_values = [0, 46 * mm, 92 * mm, 138 * mm]
        labels = [
            ("櫃台完成掛號", "沿用既有系統"),
            ("螢幕確認號碼", "口頭告知與顯示"),
            ("醫師快捷叫號", "病歷送出後按鍵"),
            ("病人進入診間", "螢幕與語音同步"),
        ]
        for i, (title, subtitle) in enumerate(labels):
            x = x_values[i]
            c.setFillColor(PALE_BLUE if i % 2 == 0 else PALE)
            c.roundRect(x, y, w, h, 3 * mm, stroke=0, fill=1)
            c.setFillColor(NAVY)
            c.setFont(FONT, 10)
            c.drawCentredString(x + w / 2, y + 10.5 * mm, title)
            c.setFillColor(MUTED)
            c.setFont(FONT, 7.6)
            c.drawCentredString(x + w / 2, y + 5.7 * mm, subtitle)
            if i < len(labels) - 1:
                start = x + w + 2 * mm
                end = x_values[i + 1] - 2 * mm
                c.setStrokeColor(TEAL)
                c.setLineWidth(1.2)
                c.line(start, y + h / 2, end, y + h / 2)
                c.line(end, y + h / 2, end - 2.2 * mm, y + h / 2 + 1.4 * mm)
                c.line(end, y + h / 2, end - 2.2 * mm, y + h / 2 - 1.4 * mm)


class ERDDiagram(Flowable):
    def __init__(self):
        super().__init__()
        self.width = 174 * mm
        self.height = 67 * mm

    def node(self, c, x, y, title, fields, fill):
        width, height = 39 * mm, 21 * mm
        c.setStrokeColor(LINE)
        c.setFillColor(fill)
        c.roundRect(x, y, width, height, 2.5 * mm, stroke=1, fill=1)
        c.setFillColor(NAVY)
        c.setFont(FONT, 9)
        c.drawCentredString(x + width / 2, y + 14.4 * mm, title)
        c.setFillColor(MUTED)
        c.setFont(FONT, 6.8)
        for i, field in enumerate(fields):
            c.drawString(x + 3 * mm, y + (9 - i * 3.6) * mm, field)

    def line(self, c, x1, y1, x2, y2, label):
        c.setStrokeColor(TEAL)
        c.setLineWidth(1.05)
        c.line(x1, y1, x2, y2)
        c.setFillColor(TEAL)
        c.setFont(FONT, 7)
        c.drawCentredString((x1 + x2) / 2, (y1 + y2) / 2 + 2.6 * mm, label)

    def draw(self):
        c = self.canv
        self.node(c, 0, 38 * mm, "診次", ["session_id", "日期 / 時段", "狀態"], PALE_BLUE)
        self.node(c, 67.5 * mm, 38 * mm, "候診紀錄", ["queue_id", "候診序號", "候診狀態"], PALE)
        self.node(c, 135 * mm, 38 * mm, "叫號紀錄", ["event_id", "動作", "發生時間"], PALE_BLUE)
        self.node(c, 33.5 * mm, 3 * mm, "操作角色", ["operator_id", "醫師 / 櫃台", "啟用狀態"], PALE)
        self.node(c, 101 * mm, 3 * mm, "設備", ["device_id", "類型", "位置"], PALE)
        self.line(c, 39 * mm, 48.5 * mm, 67.5 * mm, 48.5 * mm, "1 對 多")
        self.line(c, 106.5 * mm, 48.5 * mm, 135 * mm, 48.5 * mm, "1 對 多")
        self.line(c, 53 * mm, 24 * mm, 78 * mm, 38 * mm, "建立")
        self.line(c, 120.5 * mm, 24 * mm, 144 * mm, 38 * mm, "來源")


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.5)
    canvas.line(18 * mm, 13 * mm, 192 * mm, 13 * mm)
    canvas.setFillColor(MUTED)
    canvas.setFont(FONT, 7.2)
    canvas.drawString(18 * mm, 8.5 * mm, "葉神經科 候診叫號系統 第一階段導入規劃")
    canvas.drawRightString(192 * mm, 8.5 * mm, f"第 {doc.page} 頁")
    canvas.restoreState()


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("title", parent=base["Title"], fontName=FONT, fontSize=28, leading=36, textColor=NAVY, alignment=TA_LEFT, spaceAfter=7 * mm),
        "subtitle": ParagraphStyle("subtitle", parent=base["Normal"], fontName=FONT, fontSize=13, leading=20, textColor=TEAL, alignment=TA_LEFT, spaceAfter=8 * mm),
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName=FONT, fontSize=18, leading=25, textColor=NAVY, spaceBefore=0, spaceAfter=5 * mm, keepWithNext=True),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName=FONT, fontSize=12, leading=18, textColor=TEAL, spaceBefore=5 * mm, spaceAfter=2.5 * mm, keepWithNext=True),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontName=FONT, fontSize=10, leading=17, textColor=INK, spaceAfter=3 * mm),
        "small": ParagraphStyle("small", parent=base["BodyText"], fontName=FONT, fontSize=8.6, leading=13, textColor=INK),
        "small_center": ParagraphStyle("small_center", parent=base["BodyText"], fontName=FONT, fontSize=8.5, leading=13, textColor=INK, alignment=TA_CENTER),
        "tablehead": ParagraphStyle("tablehead", parent=base["BodyText"], fontName=FONT, fontSize=8.7, leading=12, textColor=WHITE, alignment=TA_CENTER),
        "coverlabel": ParagraphStyle("coverlabel", parent=base["BodyText"], fontName=FONT, fontSize=9, leading=14, textColor=MUTED),
        "covervalue": ParagraphStyle("covervalue", parent=base["BodyText"], fontName=FONT, fontSize=11, leading=16, textColor=INK),
        "note": ParagraphStyle("note", parent=base["BodyText"], fontName=FONT, fontSize=9.2, leading=14.5, textColor=INK),
    }


def table(data, widths, s, header=True, font=8.6):
    rows = []
    for r, row in enumerate(data):
        style = s["tablehead"] if header and r == 0 else s["small"]
        rows.append([P(str(cell), style) for cell in row])
    t = Table(rows, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.45, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]
    if header:
        commands.append(("BACKGROUND", (0, 0), (-1, 0), NAVY))
        commands.append(("TEXTCOLOR", (0, 0), (-1, 0), WHITE))
        for r in range(1, len(data)):
            if r % 2 == 0:
                commands.append(("BACKGROUND", (0, r), (-1, r), PALE_BLUE))
    t.setStyle(TableStyle(commands))
    return t


def info_band(left, right, s):
    t = Table([[P(left, s["small_center"]), P(right, s["note"])]], colWidths=[37 * mm, 137 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), TEAL),
        ("BACKGROUND", (1, 0), (1, 0), PALE),
        ("TEXTCOLOR", (0, 0), (0, 0), WHITE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.5, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    return t


def build():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pdfmetrics.registerFont(TTFont(FONT, FONT_FILE))
    s = styles()
    frame = Frame(18 * mm, 18 * mm, 174 * mm, 258 * mm, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc = BaseDocTemplate(str(OUT), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=18 * mm, title="葉神經科候診叫號系統第一階段導入規劃", author="葉神經科")
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=footer)])
    story = []

    # Cover
    story += [Spacer(1, 29 * mm), P("葉神經科", s["subtitle"]), P("候診叫號系統", s["title"]), P("第一階段導入規劃", s["subtitle"]), Spacer(1, 9 * mm)]
    story.append(info_band("本次決策", "第一階段導入無紙券候診與醫師快捷叫號；官方 LINE 僅列為第二階段自願式家屬通知。", s))
    story += [Spacer(1, 13 * mm)]
    cover = [
        [P("目的", s["coverlabel"]), P("不列印紙本號碼牌，仍維持清楚、可回查的候診秩序。", s["covervalue"])],
        [P("適用範圍", s["coverlabel"]), P("櫃台螢幕確認、候診顯示、醫師快捷叫號、原號回號及未來 LINE 通知規劃。", s["covervalue"])],
        [P("不納入範圍", s["coverlabel"]), P("健保卡串接、自助報到、線上預約、雲端候診與病歷系統改造。LINE 非病人報到前提。", s["covervalue"])],
        [P("文件版本", s["coverlabel"]), P("2026 年 10 月 28 日", s["covervalue"])],
    ]
    ct = Table(cover, colWidths=[35 * mm, 139 * mm])
    ct.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 0.45, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story += [ct, Spacer(1, 18 * mm), P("本規劃以單一診所、單一候診區為前提。無紙券為常態；對高齡、視聽或記憶困難者保留可重複使用的號碼卡作備援。", s["body"]), PageBreak()]

    # Page 2 decision and process
    story += [P("一  導入原則", s["h1"]), P("第一階段只處理現場候診與叫號。櫃台仍以現有系統完成掛號，並在小螢幕顯示當次候診序號、口頭告知病人；不列印號碼牌。醫師完成病歷及處方送出後，直接按實體快捷鍵叫下一位，無須再經由護理師。", s["body"])]
    story.append(table([
        ["原則", "現場做法", "判定標準"],
        ["流程不重做", "保留既有健保掛號與病歷系統。", "櫃台只增加一次取號動作。"],
        ["無紙券確認", "櫃台小螢幕顯示序號，並口頭確認。", "病人無須拿紙券仍知道候診序號。"],
        ["叫號由醫師控制", "病歷送出後按實體快捷鍵，可叫一般、回號或重叫。", "看診完成即由醫師決定下一位。"],
        ["資訊最小化", "公共端僅顯示候診號碼。", "不顯示姓名、病名或健保資料。"],
    ], [34 * mm, 78 * mm, 62 * mm], s))
    story += [Spacer(1, 7 * mm), P("二  現場流程", s["h1"]), P("病人完成掛號後，櫃台螢幕顯示其候診序號，櫃台口頭告知。醫師完成病歷與處方送出後，以快捷鍵決定叫一般候診或回號。公共設備僅處理候診序號。", s["body"]), ProcessDiagram(), Spacer(1, 4 * mm)]
    story.append(info_band("醫師電腦就是叫號端", "需在既有醫師電腦安裝廠商的本地叫號程式，或使用可接收 USB 快捷鍵的叫號主機。這是本地連線，不需要雲端；若既有病歷系統無正式介面，送出病歷後仍需由醫師按一次快捷鍵。", s))
    story.append(PageBreak())

    # Equipment and acceptance
    story += [P("三  設備需求與驗收", s["h1"]), P("採購時應要求同一廠商提供完整系統與現場測試，避免購入只能播報、但無法管理取號順序的單一叫號器。", s["body"])]
    story.append(table([
        ["設備", "建議數量", "用途"],
        ["叫號主機與本地控制程式", "1", "管理一般候診、回號、快捷鍵指令與設備同步。"],
        ["櫃台確認小螢幕", "1", "掛號完成後顯示候診序號，供櫃台與病人共同確認。"],
        ["候診顯示螢幕與喇叭", "1", "顯示目前號碼與播報叫號。"],
        ["醫師快捷鍵盤", "1", "一般號、回號、重叫與過號等四個實體按鍵。"],
        ["可重複使用號碼卡", "20 至 30", "僅供記憶、視聽或行動不便病人備援；非日常必發。"],
        ["醫師既有電腦", "1", "執行本地叫號程式；不必新增叫號終端。"],
        ["通訊方式", "依系統", "優先使用有線 LAN；無線方案須現場測試。"],
    ], [52 * mm, 30 * mm, 92 * mm], s))
    story += [Spacer(1, 7 * mm), P("驗收情境", s["h2"])]
    story.append(table([
        ["情境", "應有結果"],
        ["連續完成 20 筆報到", "序號連續、小螢幕更新正確，無重複或跳號。"],
        ["醫師按一般號快捷鍵", "2 秒內更新螢幕並播報下一個一般候診號。"],
        ["病人未到", "醫師可重叫；仍未到時標記過號。"],
        ["過號病人回來", "櫃台將原候診序號改為回號待叫；醫師可用回號快捷鍵叫入。"],
        ["設備或網路異常", "可立即切換人工紙牌與人工喊號。"],
    ], [61 * mm, 113 * mm], s))
    story += [Spacer(1, 7 * mm), P("供應商確認事項", s["h2"]), P("需提供設備清單、通訊方式、保固與到場維護條件；櫃台小螢幕應可顯示剛完成報到的序號至少 10 秒。若宣稱可串接，應提供正式 API 或 HIS 串接文件。", s["body"]), PageBreak()]

    # ERD
    story += [P("四  資料架構", s["h1"]), P("第一階段只保存候診與叫號所需資訊。病人姓名、健保卡號、身分證號與病情資料均不顯示於公共端，也不必串入叫號系統。若需回查過號，櫃台可人工輸入既有掛號流水號作為當日對照。", s["body"]), ERDDiagram(), Spacer(1, 5 * mm)]
    story.append(table([
        ["資料實體", "用途", "核心欄位"],
        ["診次", "區分上午、下午或晚診。", "日期、時段、啟用狀態"],
        ["候診紀錄", "記錄候診序號、回號狀態與既有掛號流水號。", "序號、診次、取號時間、狀態、掛號流水號"],
        ["叫號紀錄", "追蹤一般叫號、回號、重叫與過號。", "候診紀錄、動作、操作時間"],
        ["操作角色", "區分醫師、櫃台與管理者。", "角色、啟用狀態"],
        ["設備", "識別取號器、叫號器、螢幕與主機。", "設備類型、位置、啟用狀態"],
    ], [35 * mm, 70 * mm, 69 * mm], s))
    story += [Spacer(1, 7 * mm), P("候診號碼狀態", s["h2"])]
    story.append(table([
        ["狀態", "定義", "後續處理"],
        ["候診中", "已完成報到，尚未播報。", "可叫號或取消。"],
        ["已叫號", "已顯示並播報。", "可重叫、過號或完成。"],
        ["過號", "病人未到。", "病人回來後轉為回號待叫，保留原序號。"],
        ["回號待叫", "過號病人已回到候診區。", "醫師按回號快捷鍵叫入。"],
        ["完成", "已進入完成狀態。", "不可再叫號。"],
    ], [36 * mm, 73 * mm, 65 * mm], s))
    story.append(PageBreak())

    # Return queue rule
    story += [P("五  過號與回號規則", s["h1"]), P("每位病人報到時取得一個當日候診序號；過號後回來，仍使用同一個序號。系統以一般候診與回號待叫兩個內部佇列管理，醫師完成當位診療後，以快捷鍵選擇下一位。", s["body"])]
    story.append(info_band("同一號碼，兩個佇列", "一般候診依報到順序前進。病人過號回來後，由櫃台將原候診序號轉為回號待叫；醫師在適當時機按回號鍵叫入。病人不需記新號碼，也不需領取紙券。", s))
    story += [Spacer(1, 7 * mm)]
    story.append(table([
        ["步驟", "現場規則", "責任人"],
        ["第一次未到", "醫師按重叫鍵 1 次；仍未到時按過號鍵，系統保留原候診序號。", "醫師"],
        ["病人回來", "病人先到櫃台。櫃台以既有掛號流水號或當日清單找到原序號，改為回號待叫。", "櫃台"],
        ["範例", "16 號未到而過號；病人回來後仍是 16 號。醫師可在叫完 18 號後，再按回號鍵叫 16 號。", "櫃台"],
        ["醫師決定插入", "病歷與處方送出後，按回號快捷鍵，叫最早完成回號登記的病人。", "醫師"],
        ["叫號不倒退", "回號不影響一般候診的報到順序；一般佇列持續叫下一位，回號由醫師另行插入。", "系統"],
        ["特殊狀況", "診間內正在看診時不打斷；急性不適由醫師依臨床判斷優先處理。", "醫師"],
    ], [31 * mm, 103 * mm, 40 * mm], s))
    story += [Spacer(1, 8 * mm), P("系統要求", s["h2"]), P("系統必須維護一般候診與回號待叫兩個佇列。醫師快捷鍵至少包含一般號、回號、重叫與過號。病人回來時，櫃台只改變候診狀態，不產生新號碼或紙本憑證。", s["body"])]
    story += [P("病人說明", s["h2"]), P("過號病人回來後，應告知：已為您恢復候診，仍使用原本的候診序號；醫師會依現場看診進度叫號。", s["body"]), PageBreak()]

    # Copy
    story += [P("六  現場文案與操作規則", s["h1"]), P("所有公共文案僅傳達候診資訊，避免出現個人識別或健康資料。櫃台確認螢幕提供無紙券的候診序號提示。", s["body"])]
    story += [P("候診螢幕與櫃台確認螢幕", s["h2"])]
    story.append(table([
        ["位置", "建議文案"],
        ["螢幕標題", "葉神經科 候診叫號"],
        ["櫃台確認", "您的候診序號：16。請留意候診螢幕與語音叫號。"],
        ["目前叫號", "目前叫號 16"],
        ["候診提醒", "請依序候診，並留意螢幕與語音叫號。"],
        ["過號提醒", "如已過號，請洽櫃台恢復候診。"],
        ["備援號碼卡", "若您需要協助記住序號，請向櫃台索取可重複使用的號碼卡。"],
    ], [42 * mm, 132 * mm], s))
    story += [Spacer(1, 4 * mm), P("櫃台與醫師操作", s["h2"])]
    story.append(table([
        ["情境", "建議說法"],
        ["完成報到", "您好，已為您完成報到。您的候診序號是 16，請留意螢幕與語音叫號。"],
        ["病人詢問順序", "目前依候診號碼與看診進度安排；如需協助，請先告訴我們。"],
        ["病人已過號", "已為您恢復候診，仍使用原本的候診序號；醫師會依現場看診進度叫號。"],
        ["設備暫時故障", "叫號設備目前調整中，我們會改以人工方式通知，請留在候診區等候。"],
    ], [42 * mm, 132 * mm], s))
    story += [Spacer(1, 3 * mm), P("語音播報", s["h2"]), P("第一次叫號：請 16 號至診間外等候。<br/>重叫：再次提醒，請 16 號至診間外等候。", s["body"]), PageBreak()]

    # Deployment plan
    story += [P("七  導入計畫", s["h1"]), P("以三週為規劃基準；實際上線日期應依供應商交期、現場安裝條件與試行結果調整。", s["body"])]
    story.append(table([
        ["階段", "建議期間", "工作內容", "完成條件"],
        ["現況確認", "第 1 至 3 日", "確認現有設備、候診區視線、電源與網路位置。", "決定沿用或採購新設備。"],
        ["選型與採購", "第 4 至 10 日", "比較方案，要求演示無紙券確認、醫師快捷鍵與原號回號。", "確認設備與本地控制方式。"],
        ["安裝與設定", "第 11 至 15 日", "在醫師電腦設定快捷鍵、診次、一般與回號佇列、音量與顯示位置。", "完成完整流程及備援測試。"],
        ["試行", "第 16 至 20 日", "先以一個診次試行，記錄過號、回號、錯號與病人理解情況。", "依現場回饋調整設定。"],
        ["正式使用", "第 21 日起", "全診次啟用；每週檢視等候與過號情形。", "手寫紙牌退出常態流程。"],
    ], [27 * mm, 30 * mm, 68 * mm, 49 * mm], s))
    story += [Spacer(1, 8 * mm), P("上線前確認", s["h2"])]
    checklist = [
        "現有叫號設備的品牌、型號、照片與使用手冊。",
        "候診區與櫃台平面配置、最遠座位距離及可用電源。",
        "每日診次、是否有多位醫師，以及是否需區分診別或檢查別。",
        "醫師快捷鍵盤的位置、按鍵定義與病歷系統送出後的操作順序。",
        "櫃台確認螢幕是否清楚可見，以及備援號碼卡的清潔與回收方式。",
        "供應商保固、到場維護時限與後續維護費用。",
    ]
    for item in checklist:
        story.append(P("• " + item, s["body"]))
    story += [Spacer(1, 5 * mm), info_band("採購前必要演示", "櫃台完成報到後，小螢幕顯示候診序號 16；醫師完成一筆病歷送出後，可按一般號鍵叫下一位。16 號過號回來後，櫃台恢復為回號待叫，醫師按回號鍵可正確叫出 16 號。", s)]

    # Official LINE extension
    story.append(PageBreak())
    story += [P("八  官方 LINE 第二階段規劃", s["h1"]), P("官方 LINE 的角色是自願式候診提醒，主要服務熟悉手機的病人或家屬；不得取代櫃台報到、現場螢幕或語音叫號。", s["body"])]
    story.append(info_band("設計原則", "長者仍可完全不使用手機而順利看診。只有病人或家屬主動加入官方 LINE、完成當日綁定時，才發送個別候診通知。", s))
    story += [Spacer(1, 7 * mm), P("使用流程", s["h2"])]
    story.append(table([
        ["步驟", "做法", "必要條件"],
        ["加入好友", "病人或家屬掃官方 LINE QR Code，加入好友。", "完全自願；不加入仍走現場流程。"],
        ["選擇通知", "點選「家屬候診通知」功能，取得一次性綁定碼。", "由家屬操作，避免長者填寫資料。"],
        ["櫃台綁定", "櫃台將綁定碼連結到當日候診紀錄。", "僅限當日有效，診次結束即失效。"],
        ["自動提醒", "系統推播報到完成、即將輪到及恢復候診。", "需啟用 Messaging API 與安全後端服務。"],
    ], [31 * mm, 83 * mm, 60 * mm], s))
    story += [Spacer(1, 6 * mm), P("訊息與個資界線", s["h2"])]
    story.append(table([
        ["可傳送", "不可傳送"],
        ["已完成報到、候診序號、即將輪到、恢復候診。", "病名、診斷、藥物、檢查結果、健保卡號及身分證號。"],
        ["例：您已完成報到，候診序號為 16。", "不得以 LINE 作為醫療建議、緊急聯絡或正式診療通知。"],
    ], [87 * mm, 87 * mm], s))
    story += [Spacer(1, 6 * mm), P("啟動條件", s["h2"]), P("先完成第一階段至少一週試行，確認無紙券報到、原號回號與醫師快捷鍵穩定後，再評估 LINE。第二階段需另行確認官方帳號權限、訊息費用、後端維運、同意流程、綁定錯誤處理與資料保存期限。", s["body"])]
    story.append(info_band("立即建議動作", "先盤點現有叫號器品牌與接口、確認掛號系統是否可見每日流水號，並量測櫃台與候診區的螢幕位置。完成後，再請 2 至 3 家供應商現場演示無紙券報到、原號回號、醫師快捷鍵與離線備援。", s))

    story.append(PageBreak())
    story += [P("附件 A  廠商需求與驗收單", s["h1"]), P("請供應商逐項勾選並於現場演示；未能現場完成者，不列入採購承諾。", s["body"])]
    story.append(table([
        ["需求", "驗收標準", "供應商回覆"],
        ["無紙券報到", "櫃台小螢幕顯示剛報到的候診序號至少 10 秒。", "□ 可  □ 不可  □ 說明"],
        ["醫師快捷鍵", "一般、回號、重叫、過號四鍵均可由醫師電腦觸發。", "□ 可  □ 不可  □ 說明"],
        ["原號回號", "16 號過號回來後仍可叫 16 號，不產生新紙券。", "□ 可  □ 不可  □ 說明"],
        ["離線備援", "外網中斷時，叫號、螢幕與語音仍能運作。", "□ 可  □ 不可  □ 說明"],
        ["個資限制", "公共螢幕只顯示候診序號，不顯示姓名。", "□ 可  □ 不可  □ 說明"],
        ["既有設備", "確認 USB、LAN、序列埠或 API 可否與既有設備整合。", "□ 可  □ 不可  □ 說明"],
        ["服務條件", "列出安裝、教育訓練、保固、維護時限與總報價。", "□ 已提供"],
    ], [44 * mm, 85 * mm, 45 * mm], s))
    story += [Spacer(1, 8 * mm), info_band("必要演示", "請完成：櫃台報到 16 號、醫師一般叫號、16 號過號、櫃台恢復回號待叫、醫師叫回 16 號。", s)]

    story.append(PageBreak())
    story += [P("附件 B  現場操作卡", s["h1"]), P("供櫃台與醫師放置於工作區；按鍵名稱可依實際設備調整。", s["body"])]
    story.append(table([
        ["角色", "情境", "固定動作"],
        ["櫃台", "完成掛號", "按「完成報到」；確認小螢幕顯示序號；口頭告知病人。"],
        ["醫師", "看診完成", "送出病歷與處方後，按「一般叫號」叫下一位。"],
        ["醫師", "病人未到", "按「重叫」一次；仍未到時按「過號」。"],
        ["櫃台", "過號病人回來", "用當日掛號流水號找到原紀錄，改為「回號待叫」。"],
        ["醫師", "安排回號", "於適當時機按「回號」；不影響一般候診順序。"],
        ["櫃台", "需要協助記號", "借出大字可重複使用號碼卡，診後回收消毒。"],
        ["全員", "設備異常", "停止使用系統，改人工叫號；記錄最後成功叫號。"],
    ], [28 * mm, 38 * mm, 108 * mm], s))

    story.append(PageBreak())
    story += [P("附件 C  試行一週紀錄表", s["h1"]), P("每日診次結束後由櫃台記錄；一週後檢討是否調整螢幕、音量、快捷鍵或回號規則。", s["body"])]
    story.append(table([
        ["日期／診次", "報到數", "過號數", "回號數", "叫錯／重複", "設備異常", "病人回饋／改善"],
        ["____________", "____", "____", "____", "____", "____", "________________"],
        ["____________", "____", "____", "____", "____", "____", "________________"],
        ["____________", "____", "____", "____", "____", "____", "________________"],
        ["____________", "____", "____", "____", "____", "____", "________________"],
        ["____________", "____", "____", "____", "____", "____", "________________"],
    ], [30 * mm, 18 * mm, 18 * mm, 18 * mm, 28 * mm, 25 * mm, 37 * mm], s))
    story += [Spacer(1, 8 * mm), P("一週檢討問題", s["h2"]), P("1. 病人是否能看清／聽清叫號？  2. 櫃台能否快速找回過號病人？  3. 醫師快捷鍵是否有誤按？  4. 是否需要增加備援號碼卡？", s["body"])]

    story.append(PageBreak())
    story += [P("附件 D  技術架構與採購範圍", s["h1"]), P("MVP 採本地優先、雲端同步。現場叫號不依賴外網；雲端只提供 QR Code 查詢與未來的自願式通知服務。", s["body"])]
    story.append(table([
        ["層級", "用途", "MVP 範圍"],
        ["診所主機", "維持候診狀態、醫師快捷鍵、顯示器與語音。", "小型 Windows 電腦一台；外網中斷仍可使用。"],
        ["櫃台端", "完成報到、恢復回號及大字確認序號。", "既有電腦或櫃台操作介面，加一台小螢幕。"],
        ["醫師端", "完成診療後決定叫一般號或回號。", "既有醫師電腦加 USB 實體快捷鍵。"],
        ["候診區", "顯示目前叫號並播報。", "具內建喇叭的電視／螢幕，以 HDMI 連接主機。"],
        ["雲端網頁", "供已掛號病人或家屬遠端查看進度。", "固定 QR Code；僅顯示目前號碼、狀態與更新時間。"],
    ], [30 * mm, 70 * mm, 74 * mm], s))
    story += [Spacer(1, 7 * mm), P("採購與備援原則", s["h2"]), P("不將傳統叫號器作為主系統。既有設備只有在可接受 USB、LAN、序列埠或 API 控制時才評估沿用。MVP 不購買 UPS；電力或設備異常時，記錄最後成功叫號並改人工口頭叫號。", s["body"])]
    story += [P("聲音備援", s["h2"]), P("候診螢幕優先使用內建喇叭，主機以 HDMI 輸出畫面與聲音。若音量不足或內建喇叭故障，再連接主機的 3.5 mm 或 USB 外接喇叭。", s["body"])]
    story.append(info_band("公開網頁規則", "QR Code 網頁只供查看，不具叫號控制權，不顯示病人姓名、候診清單、診斷或預估精確等候時間。現場語音與螢幕為唯一有效叫號依據。", s))

    doc.build(story)
    print(OUT.resolve())


if __name__ == "__main__":
    build()
