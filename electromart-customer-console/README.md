# ElectroMart Frontend - React + Vite + MUI

## Standard Project Structure

This frontend follows the **standard React + Vite project structure**:

```
frontend/
├── public/                # Static assets (favicon, images, etc.)
├── src/                   # Source code
│   ├── components/        # React components
│   │   ├── ChatInterface.jsx
│   │   ├── MessageList.jsx
│   │   └── InputBox.jsx
│   ├── hooks/            # Custom React hooks
│   │   └── useSocket.js
│   ├── lib/              # Utility libraries
│   │   └── socket.js
│   ├── App.jsx           # Root application component
│   └── main.jsx          # Application entry point
├── index.html            # HTML template (Vite entry)
├── package.json          # Dependencies and scripts
├── vite.config.js        # Vite configuration
└── .env.example          # Environment variables template
```

## Technology Stack

- **React 18** - Modern UI library with hooks
- **Vite 5** - Fast build tool and dev server
- **Material-UI (MUI) v5** - Complete component library
- **Emotion** - CSS-in-JS styling (required by MUI)
- **Socket.IO Client** - Real-time communication with backend

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Set Up Environment Variables

```bash
cp .env.example .env
# Edit .env and set your backend URL (default: http://localhost:8000)
```

### 3. Run Development Server

```bash
npm run dev
```

The app will start at `http://localhost:3000`

## Available Scripts

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build
npm run lint         # Run ESLint (if configured)
```

## Project Structure Details

### `/public`
Static assets that are served directly without processing by Vite.
- Favicon
- Images
- Fonts
- Any files that don't need bundling

### `/src/components`
React components following Material-UI design patterns:
- **ChatInterface.jsx** - Main chat container with MUI AppBar
- **MessageList.jsx** - Message display with agent differentiation
- **InputBox.jsx** - Message input with MUI TextField

### `/src/hooks`
Custom React hooks for shared logic:
- **useSocket.js** - Socket.IO connection management

### `/src/lib`
Utility libraries and configurations:
- **socket.js** - Socket.IO client setup

### `/src/App.jsx`
Root component with MUI ThemeProvider and CssBaseline

### `/src/main.jsx`
Entry point that mounts the React app to the DOM

## Key Features

### Material-UI Integration
- Uses MUI's `sx` prop for styling
- Emotion CSS-in-JS engine
- Responsive design with MUI Grid and Box
- Material Icons for visual elements

### Real-time Communication
- Socket.IO for bidirectional communication
- Automatic reconnection handling
- Typing indicators
- Agent handoff notifications

### Agent Differentiation
Visual distinction for different agents:
- **Sales Agent** - Blue theme
- **Marketing Agent** - Purple theme
- **Support Agent** - Green theme
- **Logistics Agent** - Orange theme

## Environment Variables

Create a `.env` file with:

```env
VITE_API_URL=http://localhost:8000
```

**Important:** Vite requires environment variables to be prefixed with `VITE_`

## Building for Production

```bash
npm run build
```

This creates an optimized production build in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Deployment

The built files in `dist/` can be deployed to:
- **Vercel** - `vercel deploy`
- **Netlify** - Drag and drop `dist/` folder
- **AWS S3 + CloudFront**
- **GitHub Pages**
- Any static hosting service

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Development Notes

### Hot Module Replacement (HMR)
Vite provides instant HMR for React components. Changes appear immediately without full page reload.

### Fast Refresh
React Fast Refresh preserves component state during development.

### Import Aliases
Configure in `vite.config.js` if needed:
```js
resolve: {
  alias: {
    '@': '/src',
    '@components': '/src/components'
  }
}
```

## Troubleshooting

### Port Already in Use
Change port in `vite.config.js`:
```js
server: {
  port: 3001
}
```

### Module Not Found
```bash
rm -rf node_modules package-lock.json
npm install
```

### Socket Connection Failed
- Ensure backend is running on port 8000
- Check CORS settings in backend
- Verify `VITE_API_URL` in `.env`

## Additional Resources

- [React Documentation](https://react.dev)
- [Vite Documentation](https://vitejs.dev)
- [Material-UI Documentation](https://mui.com)
- [Socket.IO Client Documentation](https://socket.io/docs/v4/client-api/)

---

**This is a standard React + Vite project structure. No custom modifications or nested directories.** ✅
