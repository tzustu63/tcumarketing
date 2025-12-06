# 貢獻指南 (Contributing Guide)

感謝您對慈濟大學招生通路自動開發系統的關注！本文件說明如何為專案做出貢獻。

## 目錄

- [行為準則](#行為準則)
- [如何貢獻](#如何貢獻)
- [開發環境設定](#開發環境設定)
- [程式碼規範](#程式碼規範)
- [提交規範](#提交規範)
- [測試要求](#測試要求)
- [文件撰寫](#文件撰寫)
- [審查流程](#審查流程)

## 行為準則

### 我們的承諾

為了營造開放和友善的環境，我們承諾：

- 使用友善和包容的語言
- 尊重不同的觀點和經驗
- 優雅地接受建設性批評
- 關注對社群最有利的事情
- 對其他社群成員表示同理心

### 不可接受的行為

- 使用性化的語言或圖像
- 人身攻擊或侮辱性評論
- 公開或私下騷擾
- 未經許可發布他人的私人資訊
- 其他不道德或不專業的行為

## 如何貢獻

### 回報問題 (Bug Report)

發現問題？請提交 Issue 並包含：

1. **問題描述**: 清楚描述問題
2. **重現步驟**: 詳細的重現步驟
3. **預期行為**: 應該發生什麼
4. **實際行為**: 實際發生了什麼
5. **環境資訊**: 
   - 作業系統
   - Docker 版本
   - Python 版本
   - 瀏覽器版本（前端問題）
6. **錯誤日誌**: 相關的錯誤訊息或日誌
7. **截圖**: 如果適用

**Issue 範本**:

```markdown
## 問題描述
[清楚描述問題]

## 重現步驟
1. 
2. 
3. 

## 預期行為
[描述預期行為]

## 實際行為
[描述實際行為]

## 環境資訊
- OS: [e.g. macOS 13.0]
- Docker: [e.g. 20.10.21]
- Python: [e.g. 3.11.0]

## 錯誤日誌
```
[貼上錯誤日誌]
```

## 截圖
[如果適用，請附上截圖]
```

### 功能請求 (Feature Request)

想要新功能？請提交 Issue 並包含：

1. **功能描述**: 清楚描述想要的功能
2. **使用場景**: 為什麼需要這個功能
3. **建議實作**: 如何實作（可選）
4. **替代方案**: 考慮過的其他方案
5. **額外資訊**: 其他相關資訊

### 提交程式碼

1. **Fork 專案**
   ```bash
   # 在 GitHub 上 Fork 專案
   # 克隆你的 Fork
   git clone https://github.com/your-username/indonesia-recruitment-automation.git
   cd indonesia-recruitment-automation
   ```

2. **建立分支**
   ```bash
   # 從 main 分支建立新分支
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

3. **進行變更**
   - 遵循程式碼規範
   - 撰寫清晰的提交訊息
   - 新增或更新測試
   - 更新相關文件

4. **測試變更**
   ```bash
   # 執行測試
   cd backend
   pytest
   
   # 檢查程式碼風格
   flake8 app/
   black --check app/
   ```

5. **提交變更**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   git push origin feature/your-feature-name
   ```

6. **建立 Pull Request**
   - 在 GitHub 上建立 Pull Request
   - 填寫 PR 範本
   - 等待審查

## 開發環境設定

### 後端開發

1. **安裝 Python 依賴**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # 開發依賴
   ```

2. **啟動資料庫和 Redis**
   ```bash
   docker-compose up -d db redis
   ```

3. **執行資料庫遷移**
   ```bash
   alembic upgrade head
   ```

4. **啟動開發伺服器**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **啟動 Celery Worker**
   ```bash
   celery -A app.celery_app worker --loglevel=debug
   ```

### 前端開發

1. **安裝 Node.js 依賴**
   ```bash
   cd frontend
   npm install
   ```

2. **啟動開發伺服器**
   ```bash
   npm start
   ```

3. **執行測試**
   ```bash
   npm test
   ```

### 開發工具

推薦使用以下工具：

- **IDE**: VS Code, PyCharm
- **Python 格式化**: Black, isort
- **Python Linter**: Flake8, Pylint
- **JavaScript 格式化**: Prettier
- **JavaScript Linter**: ESLint
- **Git 工具**: GitKraken, SourceTree

## 程式碼規範

### Python 程式碼規範

遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 風格指南。

**格式化工具**:
```bash
# 使用 Black 格式化
black app/

# 使用 isort 排序 import
isort app/
```

**Linting**:
```bash
# 使用 Flake8 檢查
flake8 app/ --max-line-length=100

# 使用 Pylint 檢查
pylint app/
```

**命名規範**:
- 類別: `PascalCase` (例如: `ContactExtractor`)
- 函數/方法: `snake_case` (例如: `extract_email`)
- 常數: `UPPER_SNAKE_CASE` (例如: `MAX_RETRIES`)
- 私有成員: `_leading_underscore` (例如: `_internal_method`)

**文件字串**:
```python
def extract_email(text: str) -> List[str]:
    """
    從文本中萃取 Email 地址。
    
    Args:
        text: 要處理的文本
        
    Returns:
        萃取到的 Email 地址列表
        
    Raises:
        ValueError: 當輸入為空時
    """
    pass
```

### JavaScript/React 程式碼規範

遵循 [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)。

**格式化工具**:
```bash
# 使用 Prettier 格式化
npm run format

# 檢查格式
npm run format:check
```

**Linting**:
```bash
# 使用 ESLint 檢查
npm run lint

# 自動修正
npm run lint:fix
```

**命名規範**:
- 元件: `PascalCase` (例如: `TaskList`)
- 函數: `camelCase` (例如: `fetchTasks`)
- 常數: `UPPER_SNAKE_CASE` (例如: `API_BASE_URL`)
- 檔案: `PascalCase.js` (元件) 或 `camelCase.js` (工具)

### SQL 規範

```sql
-- 使用大寫關鍵字
SELECT id, name, email
FROM contacts
WHERE institution_type = '高中'
ORDER BY created_at DESC;

-- 適當的縮排
CREATE TABLE contacts (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 提交規範

使用 [Conventional Commits](https://www.conventionalcommits.org/) 規範。

### 提交訊息格式

```
<類型>(<範圍>): <簡短描述>

<詳細描述>

<頁尾>
```

### 類型

- `feat`: 新功能
- `fix`: 錯誤修正
- `docs`: 文件變更
- `style`: 程式碼格式（不影響功能）
- `refactor`: 重構（不是新功能也不是修正）
- `perf`: 效能改進
- `test`: 新增或修改測試
- `chore`: 建置流程或輔助工具變更
- `ci`: CI 配置變更

### 範圍

- `api`: API 相關
- `scraper`: 爬蟲相關
- `extractor`: 萃取模組
- `frontend`: 前端
- `db`: 資料庫
- `docs`: 文件
- `config`: 配置

### 範例

```bash
# 新功能
git commit -m "feat(scraper): add Instagram scraper support"

# 錯誤修正
git commit -m "fix(api): resolve CORS issue for production"

# 文件更新
git commit -m "docs: update deployment guide"

# 重構
git commit -m "refactor(extractor): improve email extraction logic"

# 效能改進
git commit -m "perf(db): add index on contacts table"
```

### 詳細提交訊息範例

```
feat(scraper): add Instagram scraper support

- Implement Instagram page scraping
- Extract contact info from bio
- Handle authentication requirements
- Add rate limiting for Instagram API

Closes #123
```

## 測試要求

### 後端測試

**單元測試**:
```python
# tests/test_contact_extractor.py
import pytest
from app.extractor.contact_extractor import ContactExtractor

def test_extract_email():
    extractor = ContactExtractor()
    text = "Contact us at info@example.com"
    emails = extractor.extract_emails(text)
    assert "info@example.com" in emails

def test_extract_whatsapp():
    extractor = ContactExtractor()
    text = "WhatsApp: +62 812-3456-7890"
    numbers = extractor.extract_whatsapp(text)
    assert "+62 812-3456-7890" in numbers
```

**執行測試**:
```bash
# 執行所有測試
pytest

# 執行特定測試
pytest tests/test_contact_extractor.py

# 顯示覆蓋率
pytest --cov=app tests/

# 生成 HTML 覆蓋率報告
pytest --cov=app --cov-report=html tests/
```

**測試覆蓋率要求**:
- 新功能: ≥ 80%
- 核心模組: ≥ 90%
- 整體專案: ≥ 70%

### 前端測試

**元件測試**:
```javascript
// src/components/__tests__/TaskList.test.js
import { render, screen } from '@testing-library/react';
import TaskList from '../TaskList';

test('renders task list', () => {
  const tasks = [
    { id: 1, keyword: 'Test', status: 'pending' }
  ];
  render(<TaskList tasks={tasks} />);
  expect(screen.getByText('Test')).toBeInTheDocument();
});
```

**執行測試**:
```bash
# 執行所有測試
npm test

# 執行特定測試
npm test TaskList

# 顯示覆蓋率
npm test -- --coverage
```

## 文件撰寫

### 程式碼文件

- 所有公開 API 必須有文件字串
- 複雜邏輯需要註解說明
- 使用清晰的變數和函數名稱

### 使用者文件

更新以下文件（如適用）:

- `README.md`: 專案概述
- `USER_MANUAL.md`: 使用者操作手冊
- `DEPLOYMENT.md`: 部署指南
- `ENV_VARIABLES.md`: 環境變數說明
- `CHANGELOG.md`: 更新日誌

### API 文件

- 使用 FastAPI 的自動文件生成
- 在路由中添加清晰的描述
- 提供請求/回應範例

```python
@router.post("/tasks", response_model=TaskResponse)
async def create_task(
    task: TaskCreateRequest,
    db: Session = Depends(get_db)
):
    """
    建立新的搜尋任務。
    
    - **keyword**: 搜尋關鍵字
    - **city**: 目標城市
    - **target_platforms**: 目標平台列表
    - **max_results**: 最大結果數（預設: 100）
    """
    pass
```

## 審查流程

### Pull Request 檢查清單

提交 PR 前請確認：

- [ ] 程式碼遵循專案規範
- [ ] 所有測試通過
- [ ] 新增了必要的測試
- [ ] 更新了相關文件
- [ ] 提交訊息符合規範
- [ ] 沒有合併衝突
- [ ] CI/CD 檢查通過

### PR 範本

```markdown
## 變更描述
[描述這個 PR 做了什麼]

## 變更類型
- [ ] 新功能
- [ ] 錯誤修正
- [ ] 重構
- [ ] 文件更新
- [ ] 其他

## 相關 Issue
Closes #[issue number]

## 測試
[描述如何測試這些變更]

## 截圖
[如果適用，請附上截圖]

## 檢查清單
- [ ] 程式碼遵循專案規範
- [ ] 所有測試通過
- [ ] 新增了必要的測試
- [ ] 更新了相關文件
```

### 審查標準

審查者會檢查：

1. **功能性**: 變更是否達到預期目的
2. **程式碼品質**: 是否遵循最佳實踐
3. **測試**: 是否有足夠的測試覆蓋
4. **文件**: 是否更新了相關文件
5. **效能**: 是否有效能問題
6. **安全性**: 是否有安全隱患

### 審查回饋

- 建設性地提供回饋
- 解釋為什麼需要變更
- 提供具體的改進建議
- 認可好的實作

## 發布流程

### 版本發布

1. 更新 `CHANGELOG.md`
2. 更新版本號
3. 建立 Git tag
4. 建立 Release Notes
5. 部署到生產環境

### 版本號規則

遵循 [語義化版本](https://semver.org/lang/zh-TW/):

- `主版本.次版本.修訂版本`
- 例如: `1.2.3`

## 獲取幫助

需要幫助？

- 📧 發送郵件: dev@example.com
- 💬 加入討論群組
- 📚 查看文件
- 🐛 提交 Issue

## 致謝

感謝所有貢獻者的付出！

---

**維護者**: 開發團隊  
**最後更新**: 2024-01-03
