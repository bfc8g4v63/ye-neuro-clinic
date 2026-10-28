# Ye Neuro Clinic

葉神經科候診叫號系統的規劃文件與未來實作專案。

## MVP 原則

- 長者友善：病人不用註冊、輸入手機或操作自助機。
- 無紙券：櫃台小螢幕顯示候診序號並口頭確認。
- 醫師主控：實體快捷鍵處理一般叫號、回號、重叫與過號。
- 原號回號：過號病人回來後保留原候診序號，由醫師決定何時叫回。
- 本地優先：現場叫號不依賴外網；QR Code 網頁只供查看公開進度。

## 文件

- `AGENTS.md`：跨對話／跨開發者的決策摘要。
- `docs/ROADMAP.md`：依驗收條件切分的交付路線圖。
- `docs/ON_SITE_UAT.md`：30 號假資料演練與現場設備驗收 SOP。
- `docs/SIMULATION_TEST_REPORT.md`：開發 NB 的模擬測試結果與現場待驗證項目。
- `output/pdf/`：正式規劃書與附件。
- `create_queue_system_pdf.py`：規劃書產生來源。

## 預計架構

```text
診所主機 → 櫃台端、醫師快捷鍵、候診螢幕與語音
     └── 雲端同步 → QR Code 公開候診頁、未來 LINE 與預約功能
```

不得提交病人資料、LINE Token、Cloudflare Token、健保資訊或任何正式環境密鑰。
