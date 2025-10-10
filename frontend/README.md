# Netra Frontend

A modern Next.js web interface for the Netra automation agent.

## Features

- **Real-time Chat Interface**: Interactive chat with streaming responses
- **Tool Usage Visualization**: See what tools the agent is using in real-time
- **System Monitoring**: Monitor running programs and agent status
- **Settings Panel**: Configure agent preferences
- **Responsive Design**: Works on desktop and mobile devices
- **Dark Mode Support**: Built-in theme switching

## Getting Started

### Prerequisites

- Node.js 18+ installed
- Netra API server running (port 8000)

### Installation

1. Install dependencies:
```bash
npm install
```

2. Run the development server:
```bash
npm run dev
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser

### Building for Production

```bash
npm run build
npm run start
```

## Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx       # Root layout
│   │   ├── page.tsx         # Main page with chat interface
│   │   └── globals.css      # Global styles with Tailwind
│   ├── components/
│   │   └── ui/              # Shadcn UI components
│   └── lib/
│       └── utils.ts         # Utility functions
├── public/                  # Static assets
└── package.json
```

## Components

The UI is built with [Shadcn UI](https://ui.shadcn.com/) components:

- **Button**: Action buttons throughout the interface
- **Input**: Text input for chat messages
- **Card**: Container components for sections
- **Tabs**: Navigation between Chat, System, and Settings
- **Badge**: Status indicators
- **ScrollArea**: Scrollable content areas
- **Separator**: Visual dividers

## API Integration

The frontend connects to the Netra API server at `http://localhost:8000`:

- `/api/status` - System status and running programs
- `/api/query/stream` - Streaming chat responses
- `/api/settings` - Agent configuration

Make sure the API server is running before starting the frontend.

## Customization

### Changing the API URL

Edit the API endpoints in `src/app/page.tsx` if your API server runs on a different port or host.

### Theme Customization

Modify the color scheme in `src/app/globals.css` to change the theme colors.

## Troubleshooting

**Frontend won't connect to API:**
- Make sure the API server is running on port 8000
- Check the browser console for CORS errors
- Verify the API URL in the frontend code

**Build errors:**
- Delete `node_modules` and `package-lock.json`
- Run `npm install` again
- Make sure you have Node.js 18+ installed

## License

MIT

