# Phase 5: Frontend Web App - Step-by-Step Breakdown

## Overview
Build React/Vite web application with live machine status tiles, branch/category selectors, 24-hour heatmaps, alert subscriptions, and geolocation integration.

## Prerequisites
- Phase 4 APIs and WebSocket endpoints operational
- Real-time data streaming from backend
- REST API endpoints tested and documented

---

## Step 1: React/Vite Project Setup
**Duration**: 25 minutes  
**Status**: ⏳ Pending

### 1.1 Initialize Vite Project
- [ ] Create React/Vite project in `/frontend` directory
```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install
```

### 1.2 Install Dependencies
- [ ] Install required packages:
```bash
npm install @types/react @types/react-dom
npm install axios socket.io-client
npm install tailwindcss postcss autoprefixer
npm install @heroicons/react date-fns
npm install recharts # for heatmaps and charts
```

### 1.3 Configure Development Environment
- [ ] Set up Tailwind CSS configuration
- [ ] Configure Vite for API proxy during development
- [ ] Set up environment variables for API endpoints
- [ ] Configure TypeScript strict mode

---

## Step 2: Application Structure and Routing
**Duration**: 30 minutes  
**Status**: ⏳ Pending

### 2.1 Project Structure Setup
- [ ] Create organized component structure:
```
src/
├── components/
│   ├── common/         # Shared components
│   ├── machine/        # Machine-related components  
│   ├── branch/         # Branch selection components
│   ├── chat/           # Chatbot interface
│   └── layout/         # Layout components
├── hooks/              # Custom React hooks
├── services/           # API and WebSocket services
├── types/              # TypeScript type definitions
├── utils/              # Utility functions
└── styles/             # CSS and styling
```

### 2.2 TypeScript Type Definitions
- [ ] **File**: `src/types/index.ts`
- [ ] Define Machine, Branch, Category interfaces
- [ ] Create API response types
- [ ] Add WebSocket message types
- [ ] Define alert and notification types

### 2.3 Basic Routing Setup
- [ ] Install React Router: `npm install react-router-dom`
- [ ] Set up main routes: Home, Branch Details, Settings
- [ ] Configure navigation components

---

## Step 3: API Service Layer
**Duration**: 35 minutes  
**Status**: ⏳ Pending

### 3.1 HTTP Client Setup
- [ ] **File**: `src/services/api.ts`
- [ ] Configure Axios with base URL and interceptors
- [ ] Implement error handling and retry logic
- [ ] Add request/response logging for development

### 3.2 API Service Methods
- [ ] **File**: `src/services/gymService.ts`
```typescript
export const gymService = {
  getBranches: () => Promise<Branch[]>,
  getMachines: (branchId: string, category: string) => Promise<Machine[]>,
  getMachineHistory: (machineId: string, range: string) => Promise<HistoryData>,
  createAlert: (machineId: string, config: AlertConfig) => Promise<Alert>,
  deleteAlert: (alertId: string) => Promise<void>
};
```

### 3.3 WebSocket Service
- [ ] **File**: `src/services/websocket.ts`
- [ ] Implement WebSocket connection management
- [ ] Handle connection lifecycle events
- [ ] Add message parsing and routing
- [ ] Implement reconnection logic

---

## Step 4: Live Machine Status Tiles
**Duration**: 40 minutes  
**Status**: ⏳ Pending

### 4.1 Machine Tile Component
- [ ] **File**: `src/components/machine/MachineTile.tsx`
- [ ] Display machine name, status, and last change time
- [ ] Show visual status indicators (free/occupied/offline)
- [ ] Include "notify when free" alert button
- [ ] Add responsive design for mobile/desktop

### 4.2 Machine Grid Layout
- [ ] **File**: `src/components/machine/MachineGrid.tsx`
- [ ] Grid layout for machine tiles
- [ ] Category-based filtering and grouping
- [ ] Real-time status updates via WebSocket
- [ ] Loading states and error handling

### 4.3 Real-Time Updates Integration
- [ ] Connect WebSocket service to machine components
- [ ] Update tile status when receiving WebSocket messages
- [ ] Add visual animations for status changes
- [ ] Implement optimistic updates for better UX

---

## Step 5: Branch and Category Selectors
**Duration**: 30 minutes  
**Status**: ⏳ Pending

### 5.1 Branch Selector Component
- [ ] **File**: `src/components/branch/BranchSelector.tsx`
- [ ] Dropdown/list for branch selection
- [ ] Show distance and ETA (when location available)
- [ ] Display aggregate free counts per branch
- [ ] Store selection in local state/URL

### 5.2 Category Filter Component
- [ ] **File**: `src/components/machine/CategoryFilter.tsx`
- [ ] Tab-based category selection (legs, chest, back)
- [ ] Show free/total counts per category
- [ ] Filter machine grid based on selection
- [ ] Persist filter state across sessions

### 5.3 Search and Filter Integration
- [ ] Global search for machines by name
- [ ] Combined filtering by branch + category
- [ ] Clear filters functionality
- [ ] URL state management for shareable links

---

