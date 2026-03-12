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

  // Load user info
  const loadUser = () => {
    const storedUser = storage.getUser();
    const storedToken = storage.getToken();
    if (storedUser && storedToken) {
      user.value = storedUser;
      token.value = storedToken;
    }
  };

  // Login
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
      return { success: false, message: 'Login failed' };
    } catch (err) {
      error.value = err.error?.message || 'Login failed';
      return { success: false, message: error.value };
    } finally {
      loading.value = false;
    }
  };

  // Register
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
      return { success: false, message: 'Registration failed' };
    } catch (err) {
      error.value = err.error?.message || 'Registration failed';
      return { success: false, message: error.value };
    } finally {
      loading.value = false;
    }
  };

  // Logout
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