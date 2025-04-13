<img src="./.github/assets/app-icon.png" alt="Voice Assistant App Icon" width="100" height="100">

# Web Voice Assistant Frontend

A Next.js frontend for the LiveKit Voice Agent that provides a simple voice interface using the [LiveKit JavaScript SDK](https://github.com/livekit/client-sdk-js).

## Setup Instructions

### 1. Configure Environment Variables

Create a `.env.local` file by copying from the example:

```bash
cp .env.example .env.local
```

Edit the `.env.local` file to include your LiveKit credentials:

```
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
LIVEKIT_URL=wss://your-project.livekit.cloud
```

You can get your LiveKit credentials from the [LiveKit Cloud Console](https://cloud.livekit.io).

### 2. Install Dependencies

Install the required dependencies using pnpm:

```bash
pnpm install
```

### 3. Start the Development Server

Run the development server:

```bash
pnpm dev
```

The application will be available at http://localhost:3000 in your browser.

## Backend Integration

This frontend requires a voice agent backend to function properly. You can use:

1. The included `voice-agent` Python backend in this repository
2. One of our sample voice assistant agents for [Python](https://github.com/livekit-examples/voice-pipeline-agent-python) or [Node.js](https://github.com/livekit-examples/voice-pipeline-agent-node)
3. A custom agent following our [agent development guide](https://docs.livekit.io/agents/quickstart/)

## License

MIT License

Copyright (c) 2025 LiveKit, Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
