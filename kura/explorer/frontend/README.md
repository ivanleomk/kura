# Kura Explorer Frontend

React + TypeScript frontend for the Kura Explorer application.

## Overview

The frontend provides an interactive web interface for exploring Kura conversation clusters. Built with modern React, TypeScript, and Vite, it offers real-time visualization and search capabilities.

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **shadcn/ui** for UI components
- **Recharts** for data visualization
- **React Router** for navigation
- **Tanstack Query** for data fetching

## Project Structure

```
frontend/
├── src/
│   ├── pages/              # Main page components
│   │   ├── HomePage.tsx
│   │   ├── ClustersPage.tsx
│   │   ├── ClusterDetailPage.tsx
│   │   ├── ConversationsPage.tsx
│   │   └── ConversationDetailPage.tsx
│   ├── components/         # Reusable components
│   │   ├── ClusterMap.tsx
│   │   ├── ClusterTree.tsx
│   │   ├── ConversationList.tsx
│   │   ├── Layout.tsx
│   │   └── ui/            # shadcn/ui components
│   ├── lib/               # Utilities and API client
│   │   ├── api.ts
│   │   └── utils.ts
│   └── main.tsx           # Application entry point
├── public/                # Static assets
├── index.html            # HTML template
└── vite.config.ts        # Vite configuration
```

## Development

### Prerequisites

- Node.js 18+ and npm
- Backend API running on port 8001

### Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linting
npm run lint
```

### Environment Variables

Create a `.env` file:

```bash
VITE_API_URL=http://localhost:8001  # Backend API URL
```

## Key Components

### Pages

- **HomePage**: Dashboard with overview statistics and recent activity
- **ClustersPage**: Interactive cluster map and tree visualization
- **ClusterDetailPage**: Detailed view of a single cluster with conversations
- **ConversationsPage**: Searchable list of all conversations
- **ConversationDetailPage**: Full conversation view with metadata

### Core Components

- **ClusterMap**: 2D visualization using UMAP coordinates
- **ClusterTree**: Hierarchical tree view of cluster relationships
- **ConversationList**: Paginated list with search and filters
- **Layout**: App shell with navigation and routing

### API Integration

The `lib/api.ts` module provides typed API client functions:

```typescript
// Fetch clusters
const clusters = await api.getClusters({ 
  skip: 0, 
  limit: 50 
});

// Search conversations
const results = await api.searchConversations({
  query: "help with code",
  limit: 20
});

// Get cluster details
const cluster = await api.getCluster(clusterId);
```

## Styling

The project uses Tailwind CSS with a custom configuration:

- Custom color palette matching Kura branding
- Responsive design utilities
- Dark mode support (planned)
- Component-specific styles in CSS modules

## State Management

- **React Router** for navigation state
- **Tanstack Query** for server state
- **React Context** for UI state (filters, preferences)
- **Local Storage** for user settings

## Performance Optimizations

- **Code Splitting**: Routes are lazy-loaded
- **Memoization**: Heavy computations are cached
- **Virtual Scrolling**: Large lists use windowing
- **Debounced Search**: API calls are throttled
- **Image Optimization**: SVGs and compressed PNGs

## Building for Production

```bash
# Build the application
npm run build

# Output is in dist/ directory
ls -la dist/

# Test the production build
npm run preview
```

### Production Considerations

1. **API URL**: Update `VITE_API_URL` for production backend
2. **Base Path**: Configure if not serving from root
3. **Caching**: Add cache headers for static assets
4. **Compression**: Enable gzip/brotli on server
5. **HTTPS**: Ensure secure connections

## Docker Deployment

The frontend includes a multi-stage Dockerfile:

```dockerfile
# Build stage
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

## Testing

```bash
# Run unit tests (coming soon)
npm run test

# Run E2E tests (coming soon)
npm run test:e2e
```

## Troubleshooting

### Common Issues

1. **"Cannot connect to API"**: Ensure backend is running and VITE_API_URL is correct
2. **Blank page**: Check browser console for errors
3. **Slow loading**: Enable production build optimizations
4. **CORS errors**: Backend must allow frontend origin

### Debug Mode

Enable debug logging:

```typescript
// In main.tsx
if (import.meta.env.DEV) {
  window.DEBUG = true;
}
```

## Contributing

### Code Style

- Follow ESLint rules
- Use TypeScript strict mode
- Prefer functional components
- Use custom hooks for logic
- Keep components small and focused

### Adding Features

1. Create new component in appropriate directory
2. Add route if needed in App.tsx
3. Update API client if new endpoints
4. Add to navigation in Layout.tsx
5. Update types as needed

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/new-component

# Make changes and commit
git add .
git commit -m "feat: add new component"

# Push and create PR
git push origin feature/new-component
```
