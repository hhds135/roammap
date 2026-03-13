<template>
  <div class="notifications-view">
    <div class="notifications-container">
      <div class="notifications-header">
        <h1>Notifications</h1>
        <div class="header-actions">
          <span v-if="unreadCount > 0" class="unread-badge">{{ unreadCount }} unread</span>
          <button 
            v-if="hasNotifications" 
            @click="markAllAsRead" 
            class="mark-all-btn"
          >
            Mark All as Read
          </button>
        </div>
      </div>

      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <p>Loading...</p>
      </div>

      <div v-else-if="notifications.length === 0" class="empty-state">
        <div class="empty-icon">🔔</div>
        <p>No notifications</p>
        <p class="empty-hint">You will receive notifications when someone likes, comments, or follows you</p>
      </div>

      <div v-else class="notifications-list">
        <div
          v-for="notification in notifications"
          :key="notification._id"
          :class="['notification-item', { unread: !notification.read }]"
          @click="handleNotificationClick(notification)"
        >
          <div class="notification-icon">
            <span v-if="notification.type === 'like'">❤️</span>
            <span v-else-if="notification.type === 'comment'">💬</span>
            <span v-else-if="notification.type === 'follow'">👥</span>
            <span v-else>🔔</span>
          </div>
          <div class="notification-content">
            <p class="notification-text">{{ notification.content }}</p>
            <p class="notification-time">{{ formatTime(notification.created_at) }}</p>
          </div>
          <div class="notification-actions">
            <button 
              v-if="!notification.read" 
              @click.stop="markAsRead(notification._id)"
              class="read-btn"
            >
              Mark as Read
            </button>
            <button 
              @click.stop="deleteNotification(notification._id)"
              class="delete-btn"
            >
              Delete
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { notificationsApi } from '../api/notifications';
import { formatRelativeTime } from '../utils/format';

const router = useRouter();

const notifications = ref([]);
const loading = ref(false);
const unreadCount = ref(0);

const hasNotifications = computed(() => notifications.value.length > 0);

const formatTime = (timestamp) => {
  return formatRelativeTime(timestamp);
};

const loadNotifications = async () => {
  loading.value = true;
  try {
    const response = await notificationsApi.getAll({ limit: 50 });
    if (response.success && response.data) {
      notifications.value = response.data.notifications || [];
    }
  } catch (error) {
    console.error('Failed to load notifications:', error);
  } finally {
    loading.value = false;
  }
};

const loadUnreadCount = async () => {
  try {
    const response = await notificationsApi.getUnreadCount();
    if (response.success && response.data) {
      unreadCount.value = response.data.unread_count || 0;
    }
  } catch (error) {
    console.error('Failed to load unread count:', error);
  }
};

const markAsRead = async (notificationId) => {
  try {
    const response = await notificationsApi.markAsRead(notificationId);
    if (response.success) {
      const notification = notifications.value.find(n => n._id === notificationId);
      if (notification) {
        notification.read = true;
        unreadCount.value = Math.max(0, unreadCount.value - 1);
      }
    }
  } catch (error) {
    console.error('Failed to mark notification as read:', error);
  }
};

const markAllAsRead = async () => {
  try {
    const response = await notificationsApi.markAllAsRead();
    if (response.success) {
      notifications.value.forEach(n => n.read = true);
      unreadCount.value = 0;
    }
  } catch (error) {
    console.error('Failed to mark all notifications as read:', error);
  }
};

const deleteNotification = async (notificationId) => {
  if (!confirm('Are you sure you want to delete this notification?')) {
    return;
  }
  
  try {
    const response = await notificationsApi.delete(notificationId);
    if (response.success) {
      notifications.value = notifications.value.filter(n => n._id !== notificationId);
      const notification = notifications.value.find(n => n._id === notificationId);
      if (notification && !notification.read) {
        unreadCount.value = Math.max(0, unreadCount.value - 1);
      }
    }
  } catch (error) {
    console.error('Failed to delete notification:', error);
  }
};

const handleNotificationClick = (notification) => {
  // Mark as read if unread
  if (!notification.read) {
    markAsRead(notification._id);
  }

  // Navigate based on notification type
  if (notification.post_id) {
    // Navigate to feed and scroll to post (simplified)
    router.push('/feed');
  } else if (notification.actor) {
    // Navigate to actor's profile
    router.push(`/profile/${notification.actor.user_id}`);
  }
};

onMounted(() => {
  loadNotifications();
  loadUnreadCount();
});
</script>

<style scoped>
.notifications-view {
  height: 100%;
  background: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}

.notifications-container {
  max-width: 800px;
  margin: 0 auto;
}

.notifications-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.notifications-header h1 {
  margin: 0;
  font-size: 24px;
  color: #333;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.unread-badge {
  padding: 6px 14px;
  background: linear-gradient(135deg, #ff6b6b 0%, #ff8e8e 100%);
  color: white;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
}

.mark-all-btn {
  padding: 8px 16px;
  background: #409eff;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.mark-all-btn:hover {
  background: #66b1ff;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #409eff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading p {
  color: #666;
  margin: 0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.empty-state p {
  margin: 4px 0;
  color: #666;
}

.empty-hint {
  font-size: 14px;
  color: #999;
}

.notifications-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.notification-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  cursor: pointer;
  transition: all 0.3s;
}

.notification-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.notification-item.unread {
  background: linear-gradient(135deg, #f0f4ff 0%, #ffffff 100%);
  border-left: 4px solid #409eff;
}

.notification-icon {
  width: 48px;
  height: 48px;
  min-width: 48px;
  border-radius: 50%;
  background: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-text {
  margin: 0 0 4px 0;
  font-size: 15px;
  color: #333;
  line-height: 1.5;
}

.notification-time {
  margin: 0;
  font-size: 13px;
  color: #999;
}

.notification-actions {
  display: flex;
  gap: 8px;
}

.read-btn,
.delete-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s;
}

.read-btn {
  background: #409eff;
  color: white;
}

.read-btn:hover {
  background: #66b1ff;
}

.delete-btn {
  background: #f5f5f5;
  color: #666;
}

.delete-btn:hover {
  background: #fee;
  color: #f56c6c;
}
</style>