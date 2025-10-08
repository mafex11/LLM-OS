# Windows-Use ChatGPT-like UI

A modern, ChatGPT-inspired interface for the Windows-Use agent built with Next.js and Shadcn UI.

## Features

- **Modern Chat Interface**: ChatGPT-like design with sidebar and main chat area
- **Conversation Management**: Create new chats, switch between conversations
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Real-time Updates**: Live status indicators and typing animations
- **Auto-resizing Input**: Textarea that grows with your message
- **Keyboard Shortcuts**: Enter to send, Shift+Enter for new line
- **Dark/Light Theme**: Automatic theme switching based on system preference

## Quick Start

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start the development server:**
   ```bash
   npm run dev
   ```

3. **Open your browser:**
   Navigate to `http://localhost:3000` - you'll be automatically redirected to the chat interface.

## Usage

### Starting a New Chat
- Click the "New Chat" button in the sidebar
- Start typing your question or command

### Managing Conversations
- All your conversations are saved in the sidebar
- Click on any conversation to continue where you left off
- The sidebar shows the number of messages in each conversation

### Chatting with the Agent
- Type your message in the input area at the bottom
- Press Enter to send, or Shift+Enter for a new line
- The agent will respond with helpful information about your Windows system

### Mobile Usage
- On mobile devices, the sidebar can be toggled with the menu button
- The interface is fully responsive and touch-friendly

## Technical Details

### Built With
- **Next.js 15** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Shadcn UI** - Modern component library
- **Radix UI** - Accessible primitives
- **Lucide React** - Beautiful icons

### Architecture
- Single-page application with client-side routing
- RESTful API communication with the Python backend
- Real-time status updates and error handling
- Responsive design with mobile-first approach

### File Structure
```
src/
├── app/
│   ├── chat/page.tsx          # Main chat interface
│   ├── page.tsx               # Home page (redirects to chat)
│   └── globals.css            # Global styles and themes
├── components/
│   ├── ui/                    # Shadcn UI components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── textarea.tsx
│   │   ├── scroll-area.tsx
│   │   ├── avatar.tsx
│   │   └── separator.tsx
│   └── [existing components]  # Original UI components
└── lib/
    └── utils.ts               # Utility functions
```

## Customization

### Themes
The interface supports both light and dark themes. You can customize the theme by modifying the CSS variables in `src/app/globals.css`.

### Components
All UI components are built with Shadcn UI and can be easily customized. Check the `src/components/ui/` directory for component implementations.

### Styling
The interface uses Tailwind CSS with a custom design system. You can modify colors, spacing, and other design tokens in `tailwind.config.ts`.

## API Integration

The chat interface communicates with the Python backend via REST API:

- **Query Processing**: `POST /api/query` - Send messages to the agent
- **System Status**: `GET /api/status` - Check agent readiness
- **Conversation Management**: `POST /api/conversation/clear` - Clear chat history

Make sure the Python API server is running on `http://localhost:8000` for the interface to work properly.

## Development

### Adding New Features
1. Create new components in `src/components/`
2. Add new pages in `src/app/`
3. Update the API integration as needed
4. Test responsiveness across devices

### Building for Production
```bash
npm run build
npm run start
```

### Static Export (for Installer)
```bash
npm run export
```

## Troubleshooting

### Common Issues

**Interface won't load:**
- Make sure the Python API server is running on port 8000
- Check browser console for error messages
- Verify all dependencies are installed

**Messages not sending:**
- Check network connectivity
- Verify API server is responding
- Look for CORS errors in browser console

**Styling issues:**
- Clear browser cache
- Restart the development server
- Check Tailwind CSS compilation

## Support

For technical support or feature requests, please refer to the main Windows-Use documentation or create an issue in the project repository.
