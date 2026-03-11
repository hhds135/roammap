import { ref, onMounted } from 'vue';
import { feedApi } from '../api/feed';

export function useFeed(feedType = 'following') {
  const posts = ref([]);
  const loading = ref(false);
  const error = ref(null);
  const hasMore = ref(true);
  const skip = ref(0);
  const limit = 20;

  const fetchPosts = async (reset = false) => {
    if (reset) {
      skip.value = 0;
      posts.value = [];
    }

    loading.value = true;
    error.value = null;

    try {
      const response = await feedApi.getFollowing({
        skip: skip.value,
        limit,
        include_own: true
      });

      if (response.success && response.data?.posts) {
        if (reset) {
          posts.value = response.data.posts;
        } else {
          posts.value = [...posts.value, ...response.data.posts];
        }
        skip.value += response.data.posts.length;
        hasMore.value = response.data.posts.length === limit;
      }
    } catch (err) {
      error.value = err.error?.message || '加载失败';
    } finally {
      loading.value = false;
    }
  };

  const loadMore = () => {
    if (!loading.value && hasMore.value) {
      fetchPosts(false);
    }
  };

  const refresh = () => {
    fetchPosts(true);
  };

  onMounted(() => {
    fetchPosts(true);
  });

  return {
    posts,
    loading,
    error,
    hasMore,
    loadMore,
    refresh
  };
}