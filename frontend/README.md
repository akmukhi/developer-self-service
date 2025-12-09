# Developer Self-Service Portal - Frontend

React frontend application built with TypeScript, Vite, TailwindCSS, and Material-UI.

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Material-UI (MUI)** - Component library
- **TailwindCSS** - Utility-first CSS framework
- **React Router** - Routing
- **Axios** - HTTP client

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### Build

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/     # Reusable UI components
│   ├── pages/          # Page components
│   ├── services/       # API client services
│   ├── types/          # TypeScript type definitions
│   ├── App.tsx         # Main app component
│   ├── main.tsx        # Entry point
│   ├── theme.ts        # MUI theme configuration
│   └── index.css       # Global styles
├── public/             # Static assets
├── index.html          # HTML template
├── vite.config.ts      # Vite configuration
├── tailwind.config.js # TailwindCSS configuration
└── package.json        # Dependencies
```

## Features

- Modern React with TypeScript
- Material-UI components with custom theme
- TailwindCSS for utility styling
- React Router for navigation
- Axios for API calls
- Vite for fast development and builds

## Environment Variables

Create a `.env` file in the frontend directory:

```
VITE_API_BASE_URL=http://localhost:8000
```

## Development Proxy

The Vite dev server is configured to proxy `/api` requests to `http://localhost:8000` (the FastAPI backend).

