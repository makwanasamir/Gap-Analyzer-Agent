# Gap Analysis Bot for Microsoft Teams (Python)

A simple Teams bot that compares Job Descriptions with Resumes to identify skill gaps using Azure OpenAI (gpt-4o-mini).

## Features

- 🎯 **Gap Analysis**: Compare JD and Resume to find matched, partial, and missing skills
- 💡 **Recommendations**: Get actionable suggestions for improving alignment
- 🤖 **Teams Integration**: Works in personal chat, group chats, and channels
- 🔒 **Secure**: Azure OpenAI integration with secure credential storage

## Prerequisites

1. **Python 3.10+** installed
2. **Azure OpenAI** resource with `gpt-4o-mini` deployment
3. **Azure Bot Registration** (for Teams deployment)
4. **Agents Playground** or **Bot Framework Emulator** (for local testing)

## Quick Start

### 1. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate   # Windows
# or: source venv/bin/activate  # macOS/Linux
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Edit `.env` with your Azure OpenAI credentials:

```
MICROSOFT_APP_ID=         # Leave blank for local testing
MICROSOFT_APP_PASSWORD=   # Leave blank for local testing
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_KEY=your-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
```

### 4. Run Locally

```bash
python app.py
```

The bot will start at `http://localhost:3978/api/messages`

### 5. Test with Agents Playground

```bash
agentsplayground start -e http://localhost:3978/api/messages -c msteams
```

Then open http://localhost:56150 in your browser.

## Deploy to Azure

### 1. Create Azure Resources

- **Azure Bot Registration**: Create a Multi-Tenant bot registration
- **Azure App Service** or **Azure Functions**: Host the bot code
- **Azure Key Vault** (recommended): Store secrets securely

### 2. Configure Bot Registration

1. In Azure Portal, create a new Azure Bot
2. Note the `Microsoft App ID`
3. Create a new secret under "Configuration" > "Manage Password"
4. Set the Messaging Endpoint to `https://your-app.azurewebsites.net/api/messages`

### 3. Deploy Code

Deploy to Azure App Service:

```bash
az webapp up --name your-bot-name --resource-group your-rg --runtime "NODE:18-lts"
```

### 4. Configure App Settings

Set environment variables in Azure App Service:

```bash
az webapp config appsettings set --name your-bot-name --resource-group your-rg --settings \
  MICROSOFT_APP_ID=your-app-id \
  MICROSOFT_APP_PASSWORD=your-app-password \
  AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com \
  AZURE_OPENAI_KEY=your-key \
  AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
```

## Deploy to Teams

### 1. Update Manifest

Edit `manifest/manifest.json`:
- Replace `{{BOT_ID}}` with your Microsoft App ID
- Update developer info and URLs

### 2. Create App Package

```bash
cd manifest
zip -r ../gap-analysis-bot.zip *
```

### 3. Upload to Teams

1. Go to Teams Admin Center or use "Upload a custom app" in Teams
2. Upload `gap-analysis-bot.zip`
3. Approve and install the app

## Usage

1. **Start**: Type "start" or "hello" to open the analysis form
2. **Paste JD**: Paste the full Job Description text
3. **Paste Resume**: Paste the full Resume text
4. **Analyze**: Click "Analyze Gaps" button
5. **Review**: View matched skills, missing skills, and recommendations

## Project Structure

```
├── src/
│   ├── bot/
│   │   ├── index.js              # Server entry point
│   │   ├── gapAnalysisBot.js     # Bot message handler
│   │   └── handlers/
│   │       └── submitHandler.js  # Adaptive Card submit handler
│   ├── api/
│   │   └── analyze.js            # Gap analysis logic
│   ├── lib/
│   │   └── azureOpenAI.js        # Azure OpenAI client
│   └── adaptiveCards/
│       ├── analysisCard.json     # Input form card
│       ├── resultCard.json       # Results display card
│       └── errorCard.json        # Error display card
├── manifest/
│   ├── manifest.json             # Teams app manifest
│   ├── color.png                 # App icon (color)
│   └── outline.png               # App icon (outline)
├── .env.example                  # Environment template
├── package.json
└── README.md
```

## Troubleshooting

### Bot doesn't respond
- Check that the bot is running (`npm start`)
- Verify the messaging endpoint URL is correct
- Check Azure OpenAI credentials are set

### Azure OpenAI errors
- Verify endpoint URL includes `https://` 
- Check deployment name matches your Azure OpenAI deployment
- Ensure API key is valid and not expired

### Teams app won't install
- Ensure `manifest.json` has valid Bot ID
- Check that icons are valid PNG files
- Verify all URLs in manifest are HTTPS

## License

MIT
