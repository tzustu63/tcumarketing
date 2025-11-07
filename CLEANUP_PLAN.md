# .md 文件整理計劃

## 📋 文件分類

### ✅ 保留的重要文件

#### 核心文檔
- `README.md` - 專案主要說明
- `QUICK_START.md` - 快速開始指南
- `USER_MANUAL.md` - 用戶手冊
- `CHANGELOG.md` - 變更日誌
- `CONTRIBUTING.md` - 貢獻指南
- `ENV_VARIABLES.md` - 環境變數說明

#### 部署相關（當前使用）
- `DEPLOYMENT.md` - 通用部署指南
- `DIGITALOCEAN_DEPLOYMENT_GUIDE.md` - DigitalOcean 完整部署指南
- `QUICK_DEPLOY.md` - 快速部署指南（最簡單）
- `DIGITALOCEAN_TROUBLESHOOTING.md` - 故障排除指南

#### 功能文檔
- `PERFORMANCE_OPTIMIZATION_GUIDE.md` - 效能優化指南
- `backend/` 目錄下的技術文檔

---

### ❌ 可刪除的文件

#### 重複的部署狀態報告
- `DEPLOYMENT_SUCCESS.md`
- `DEPLOYMENT_COMPLETE.md`
- `DEPLOYMENT_STATUS.md`
- `DEPLOYMENT_SUCCESS_REPORT.md`
- `DEPLOYMENT_FIXED.md`
- `FINAL_DEPLOYMENT_STATUS.md`
- `FINAL_DEPLOYMENT_CHECKLIST.md`
- `MIGRATION_SUCCESS.md`

#### 臨時的 SSH/CORS 修復文件（已解決）
- `FIX_SSH_CONNECTION.md`
- `SSH_CONNECTION_SUMMARY.md`
- `ADD_SSH_KEY_TO_DO.md`
- `ADD_KEY_VIA_CONSOLE.md`
- `STEP_BY_STEP_SSH_SETUP.md`
- `CORS_FIX_COMPLETE.md`
- `CORS_AND_DB_FIX.md`

#### Railway 相關（不使用）
- `RAILWAY_DEPLOYMENT_GUIDE.md`
- `RAILWAY_DEPLOYMENT_ISSUES.md`
- `RAILWAY_CLI_DEPLOYMENT.md`

#### 舊的部署指令（已整合）
- `DEPLOY_INSTRUCTIONS.md` - 內容已整合到其他文件

#### 其他臨時/舊文件
- `VPS_PROVIDERS_COMPARISON.md` - 比較文件，已選擇 DigitalOcean
- `DEPLOY_MANUAL_STEPS.md` - 內容已整合到 QUICK_DEPLOY.md

#### 舊的任務完成摘要
- `TASK_10_COMPLETION_SUMMARY.md`
- `TASK_11_IMPLEMENTATION_SUMMARY.md`
- `TASK_12_COMPLETION_SUMMARY.md`
- `TASK_13_COMPLETION_SUMMARY.md`
- `TASK_14_COMPLETION_SUMMARY.md`
- `backend/TASK_10_COMPLETION_SUMMARY.md`

#### 臨時修復文件（已解決）
- `FIX_CELERY_BEAT.md`
- `FIX_COUNTRY_DATA.md`
- `FIX_TASK_MONITOR_REGISTRATION.md`
- `VERIFY_KEYWORD_DISPLAY.md`
- `ADD_KEYWORD_TO_CONTACTS.md`
- `ADD_KEYWORD_CITY_FILTERS.md`
- `TASK_CLICK_NAVIGATION.md`
- `TASK_PROGRESS_MECHANISM.md`
- `SIMPLIFIED_AUTO_COMPLETION.md`

---

## 🎯 整理後的文件結構

```
根目錄/
├── README.md                          # 專案說明
├── QUICK_START.md                     # 快速開始
├── USER_MANUAL.md                     # 用戶手冊
├── CHANGELOG.md                       # 變更日誌
├── CONTRIBUTING.md                    # 貢獻指南
├── ENV_VARIABLES.md                  # 環境變數
├── DEPLOYMENT.md                      # 通用部署指南
├── DIGITALOCEAN_DEPLOYMENT_GUIDE.md   # DigitalOcean 完整指南
├── QUICK_DEPLOY.md                    # 快速部署（推薦）
├── DIGITALOCEAN_TROUBLESHOOTING.md    # 故障排除
└── PERFORMANCE_OPTIMIZATION_GUIDE.md  # 效能優化

backend/
└── [技術文檔保留]

docs/
└── [文檔保留]

frontend/
└── README.md                          # 保留
```

