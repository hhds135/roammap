import { ref, onMounted } from 'vue';
import { feedApi } from '../api/feed';
import { recommendationsApi } from '../api/recommendations';

// Get user location
async function getUserLocation() {
  return new Promise((resolve) => {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            lat: position.coords.latitude,
            lng: position.coords.longitude
          });
        },
        () => {
          // Default location: Birmingham
          resolve({ lat: 52.4862, lng: -1.8904 });
        }
      );
   } else {
  // Default location: Birmingham
  resolve({ lat: 52.4862, lng: -1.8904 });
   }
  });
}

export function useFeed(feedType = 'following') {
  const posts = ref([]);
  const loading = ref(false);
  const error = ref(null);
  const hasMore = ref(true);
  const skip = ref(0);
  const limit = 20;
  const userLocation = ref(null);

  const fetchPosts = async (reset = false) => {
    if (reset) {
      skip.value = 0;
      posts.value = [];
    }

    loading.value = true;
    error.value = null;

    try {
      let response;

      if (feedType === 'following') {
        // Following feed
        response = await feedApi.getFollowing({
          skip: skip.value,
          limit,
          include_own: true
        });
      } else if (feedType === 'recommendation') {
        // Recommendation feed
        if (!userLocation.value) {
          userLocation.value = await getUserLocation();
        }

        response = await recommendationsApi.getFeed({
          lat: userLocation.value.lat,
          lng: userLocation.value.lng,
          skip: skip.value,
          limit
        });
      } else {
        // Comprehensive feed
        if (!userLocation.value) {
          userLocation.value = await getUserLocation();
        }

        response = await recommendationsApi.getComprehensive({
          lat: userLocation.value.lat,
          lng: userLocation.value.lng,
          skip: skip.value,
          limit
        });
      }

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
      error.value = err.error?.message || 'Load failed';
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
    refresh,
    userLocation
  };
}