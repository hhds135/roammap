# RoamMap

RoamMap is a location-centric social media application enabling urban exploration through geotagged content sharing. Unlike conventional social media platforms where location serves as ancillary metadata, RoamMap implements a geography-primary design paradigm where geographic context drives content discovery and social connectivity. Users can create "corners"—geographic points annotated with multimedia posts—and discover new locations through friends, family, and intelligent recommendations.

## Project Highlights

RoamMap differentiates itself from existing platforms through:

- **Map-First Interface**: Cartographic interfaces constitute the primary interaction modality, not a secondary feature
- **User-Defined Locations**: Users can designate corners at arbitrary coordinates, beyond pre-established commercial venues
- **Hybrid Discovery Architecture**: Multi-dimensional content discovery combining geographic proximity, categorical filtering, social relationships, and behavioral analysis
- **Asymmetric Social Model**: One-way follow relationships enabling content discovery without requiring reciprocal acceptance
- **Intelligent Recommendations**: Multi-dimensional algorithm synthesizing four scoring dimensions for personalized content discovery

**Comparison with Existing Platforms:**

| Feature | RoamMap | Google Maps | Instagram | Foursquare | Yelp |
|---------|---------|-------------|-----------|------------|------|
| **Primary Focus** | Location-centric social | Navigation | Photo sharing | Venue discovery | Business reviews |
| **User-defined Locations** | ✓ (arbitrary coordinates) | ✗ (businesses only) | ✗ (existing places) | ✗ (venues only) | ✗ (businesses only) |
| **Map-First Interface** | ✓ | ✓ | ✗ | ✗ | ✗ |
| **Social Following** | ✓ (one-way) | ✗ | ✓ | ✗ | ✗ |
| **Route Planning** | ✓ (waypoint) | ✓ (full navigation) | ✗ | ✗ | ✗ |
| **Recommendations** | ✓ (multi-dimensional) | ✓ (business) | ✓ (algorithmic) | ✓ (venue) | ✓ (business) |

## Features

- **User Management**: Register, authenticate, and manage user profiles with JWT-based stateless authentication
- **Corner Creation**: Create and manage geographic locations with custom visibility (public, private, followers-only)
- **Social Features**: One-way follow relationships, like, comment, save (favorites), and share corners
- **Content Interaction**: Multimedia posts with images, privacy controls, and engagement metrics
- **Geographic Discovery**: Proximity-based search, nearby content identification, and route visualization
- **Route Planning**: Waypoint-based itinerary planning with OSRM-powered route computation
- **Intelligent Recommendations**: Multi-dimensional recommendation algorithm (geography 40%, interests 30%, social 20%, behavior 10%)
- **Interactive Map**: Real-time map visualization using Leaflet with OpenStreetMap tiles

## Development History

RoamMap was developed across three Agile iterations with User Acceptance Testing validation:

### Sprint 1: MVP Foundation
- Established basic corner designation capability with Leaflet click events
- Implemented bidirectional friend system (later replaced with one-way follows)
- JSON file-based storage for rapid development
- JWT authentication with 1-day token expiration
- Five privacy levels: public, private, friends-only, specific-friends, exclude-friends

### Sprint 2: Social & Content Expansion
- Migrated to MongoDB for production-grade data persistence
- Replaced bidirectional friend system with one-way follow model
- Streamlined privacy controls to three levels: public, private, followers-only
- Implemented chronological feed with pagination
- Added categorical filtering and geospatial search capabilities
- Profile management with interest tags and customization

### Sprint 3: Advanced Features
- Proximate content discovery using browser Geolocation API
- Route visualization with waypoint-based itinerary planning
- View history tracking for behavioral analysis
- Multi-dimensional recommendation algorithm with caching
- Notification system for social events
- Hot corners ranking and trending views

## Recommendation Algorithm

The recommendation system calculates scores synthesizing four dimensions:

1. **Geographic Proximity (40%)**: Haversine distance calculation
   - < 1km: 100 points
   - 1-5km: 80 points
   - 5-10km: 60 points
   - 10-20km: 40 points
   - > 20km: 20 points

2. **Interest Matching (30%)**: Set intersection of user tags and post tags
   - Full match: 100 points
   - Partial: proportional score
   - No match: 20 points

3. **Social Relationships (20%)**: Follow status check
   - Own post: 100 points
   - Mutual: 90 points
   - Following: 80 points
   - No relation: 40 points

