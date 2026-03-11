import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { authApi } from '../api/auth';
import { storage } from '../utils/storage';

export function useAuth() {
  const router = useRouter();
  const user = ref(storage.getUser());
  const token = ref(storage.getToken());
  const loading = ref(false);
  const error = ref(null);

  const isAuthenticated = computed(() => !!token.value);

  // 加载用户信息
  const loadUser = () => {
    const storedUser = storage.getUser();
    const storedToken = storage.getToken();
    if (storedUser && storedToken) {
      user.value = storedUser;
      token.value = storedToken;
    }
  };

  // 登录
  const login = async (username, password) => {
    loading.value = true;
    error.value = null;

    try {
      const response = await authApi.login(username, password);
      if (response.user && response.token) {
        storage.setUser(response.user);
        storage.setToken(response.token);
        user.value = response.user;
        token.value = response.token;
        return { success: true };
      }
      return { success: false, message: '登录失败' };
    } catch (err) {
      error.value = err.error?.message || '登录失败';
      return { success: false, message: error.value };
    } finally {
      loading.value = false;
    }
  };

  // 注册
  const register = async (username, password) => {
    loading.value = true;
    error.value = null;

    try {
      const response = await authApi.register(username, password);
      if (response.user && response.token) {
        storage.setUser(response.user);
        storage.setToken(response.token);
        user.value = response.user;
        token.value = response.token;
        return { success: true };
      }
      return { success: false, message: '注册失败' };
    } catch (err) {
      error.value = err.error?.message || '注册失败';
      return { success: false, message: error.value };
    } finally {
      loading.value = false;
    }
  };

  // 登出
  const logout = () => {
    authApi.logout();
    user.value = null;
    token.value = null;
    router.push('/login');
  };

  return {
    user,
    token,
    loading,
    error,
    isAuthenticated,
    loadUser,
    login,
    register,
    logout
  };
}