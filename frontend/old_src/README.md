# Old Frontend (Archived)

## Archive Date

2026-03-06

## Reason for Archiving

The old frontend architecture no longer aligned with the goals of the new product in several important ways:

### 1. Changes in Interface Structure
- **Old frontend**: A single-page map application, with the map as the core interaction
- **New product**: A dual-tab structure (feed interface + map interface), with the feed interface becoming the main entry point

### 2. Changes in API Dependencies
- **Old frontend**: Used the deprecated bidirectional friendship APIs (`/api/friends/*`)
- **New product**: Uses one-way follow system APIs (`/api/follows/*`, `/api/feed/*`)

### 3. Changes in the Data Model
- **Old frontend**: Expected Corners to contain post data, with posts treated as sub-resources of Corners
- **New product**: Corners and Posts are fully separated; posts can reference multiple Corners and support route-related functionality

### 4. Changes in the Interaction Model
- **Old frontend**: Form-based interactions for creating, editing, and deleting content
- **New product**: Feed-style scrolling interactions (infinite scroll, immersive browsing) combined with map-based exploration

### 5. Changes in Functional Requirements
- **Old frontend**: Basic location marking and sharing
- **New product**:
  - Feed-based content discovery (similar to TikTok)
  - Intelligent recommendation algorithms (geographic, interest-based, social, and behavioural)
  - Route planning and sharing
  - Follow system and social interaction
  - View history tracking

## Tech Stack

- **Framework**: Vue 3
- **Map**: Leaflet (OpenStreetMap)
- **HTTP Client**: Axios
- **Build Tool**: Vite
- **Styling**: CSS

## Directory Structure

```text
old_src/
├── App.vue              # Main application component
├── main.js              # Application entry point
└── views/               # Page components
    ├── Friends.vue      # Friends page (deprecated)
    ├── Home.vue         # Home page
    ├── Login.vue        # Login page
    ├── Map.vue          # Map page
    ├── Register.vue     # Register page
    └── Share.vue        # Share page
```
    

Reason for Retaining the Code

This code is retained in the old_src/ directory for the following reasons:

Reference purposes: To refer to certain implementation details or UI components

Rollback purposes: To preserve the option of returning to the previous version if necessary (not recommended, but retained as an option)

Component reuse: To extract potentially reusable components for the new frontend

Learning purposes: To serve as an example of the previous architecture

Deprecated APIs

The following APIs were used by the old frontend but have been replaced in the new product:

Old API	New API	Description
POST /api/friends/request	POST /api/follows/<user_id>	Bidirectional friendship → one-way follow
PUT /api/friends/request/<id>	-	Friend request workflow is no longer needed
GET /api/friends	GET /api/users/<id>/following	Friends list → following list
DELETE /api/friends/<id>	DELETE /api/follows/<user_id>	Remove friend → unfollow
Migration Guide

If migration from the old frontend to the new frontend is required:

1. Authentication and Authorisation

Keep the JWT token authentication method

Update API endpoint paths

2. Data Fetching

Posts: Fetch from /api/posts using the new Feed API

Locations: Fetch from /api/corners using the new aggregation and search APIs

Users: Fetch from /api/users using the new follow APIs

3. Component Refactoring

Remove friend-related components

Add feed-style content components

Add route display components

Update map components to support route rendering

4. State Management

Consider using Pinia to manage complex state

Add state management for follow relationships

Add state management for recommendations

Notes

⚠️ This code is no longer maintained and is not recommended for active use.

Many of the backend APIs it depends on have been deprecated or modified

Its data model is incompatible with the new backend

Its UI/UX design no longer matches the direction of the new product

There may be security and performance issues

Recommendations for the New Frontend

The new frontend should adopt the following architecture:

1. Technology Choices

Framework: Vue 3 + TypeScript

State Management: Pinia

Routing: Vue Router

UI Component Library: Element Plus

Map: Leaflet

HTTP Client: Axios

Build Tool: Vite

2. Core Features

Feed interface: Infinite scrolling, video playback, lazy loading of images

Map interface: Route drawing, location markers, nearby search

Social features: Follow, like, comment, and favourite

Recommendation system: Personalised content feed

3. Performance Optimisation

Virtual scrolling

Lazy loading of images and videos

Request caching and deduplication

Component lazy loading

Last updated: 2026-03-06