## Step 6: 24-Hour Heatmap Component
**Duration**: 35 minutes  
**Status**: ⏳ Pending

### 6.1 Heatmap Visualization
- [ ] **File**: `src/components/machine/Heatmap.tsx`
- [ ] Use Recharts for heatmap rendering
- [ ] Display 24-hour occupancy data in 15-minute bins
- [ ] Color coding for occupancy levels
- [ ] Interactive hover tooltips with details

### 6.2 Heatmap Data Processing
- [ ] **File**: `src/utils/heatmapUtils.ts`
- [ ] Process API data into chart format
- [ ] Calculate occupancy percentages
- [ ] Handle missing data points gracefully
- [ ] Add time zone handling for Hong Kong

### 6.3 Mini-Heatmap for Tiles
- [ ] Compact heatmap version for machine tiles
- [ ] Show last 24 hours of activity
- [ ] Minimal visual design for space constraints
- [ ] Click to expand to full heatmap view

---

## Step 7: Alert Subscription Interface
**Duration**: 25 minutes  
**Status**: ⏳ Pending

### 7.1 Alert Button Component
- [ ] **File**: `src/components/machine/AlertButton.tsx`
- [ ] "Notify when free" toggle button
- [ ] Visual states: inactive, active, triggered
- [ ] Integration with alert API endpoints
- [ ] Confirmation modals and feedback

### 7.2 Alert Management Panel
- [ ] **File**: `src/components/alerts/AlertPanel.tsx`
- [ ] List active alerts with machine details
- [ ] Cancel/modify alert functionality
- [ ] Quiet hours configuration
- [ ] Alert history and statistics

### 7.3 Notification Display
- [ ] Toast notifications for alert triggers
- [ ] Browser notification integration (with permission)
- [ ] Sound alerts (optional, user configurable)
- [ ] Notification history and management

---

## Step 8: Geolocation Integration
**Duration**: 30 minutes  
**Status**: ⏳ Pending

### 8.1 Geolocation Hook
- [ ] **File**: `src/hooks/useGeolocation.ts`
- [ ] Request browser geolocation permission
- [ ] Handle permission granted/denied states
- [ ] Store location temporarily for session
- [ ] Provide fallback for manual location entry

### 8.2 Location-Based Features
- [ ] Calculate and display distances to branches
- [ ] Sort branches by proximity
- [ ] Show ETAs when location available
- [ ] Privacy notice and consent flow

### 8.3 Manual Location Entry
- [ ] Text input for address/location
- [ ] Basic geocoding for address to coordinates
- [ ] Location validation and error handling
- [ ] Save preferences for return visits

---

## Step 9: Forecast Chip Implementation
**Duration**: 20 minutes  
**Status**: ⏳ Pending

### 9.1 Forecast Chip Component
- [ ] **File**: `src/components/machine/ForecastChip.tsx`
- [ ] Small "likely free in 30m" indicator
- [ ] Color coding based on probability
- [ ] Tooltip with forecast explanation
- [ ] Integration with machine history API

### 9.2 Forecast Logic Integration
- [ ] Process weekly seasonality data
- [ ] Calculate probability thresholds
- [ ] Handle missing forecast data
- [ ] Update forecasts periodically

---

## Step 10: Responsive Design and Testing
**Duration**: 30 minutes  
**Status**: ⏳ Pending

### 10.1 Responsive Design
- [ ] Mobile-first design approach
- [ ] Tablet and desktop layouts
- [ ] Touch-friendly interface elements
- [ ] Optimized loading for mobile networks

### 10.2 Cross-Browser Testing
- [ ] Test on Chrome, Firefox, Safari, Edge
- [ ] Verify WebSocket functionality across browsers
- [ ] Test geolocation on different devices
- [ ] Validate responsive design breakpoints

### 10.3 Performance Optimization
- [ ] Code splitting and lazy loading
- [ ] Image optimization and caching
- [ ] Bundle size analysis and optimization
- [ ] WebSocket connection efficiency

### 10.4 Evidence Capture and Commit
```bash
git add .
git commit -m "feat: Phase 5 frontend web application

- React/Vite app with TypeScript and Tailwind CSS
- Live machine status tiles with real-time WebSocket updates
- Branch and category selectors with filtering
- 24-hour heatmap component with interactive visualization
- Alert subscription interface with notification management
- Geolocation integration with privacy consent flow
- Forecast chip showing 30-minute availability predictions
- Responsive design optimized for mobile and desktop

🤖 Generated with Amazon Q Developer
Co-Authored-By: Amazon Q Developer <noreply@aws.amazon.com>"
```

---

## Success Criteria
- [ ] Application loads and displays machine data correctly
- [ ] Real-time updates work via WebSocket connection
- [ ] Branch and category filtering functions properly
- [ ] Heatmaps display historical occupancy data
- [ ] Alert system allows subscription and notification
- [ ] Geolocation works with user permission
- [ ] Forecast chips show availability predictions
- [ ] Responsive design works across devices
- [ ] Performance targets met for mobile networks

## Estimated Total Time: 4 hours

## Next Phase
Phase 6: Agentic chatbot with tool-use implementation