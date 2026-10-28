from pathlib import Path
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


OUT = Path("deliverables") / "葉神經科_現場叫號系統_MVP_規劃書.docx"
FONT = "Microsoft JhengHei"
MONO = "Consolas"
NAVY = "1F4E78"
LIGHT_BLUE = "EAF2F8"
LIGHT_GRAY = "F5F6F7"
MID_GRAY = "D9D9D9"


def set_font(run, name=FONT, size=None, bold=None, color=None):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run._element.rPr.rFonts.set(qn("w:ascii"), name)
    run._element.rPr.rFonts.set(qn("w:hAnsi"), name)
    if size:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if color:
        run.font.color.rgb = RGBColor.from_string(color)


def shade(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_border(cell, color=MID_GRAY):
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = tc_pr.first_child_found_in("w:tcBorders")
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tc_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = qn(f"w:{edge}")
        element = borders.find(tag)
        if element is None:
            element = OxmlElement(f"w:{edge}")
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "6")
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), color)


def set_cell_margins(cell, top=90, start=110, bottom=90, end=110):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for m, v in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{m}"))
        if node is None:
            node = OxmlElement(f"w:{m}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(v))
        node.set(qn("w:type"), "dxa")


def set_repeat_table_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def add_text(paragraph, text, size=11, bold=False, color="000000", font=FONT):
    run = paragraph.add_run(text)
    set_font(run, font, size, bold, color)
    return run


def add_paragraph(doc, text="", style=None, before=0, after=6, align=None, size=11):
    p = doc.add_paragraph(style=style)
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = 1.35
    if align is not None:
        p.alignment = align
    if text:
        add_text(p, text, size=size)
    return p


def add_bullet(doc, text, level=0):
    p = doc.add_paragraph(style="List Bullet" if level == 0 else "List Bullet 2")
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.25
    add_text(p, text, size=10.5)
    return p


def add_heading(doc, text, level=1):
    p = doc.add_paragraph(style=f"Heading {level}")
    p.paragraph_format.space_before = Pt(15 if level == 1 else 10)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    add_text(p, text, size=15 if level == 1 else 12.5, bold=True)
    return p


def add_table(doc, headers, rows, widths=None, font_size=9.5):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.style = "Table Grid"
    header = table.rows[0]
    set_repeat_table_header(header)
    for i, text in enumerate(headers):
        cell = header.cells[i]
        shade(cell, NAVY)
        set_cell_border(cell)
        set_cell_margins(cell)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        if widths:
            cell.width = Inches(widths[i])
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        add_text(p, text, size=font_size, bold=True, color="FFFFFF")
    for row_index, row in enumerate(rows):
        cells = table.add_row().cells
        for i, value in enumerate(row):
            cell = cells[i]
            if row_index % 2 == 1:
                shade(cell, LIGHT_BLUE)
            set_cell_border(cell)
            set_cell_margins(cell)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            if widths:
                cell.width = Inches(widths[i])
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.15
            add_text(p, str(value), size=font_size)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return table


def add_code_block(doc, lines):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.cell(0, 0)
    shade(cell, LIGHT_GRAY)
    set_cell_border(cell, "B7C3D0")
    set_cell_margins(cell, top=140, start=160, bottom=140, end=160)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.1
    for index, line in enumerate(lines):
        if index:
            p.add_run("\n")
        add_text(p, line, size=8.7, font=MONO)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def add_section_break(doc):
    doc.add_page_break()


def suppress_title_rule(paragraph):
    p_pr = paragraph._p.get_or_add_pPr()
    p_bdr = p_pr.find(qn("w:pBdr"))
    if p_bdr is None:
        p_bdr = OxmlElement("w:pBdr")
        p_pr.append(p_bdr)
    bottom = p_bdr.find(qn("w:bottom"))
    if bottom is None:
        bottom = OxmlElement("w:bottom")
        p_bdr.append(bottom)
    bottom.set(qn("w:val"), "nil")


def setup_styles(doc):
    normal = doc.styles["Normal"]
    normal.font.name = FONT
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    normal.font.size = Pt(11)
    for name in ("Title", "Heading 1", "Heading 2", "List Bullet", "List Bullet 2"):
        style = doc.styles[name]
        style.font.name = FONT
        style._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        style.font.color.rgb = RGBColor(0, 0, 0)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.78)
    section.right_margin = Inches(0.78)
    setup_styles(doc)

    # Cover and decision
    p = doc.add_paragraph(style="Title")
    p.paragraph_format.space_before = Pt(70)
    p.paragraph_format.space_after = Pt(14)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_text(p, "葉神經科 現場叫號系統 MVP 規劃書", size=25, bold=True)
    suppress_title_rule(p)
    p = add_paragraph(doc, "獨立式取號與護理叫號方案", after=28, align=WD_ALIGN_PARAGRAPH.CENTER, size=14)
    meta = add_table(doc, ["文件項目", "內容"], [
        ["文件目的", "確認第一階段現場叫號方案、採購需求與驗收標準"],
        ["適用範圍", "櫃台報到後取號、候診顯示、護理師叫號與過號處理"],
        ["版本", "0.1"],
        ["日期", "2026 年 10 月 28 日"],
    ], widths=[1.35, 5.65], font_size=10)
    add_heading(doc, "執行結論", 1)
    add_paragraph(doc, "第一階段採購完整的獨立式取號與叫號設備，不與健保卡、既有掛號系統或雲端預約串接。櫃台在既有系統完成掛號後，按取號器列印候診號碼；護理師依醫師節奏按下叫號器。此作法僅增加一個櫃台操作動作，能立即取代手寫紙牌，並保留現有看診習慣。", after=8)
    add_paragraph(doc, "本 MVP 的選型重點不是單買一個叫號按鈕，而是採購同一套可同步管理取號、票券列印、候診螢幕、語音與護理師叫號的設備。", after=10)
    add_heading(doc, "MVP 不包含項目", 2)
    for t in ["健保卡讀取或健保系統串接", "自助報到機與線上預約", "手機候診通知與雲端叫號", "病歷、處方、收費或健保申報功能重做"]:
        add_bullet(doc, t)

    add_heading(doc, "一 現況與目標", 1)
    add_paragraph(doc, "葉神經科目前由醫師在完成一位病人的診療後，以口頭方式通知護理師，再由護理師叫下一位病人。櫃台在病人交付健保卡並完成掛號時，另以手寫紙牌告知候診號碼。系統化的第一步應聚焦在候診秩序與叫號可靠性，而非擴大至醫院級的自助化流程。", after=8)
    add_table(doc, ["目標", "MVP 做法", "成功判準"], [
        ["取代手寫號碼", "櫃台取號器直接列印紙本號碼牌", "號碼清楚、無重複、可快速補印"],
        ["保留醫師節奏", "護理師在醫師示意後按下一號", "不改變看診順序的決定權"],
        ["讓病人不漏聽", "大字體候診顯示加上語音播報", "高齡或聽力不便者可看見或聽見"],
        ["降低個資暴露", "公共螢幕只顯示候診號碼", "不顯示姓名、病名或掛號資料"],
        ["維持可營運性", "保留人工叫號與紙本備援", "設備或網路故障時診間不中斷"],
    ], widths=[1.3, 3.2, 2.5])
    add_heading(doc, "二 目標流程", 1)
    add_code_block(doc, [
        "病人交健保卡 -> 櫃台完成既有掛號 -> 櫃台取號列印 -> 候診", 
        "醫師示意護理師 -> 護理師按下一號或指定號碼 -> 螢幕與語音同步播報", 
    ])
    add_table(doc, ["角色", "操作", "系統輸出"], [
        ["櫃台", "完成既有掛號後按取號", "列印票券與建立候診號碼"],
        ["病人", "持票在候診區等待", "看到號碼並聽到語音提示"],
        ["醫師", "決定何時進入下一位病人", "維持現有口頭通知方式"],
        ["護理師", "按下一號、重叫或指定叫號", "螢幕與語音即時同步"],
    ], widths=[1.0, 2.65, 3.35])
    add_section_break(doc)
    add_heading(doc, "三 設備與場域配置", 1)
    add_table(doc, ["設備", "數量", "放置位置", "必要能力"], [
        ["叫號主機或控制器", "1", "櫃台內或資訊設備區", "管理診次、同步各設備、可設定號碼前綴"],
        ["櫃台取號器與票券印表機", "1", "櫃台", "按鍵取號、熱感列印、可重印與補號"],
        ["候診顯示螢幕與喇叭", "1", "候診區正面且可見處", "大字體、語音、可顯示目前與最近叫號"],
        ["護理師叫號器", "1 至 2", "護理站或診間外", "下一號、重叫、指定叫號、過號處理"],
        ["網路或通訊模組", "視系統", "設備之間", "有線 LAN 優先；廠商無線方案須現場測試"],
    ], widths=[1.65, 0.75, 1.4, 3.2])
    add_paragraph(doc, "不需另外部署一般電腦作為終端，前提是供應商提供完整的獨立式叫號主機。只有在未來要把既有掛號資料自動帶入、插健保卡後自動報到或加入報表整合時，才需要櫃台電腦與既有系統供應商協作。", after=4)

    add_section_break(doc)
    add_heading(doc, "四 功能需求與例外處理", 1)
    add_table(doc, ["功能", "最低需求", "驗收方式"], [
        ["取號", "櫃台每按一次即產生唯一當日號碼並列印票券", "連續取 20 張票，號碼連續且票面清楚"],
        ["叫下一號", "護理師單鍵呼叫下一張待候診票", "按鍵後 2 秒內更新螢幕並播報"],
        ["重叫", "可重播目前號碼", "連按三次後顯示與語音均正確"],
        ["指定叫號", "可輸入已過號或需回叫的號碼", "指定號碼顯示與播報正確"],
        ["診次區分", "上午、下午、晚診可獨立編號或使用前綴", "不同診次不混號"],
        ["日結", "可結束本診次並於下一診次重新起號", "隔一診次測試不沿用舊號碼"],
        ["斷線備援", "可立即改用人工紙牌與人工喊號", "演練一次，診療流程不中斷"],
    ], widths=[1.1, 3.5, 2.4])
    add_heading(doc, "過號規則", 2)
    add_bullet(doc, "病人未到時，護理師先重叫一次；仍未到則標記為過號。")
    add_bullet(doc, "過號病人回到候診區後，請先至櫃台或護理站確認，再由護理師以指定叫號方式安排回診。")
    add_bullet(doc, "插隊、急性不適或需要立即協助的情況，不以候診號碼處理，改依醫師或護理師的臨床判斷。")
    add_heading(doc, "隱私與操作原則", 2)
    add_bullet(doc, "公共顯示器只顯示候診號碼，例如 A-023。")
    add_bullet(doc, "票券、螢幕和語音不呈現姓名、身分證號、健保卡號、病名或檢查項目。")
    add_bullet(doc, "MVP 不保存健保卡資料；健保掛號仍由現有受控系統處理。")

    add_section_break(doc)
    add_heading(doc, "五 採購與現場驗證清單", 1)
    add_table(doc, ["確認項目", "供應商應提供的證明"], [
        ["完整系統範圍", "明列主機、取號器、票券機、螢幕、喇叭、叫號器與安裝內容"],
        ["設備通訊", "標明有線 LAN、Wi Fi、RS 232 或廠商自有無線方式"],
        ["多操作點", "可支援至少一台櫃台取號器與兩支護理師叫號器"],
        ["號碼流程", "可展示取號、下一號、重叫、指定叫號與過號回叫"],
        ["現場可視性", "確認候診區最遠座位能看清號碼並聽見合理音量"],
        ["維護服務", "載明保固、到場處理時限、耗材型號和備品建議"],
        ["未來串接", "若宣稱可串接，須提供 API 或 HIS 串接文件，不以設備互通替代"],
    ], widths=[1.6, 5.4])
    add_paragraph(doc, "驗機時應以實際場景演示：櫃台列印 A-023 後，護理師按下一號，候診螢幕與語音必須同步正確叫出 A-023。這項演示成功，才代表設備符合本 MVP 的核心需求。", after=6)

    add_section_break(doc)
    add_heading(doc, "六 資料模型 ERD", 1)
    add_paragraph(doc, "以下 ERD 是獨立式叫號系統的最小資料結構。其設計刻意不建立病人或健保卡資料表，以降低第一階段的個資處理範圍。若設備是純硬體且不提供資料匯出，可把此 ERD 視為未來升級至本地管理介面時的資料契約。", after=8)
    add_code_block(doc, [
        "[CLINIC_SESSION] 1 -------- * [QUEUE_TICKET] 1 -------- * [CALL_EVENT]",
        "       |                           |                         |",
        "       |                           |                         |",
        "       |                           +--- created by ----------+",
        "       |                                                     ",
        "       +-------------------- 1 -------- * [DEVICE]         ",
        "                                     \\                     ",
        "[OPERATOR] 1 ---------------------------------------------- * [CALL_EVENT]",
        "",
        "CLINIC_SESSION: one診次      QUEUE_TICKET: one候診號碼",
        "CALL_EVENT: one叫號動作      OPERATOR: one操作人員角色",
        "DEVICE: one取號或叫號設備",
    ])
    add_table(doc, ["實體", "主鍵", "主要欄位", "關係與說明"], [
        ["CLINIC_SESSION", "session_id", "session_date, session_code, status, opened_at, closed_at", "一個診次有多張候診票。session_code 例如 AM 或 PM。"],
        ["QUEUE_TICKET", "ticket_id", "session_id, ticket_no, status, issued_at, called_at", "每張票屬於一個診次；不保存姓名或健保資料。"],
        ["CALL_EVENT", "call_event_id", "ticket_id, operator_id, device_id, action, occurred_at", "記錄下一號、重叫、指定叫號、過號與取消等動作。"],
        ["OPERATOR", "operator_id", "role, display_name, active", "櫃台、護理師或管理者；MVP 可僅記錄角色，不必保存個人姓名。"],
        ["DEVICE", "device_id", "device_type, location, active", "取號器、叫號器、候診螢幕或主機，用於維護與事件追蹤。"],
    ], widths=[1.45, 1.1, 2.55, 2.1], font_size=8.7)
    add_section_break(doc)
    add_heading(doc, "狀態定義", 2)
    add_table(doc, ["QUEUE_TICKET 狀態", "意義", "允許下一步"], [
        ["WAITING", "已取號並等待", "CALLED 或 CANCELLED"],
        ["CALLED", "已在螢幕與語音播報", "CALLED 重叫、MISSED 或 COMPLETED"],
        ["MISSED", "過號", "CALLED 指定回叫或 CANCELLED"],
        ["COMPLETED", "已完成看診流程", "不再叫號"],
        ["CANCELLED", "取消或誤取", "不再叫號"],
    ], widths=[2.15, 2.4, 2.65])

    add_heading(doc, "七 病人與院內操作文案", 1)
    add_heading(doc, "候診螢幕", 2)
    add_table(doc, ["位置", "建議文案"], [
        ["標題", "葉神經科 候診叫號"],
        ["目前叫號", "目前叫號 A-023"],
        ["提醒", "請依序候診，並留意螢幕與語音叫號。"],
        ["過號說明", "如已過號，請洽櫃台或護理人員協助安排。"],
    ], widths=[1.6, 5.4])
    add_heading(doc, "紙本號碼牌", 2)
    add_code_block(doc, [
        "葉神經科", 
        "您的候診號碼", 
        "A-023", 
        "請在候診區等候螢幕與語音叫號", 
        "如已過號，請洽櫃台或護理人員", 
    ])
    add_section_break(doc)
    add_heading(doc, "櫃台與護理師話術", 2)
    add_table(doc, ["情境", "建議說法"], [
        ["交付號碼牌", "您好，已為您完成報到。這是您今天的候診號碼，請在候診區留意螢幕與語音叫號。"],
        ["病人詢問等待順序", "目前依候診號碼與看診進度安排；如有需要協助，請先告訴我們。"],
        ["過號病人回來", "您剛才已過號，我們先為您登記，護理師會依現場看診進度安排回叫。"],
        ["設備暫時故障", "叫號設備目前調整中，我們會改以人工方式通知，請先保留您的號碼牌。"],
    ], widths=[1.85, 5.15])
    add_heading(doc, "語音播報", 2)
    add_bullet(doc, "第一次叫號：請 A-023 號至診間外等候。")
    add_bullet(doc, "重叫：再次提醒，請 A-023 號至診間外等候。")
    add_bullet(doc, "避免播報病人姓名、病情、檢查或處置資訊。")

    add_section_break(doc)
    add_heading(doc, "八 執行計畫", 1)
    add_table(doc, ["階段", "時間", "工作內容", "完成條件"], [
        ["0 現況確認", "第 1 至 3 日", "確認現有設備品牌型號、候診區視線、電源與網路；取得供應商規格。", "確認沿用或採購新設備的決策。"],
        ["1 選型與採購", "第 4 至 10 日", "以本文件功能清單比較至少兩家方案，要求現場或遠端流程演示。", "簽核完整設備與維護範圍。"],
        ["2 安裝與設定", "第 11 至 15 日", "安裝主機、取號器、螢幕、喇叭與叫號器；設定診次與號碼前綴。", "完成全流程測試及備援演練。"],
        ["3 試行", "第 16 至 20 日", "以一個診次開始試行，記錄過號、叫錯號、病人理解度與設備異常。", "完成調整並由櫃台與護理師確認可用。"],
        ["4 正式上線", "第 21 日起", "全診次使用；每週檢視等待與過號情形。", "系統穩定且紙本手寫牌停止作為常態流程。"],
    ], widths=[1.15, 1.15, 3.0, 1.7], font_size=8.8)
    add_heading(doc, "啟動前待確認事項", 2)
    for t in [
        "現有叫號設備的品牌、型號、照片與使用手冊。",
        "候診區與櫃台的平面配置、最遠座位距離、可用電源與網路位置。",
        "每日診次、是否有多位醫師、是否需要分診別或檢查別的號碼。",
        "護理師需要的叫號器數量與擺放位置。",
        "供應商的保固、到場維護與耗材費用。",
    ]:
        add_bullet(doc, t)

    doc.core_properties.title = "葉神經科 現場叫號系統 MVP 規劃書"
    doc.core_properties.subject = "獨立式取號與護理叫號方案"
    doc.core_properties.author = "葉神經科"
    doc.core_properties.comments = ""
    doc.save(OUT)
    print(OUT.resolve())


if __name__ == "__main__":
    main()
