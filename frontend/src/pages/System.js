import React, { useState, useEffect } from "react";
import api from "../services/api";

const System = () => {
  const [workersStatus, setWorkersStatus] = useState(null);
  const [redisInfo, setRedisInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [message, setMessage] = useState(null);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      // 使用 allSettled 確保即使一個請求失敗也不影響另一個
      // 增加 Worker 狀態請求的超時時間到 25 秒，因為 Celery inspect 操作較慢
      // 雖然後端已經優化，但考慮到網路延遲，保留較大的安全邊際
      const results = await Promise.allSettled([
        api.get("/api/system/workers/status", { timeout: 25000 }),
        api.get("/api/system/redis/info", { timeout: 5000 }),
      ]);

      // 處理 workers status
      if (results[0].status === "fulfilled") {
        setWorkersStatus(results[0].value.data);
      } else {
        console.error("載入 Worker 狀態失敗:", results[0].reason);
        setWorkersStatus({ error: "無法載入 Worker 狀態" });
      }

      // 處理 redis info
      if (results[1].status === "fulfilled") {
        setRedisInfo(results[1].value.data);
      } else {
        console.error("載入 Redis 資訊失敗:", results[1].reason);
        setRedisInfo({ error: "無法載入 Redis 資訊" });
      }
    } catch (err) {
      console.error("載入系統狀態失敗:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    try {
      setRefreshing(true);
      await fetchStatus();
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    // 移除自動輪詢，改為手動刷新
  }, []);

  const showMessage = (msg, type = "success") => {
    setMessage({ text: msg, type });
    setTimeout(() => setMessage(null), 3000);
  };

  const handlePurgeQueue = async () => {
    if (!window.confirm("確定要清理任務隊列嗎？所有等待中的任務將被刪除。"))
      return;

    try {
      const res = await api.post("/api/system/queue/purge");
      showMessage(res.data.detail);
      fetchStatus();
    } catch (err) {
      showMessage(
        "清理隊列失敗: " + (err.response?.data?.detail || err.message),
        "error"
      );
    }
  };

  const handleFlushRedis = async () => {
    if (
      !window.confirm(
        "⚠️ 警告：這將清除所有 Redis 數據，包括任務隊列和速率限制！確定要繼續嗎？"
      )
    )
      return;

    try {
      const res = await api.post("/api/system/redis/flush");
      showMessage(res.data.message);
      fetchStatus();
    } catch (err) {
      showMessage(
        "清理 Redis 失敗: " + (err.response?.data?.detail || err.message),
        "error"
      );
    }
  };

  const handleRevokeTask = async (taskId, terminate = false) => {
    if (!window.confirm(`確定要${terminate ? "強制終止" : "撤銷"}這個任務嗎？`))
      return;

    try {
      const res = await api.post(
        `/api/system/tasks/${taskId}/revoke?terminate=${terminate}`
      );
      showMessage(res.data.message);
      fetchStatus();
    } catch (err) {
      showMessage(
        "撤銷任務失敗: " + (err.response?.data?.detail || err.message),
        "error"
      );
    }
  };

  const getActiveTasks = () => {
    if (!workersStatus?.active_tasks) return [];

    const tasks = [];
    Object.entries(workersStatus.active_tasks).forEach(
      ([worker, workerTasks]) => {
        workerTasks.forEach((task) => {
          tasks.push({ ...task, worker });
        });
      }
    );
    return tasks;
  };

  return (
    <div className="px-4 sm:px-0">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">系統管理</h2>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          title="手動刷新系統狀態"
        >
          <svg
            className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          {refreshing ? "刷新中..." : "刷新"}
        </button>
      </div>

      {message && (
        <div
          className={`mb-4 px-4 py-3 rounded ${
            message.type === "error"
              ? "bg-red-50 border border-red-200 text-red-700"
              : "bg-green-50 border border-green-200 text-green-700"
          }`}
        >
          {message.text}
        </div>
      )}

      {/* 快速操作 */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">快速操作</h3>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={handlePurgeQueue}
            className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-md"
          >
            🗑️ 清理任務隊列
          </button>
          <button
            onClick={handleFlushRedis}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md"
          >
            ⚠️ 清理 Redis
          </button>
        </div>
      </div>

      {/* Worker 狀態 */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Worker 狀態
          {workersStatus && (
            <span className="ml-2 text-sm font-normal text-gray-600">
              ({workersStatus.total_active} 個活動任務)
            </span>
          )}
        </h3>

        {loading ? (
          <div className="text-center py-4">
            <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900"></div>
          </div>
        ) : (
          <div className="space-y-4">
            {getActiveTasks().length === 0 ? (
              <p className="text-gray-500 text-center py-4">
                沒有正在運行的任務
              </p>
            ) : (
              getActiveTasks().map((task, idx) => (
                <div
                  key={idx}
                  className="border border-gray-200 rounded-lg p-4"
                >
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">
                        {task.name}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">
                        Worker: {task.worker}
                      </div>
                      <div className="text-sm text-gray-600">
                        Task ID:{" "}
                        <code className="bg-gray-100 px-1 rounded">
                          {task.id}
                        </code>
                      </div>
                      {task.args && task.args.length > 0 && (
                        <div className="text-sm text-gray-600 mt-1">
                          參數: {task.args.slice(0, 2).join(", ")}
                          {task.args.length > 2 && "..."}
                        </div>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleRevokeTask(task.id, false)}
                        className="px-3 py-1 text-sm bg-yellow-100 hover:bg-yellow-200 text-yellow-800 rounded"
                      >
                        撤銷
                      </button>
                      <button
                        onClick={() => handleRevokeTask(task.id, true)}
                        className="px-3 py-1 text-sm bg-red-100 hover:bg-red-200 text-red-800 rounded"
                      >
                        強制終止
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Redis 狀態 */}
      {redisInfo && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Redis 狀態</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 p-4 rounded">
              <div className="text-sm text-gray-600">連接數</div>
              <div className="text-2xl font-bold text-gray-900">
                {redisInfo.connected_clients}
              </div>
            </div>
            <div className="bg-gray-50 p-4 rounded">
              <div className="text-sm text-gray-600">記憶體使用</div>
              <div className="text-2xl font-bold text-gray-900">
                {redisInfo.used_memory_human}
              </div>
            </div>
            <div className="bg-gray-50 p-4 rounded">
              <div className="text-sm text-gray-600">處理命令數</div>
              <div className="text-2xl font-bold text-gray-900">
                {redisInfo.total_commands_processed?.toLocaleString()}
              </div>
            </div>
            <div className="bg-gray-50 p-4 rounded">
              <div className="text-sm text-gray-600">運行時間</div>
              <div className="text-2xl font-bold text-gray-900">
                {Math.floor(redisInfo.uptime_in_seconds / 3600)}h
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default System;
