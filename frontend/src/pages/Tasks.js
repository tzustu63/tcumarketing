import React, { useState, useEffect } from 'react';
import { taskService } from '../services/taskService';
import TaskForm from '../components/TaskForm';
import TaskList from '../components/TaskList';

const Tasks = () => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      const data = await taskService.getTasks();
      // API returns { total, skip, limit, tasks } so we need to extract tasks array
      setTasks(Array.isArray(data) ? data : (data.tasks || []));
      setError(null);
    } catch (err) {
      setError('無法載入任務列表');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    try {
      setRefreshing(true);
      await fetchTasks();
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchTasks();
    // 移除自動輪詢，改為手動刷新
  }, []);

  const handleCreateTask = async (taskData) => {
    try {
      await taskService.createTask(taskData);
      setShowForm(false);
      fetchTasks();
    } catch (err) {
      console.error('建立任務失敗:', err);
      throw err;
    }
  };

  const handleDeleteTask = async (taskId) => {
    if (!window.confirm('確定要刪除此任務嗎？')) return;
    
    try {
      await taskService.deleteTask(taskId);
      fetchTasks();
    } catch (err) {
      console.error('刪除任務失敗:', err);
    }
  };

  return (
    <div className="px-4 sm:px-0">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">任務管理</h2>
        <div className="flex gap-2">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            title="手動刷新任務列表"
          >
            <svg 
              className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} 
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
            {refreshing ? '刷新中...' : '刷新'}
          </button>
          <button
            onClick={() => setShowForm(!showForm)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md"
          >
            {showForm ? '取消' : '建立新任務'}
          </button>
        </div>
      </div>

      {showForm && (
        <div className="mb-6">
          <TaskForm onSubmit={handleCreateTask} onCancel={() => setShowForm(false)} />
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {loading && tasks.length === 0 ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
          <p className="mt-2 text-gray-600">載入中...</p>
        </div>
      ) : (
        <TaskList
          tasks={tasks}
          onDelete={handleDeleteTask}
        />
      )}
    </div>
  );
};

export default Tasks;
