<a href="https://livekit.io/">
  <img src="./.github/assets/livekit-mark.png" alt="LiveKit logo" width="100" height="100">
</a>

# Python Voice Agent

<p>
  <a href="https://cloud.livekit.io/projects/p_/sandbox"><strong>Deploy a sandbox app</strong></a>
  •
  <a href="https://docs.livekit.io/agents/overview/">LiveKit Agents Docs</a>
  •
  <a href="https://livekit.io/cloud">LiveKit Cloud</a>
  •
  <a href="https://blog.livekit.io/">Blog</a>
</p>

A voice agent implementation using LiveKit and Python for handling speech-to-text, agent processing, and text-to-speech capabilities.

## Setup Instructions

### 1. Create a Virtual Environment

Clone the repository and set up a virtual environment:

```console
# Linux/macOS
cd voice-agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

<details>
  <summary>Windows instructions (click to expand)</summary>
  
```cmd
:: Windows (CMD/PowerShell)
cd voice-agent
python3 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
</details>

### 2. Configure Environment Variables

Create a `.env.local` file by copying `.env.example`:

```console
cp .env.example .env.local
```

Edit the `.env.local` file and add your API keys:

```
LIVEKIT_API_KEY="your_livekit_api_key"
LIVEKIT_API_SECRET="your_livekit_api_secret"
LIVEKIT_URL=wss://your-project.livekit.cloud
OPENAI_API_KEY="sk-your_openai_api_key"
```

You can get your LiveKit credentials from the [LiveKit Cloud Console](https://cloud.livekit.io).

### 3. Running the Server

Start the API server:

```console
python api.py
```

In a separate terminal (with the virtual environment activated), start the agent:

```console
python agent.py dev
```

## Frontend Integration

This backend requires a frontend application to communicate with. You can use:

1. The included `voice-agent-frontend` in this repository
2. One of the example frontends in [livekit-examples](https://github.com/livekit-examples/)
3. A custom frontend following one of the [client quickstarts](https://docs.livekit.io/realtime/quickstarts/)
4. A hosted [Sandbox](https://cloud.livekit.io/projects/p_/sandbox) frontend

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