4. **Behavioral History (10%)**: Past interactions
   - Liked: +30 points
   - Favorited: +30 points
   - Viewed: +20 points
   - View > 10s: +10 points
   - Base: 10 points

**Total Score**: 0.4×geo + 0.3×interest + 0.2×social + 0.1×behavior

Results are cached with 5-minute TTL for performance optimization.

## Architecture

The application follows a classical three-tier architectural pattern:

### Backend (Flask API)
- Python 3.12+ with Flask framework
- MongoDB with geospatial indexing (2dsphere) and TTL indexes
- JWT (JSON Web Token) for stateless authentication
- RESTful API with 15 route modules
- Comprehensive test suite with pytest and pytest-cov

### Frontend (Vue 3)
- Vue 3 with Composition API
- Vue Router for client-side navigation
- Axios for API communication
- Leaflet with OpenStreetMap tiles for interactive maps
- @mapbox/polyline for OSRM route decoding
- Vite for fast development and optimized builds

### External Services
- **OpenStreetMap**: Cartographic tiles with open licensing
- **OSRM (Open Source Routing Machine)**: Route computation for waypoint-based itineraries
- **Browser Geolocation API**: Proximate content discovery

## Prerequisites

- **Backend**: Python 3.12 or higher
- **Frontend**: Node.js 16+ and npm
- **Database**: MongoDB (configured in `config.py`)
- **Environment Variables** (optional):
  - `SECRET_KEY`: Flask secret key
  - `MONGODB_URI`: MongoDB connection string
  - `MONGODB_DB_NAME`: Database name

## Installation

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements-test.txt
   ```

3. Configure MongoDB connection in `config.py` or set environment variables

4. Run the application:
   ```bash
   python app.py
   ```

5. The backend API will be available at `http://localhost:5200`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```

4. The frontend application will be available at `http://localhost:5173`

## Testing

### Backend Tests

Run the backend test suite:

```bash
cd backend
pytest -v
```

For coverage report:

```bash
pytest --cov=. --cov-report=html
```

## API Documentation

The backend provides RESTful API endpoints for:

- **Authentication**: Register, login, token refresh
- **Users**: Profile management, user search
- **Corners**: Create, read, update, delete corners with geospatial queries
- **Posts**: Create and manage posts with route and privacy controls
- **Comments**: Add and retrieve comments
- **Likes**: Like/unlike content
- **Favorites**: Save corners to favorites
- **Follows**: Manage one-way follow relationships
- **Recommendations**: Get personalized corner recommendations with multi-dimensional scoring
- **Notifications**: User notification management
- **Media**: Image and video uploads via GridFS
- **View History**: Track user browsing behavior for recommendation analysis

## Project Structure

```
project/
├── backend/
│   ├── app.py              # Main application entry point
│   ├── config.py           # Application configuration
│   ├── models.py           # Data models
│   ├── utils.py            # Utility functions
│   ├── routes/             # API route handlers (15 modules)
│   ├── services/           # Business logic (recommendation)
│   ├── storage/            # Database storage layer (12 stores)
│   └── tests/              # Backend test suite
├── frontend/
│   ├── index.html          # Entry HTML file
│   ├── vite.config.js      # Vite configuration
│   └── src/
│       ├── main.js         # Application entry point
│       ├── App.vue         # Root component
│       ├── api/            # API client modules
│       ├── components/     # Vue components
│       ├── composables/    # Vue composables
│       ├── router/         # Vue Router configuration
│       ├── utils/          # Utility functions
│       └── views/          # Page views
└── docs/                   # Project documentation
```

## Configuration

Key configuration options in `backend/config.py`:

- `UPLOAD_FOLDER`: Directory for media uploads
- `MAX_CONTENT_LENGTH`: Maximum file upload size (16MB default)
- `PRESET_TAGS`: Available interest tags (Food, Travel, Sports, Art, Photography, Reading, Music, Movies, Pets, Nature)
- `RECOMMENDATION_WEIGHTS`: Algorithm weights (geo: 0.4, interest: 0.3, social: 0.2, behavior: 0.1)
- `DEFAULT_SEARCH_RADIUS_METERS`: Default geographic search radius (10km)
- `MAX_SEARCH_RADIUS_METERS`: Maximum search radius (100km)
- `RECOMMENDATION_CACHE_TTL`: Cache TTL in seconds (300)
- `VIEW_HISTORY_TTL_DAYS`: View history retention period (30 days)