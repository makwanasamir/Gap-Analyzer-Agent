# Gap Analysis Agent for Microsoft Teams

An AI-powered document comparison bot built with **M365 Agents SDK (Python)** that analyzes gaps between any two documents using Azure OpenAI.

## Features

- 📄 **Document Comparison**: Upload or paste two documents to find gaps
- 📎 **File Support**: PDF, Word (.docx), and Text files
- 🎯 **Custom Objectives**: Define what kind of gaps you want to find
- 💡 **AI-Powered Analysis**: Uses Azure OpenAI GPT-4o-mini for intelligent gap detection
- 🃏 **Adaptive Cards**: Rich interactive UI with progressive disclosure
- 🔒 **Enterprise Ready**: Single-tenant authentication with Azure AD

## Tech Stack

| Component | Technology |
|-----------|------------|
| **Framework** | M365 Agents SDK (teams-ai) |
| **Language** | Python 3.13 |
| **AI** | Azure OpenAI (GPT-4o-mini) |
| **UI** | Adaptive Cards |
| **Hosting** | Azure App Service (Linux) |
| **Auth** | Azure AD (Single Tenant) |

---

## Table of Contents

1. [Part 1: Local Development Setup](#part-1-local-development-setup)
2. [Part 2: Azure Resource Creation](#part-2-azure-resource-creation)
3. [Part 3: Deploy to Azure](#part-3-deploy-to-azure)
4. [Part 4: Deploy to Teams](#part-4-deploy-to-teams)
5. [Usage Guide](#usage-guide)
6. [Troubleshooting](#troubleshooting)

---

## Part 1: Local Development Setup

### Prerequisites

- **Python 3.13** installed ([Download](https://www.python.org/downloads/))
- **Git** installed ([Download](https://git-scm.com/downloads))
- **Azure OpenAI** resource with GPT-4o-mini model deployed
- **Code Editor** (VS Code recommended)

### Step 1.1: Clone the Repository

```bash
git clone https://github.com/your-username/gap-analysis-agent.git
cd gap-analysis-agent
```

### Step 1.2: Create Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

### Step 1.3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 1.4: Deploy Azure OpenAI Model

If you haven't already deployed an Azure OpenAI model:

1. Go to **Azure Portal**: https://portal.azure.com
2. Search for **Azure OpenAI** and create a new resource (or use existing)
3. Once created, go to **Azure OpenAI Studio**: https://oai.azure.com
4. Click **Deployments** → **Create new deployment**
5. Select:
   - **Model**: `gpt-4o-mini`
   - **Deployment name**: `gpt-4o-mini` (or your preferred name)
   - **Deployment type**: Standard
6. Click **Create**
7. Note down:
   - **Endpoint**: `https://your-resource-name.openai.azure.com`
   - **API Key**: Found in Azure Portal → Your OpenAI resource → **Keys and Endpoint**

### Step 1.5: Configure Environment

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in your Azure OpenAI credentials:
   ```env
   # Leave these empty for local testing
   MicrosoftAppId=
   MicrosoftAppPassword=
   MicrosoftAppType=SingleTenant
   MicrosoftAppTenantId=

   # Fill these with your Azure OpenAI details
   AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com
   AZURE_OPENAI_KEY=your-azure-openai-api-key
   AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
   ```

### Step 1.6: Run Locally

```bash
python app.py
```

The bot will start at: `http://localhost:3978/api/messages`

### Step 1.7: Test with Agents Playground

1. Install the M365 Agents Playground:
   ```bash
   pip install m365-agents-playground
   ```

2. Start the playground:
   ```bash
   agentsplayground start -e http://localhost:3978/api/messages -c msteams
   ```

3. Open http://localhost:56150 in your browser
4. Type `start` to begin testing the bot

> 📝 **Note**: The Agents Playground does not support file uploads. This is expected. Use Teams for testing file upload functionality.

**Alternative: Bot Framework Emulator**
- Download from: https://github.com/microsoft/BotFramework-Emulator/releases
- Connect to: `http://localhost:3978/api/messages`
- Leave App ID and Password empty for local testing

---

## Part 2: Azure Resource Creation

> ⚠️ **Important**: Follow these steps in the exact order shown. Each step depends on the previous one.

### Step 2.1: Create App Registration (Azure AD)

This creates the identity for your bot.

1. Go to **Azure Portal**: https://portal.azure.com
2. Search for **App registrations** in the search bar
3. Click **+ New registration**
4. Fill in:
   - **Name**: `gap-analysis-agent` (or your preferred name)
   - **Supported account types**: Select **Accounts in this organizational directory only (Single tenant)**
   - **Redirect URI**: Leave empty
5. Click **Register**
6. On the **Overview** page, note down:
   - **Application (client) ID**: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` — This is your `MicrosoftAppId`
   - **Directory (tenant) ID**: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` — This is your `MicrosoftAppTenantId`

### Step 2.2: Create Client Secret

1. In your App Registration, go to **Certificates & secrets** (left sidebar)
2. Click **+ New client secret**
3. Fill in:
   - **Description**: `Bot Secret`
   - **Expires**: Choose your preferred expiration (24 months recommended)
4. Click **Add**
5. **IMMEDIATELY** copy the **Value** column — This is your `MicrosoftAppPassword`
   
   > ⚠️ **Warning**: The secret value is only shown once! Copy it now before navigating away.

### Step 2.3: Add API Permissions (For File Uploads)

This allows the bot to download files from SharePoint/OneDrive in Teams.

> 📝 **Note**: This permission is required only for file uploads, not text-only usage. Skip this step if you only need paste-text functionality.

1. In your App Registration, go to **API permissions** (left sidebar)
2. Click **+ Add a permission**
3. Select **Microsoft Graph**
4. Select **Application permissions** (NOT Delegated)
5. Search for and check: `Files.Read.All`
6. Click **Add permissions**
7. Click **Grant admin consent for [Your Organization]**
8. Confirm by clicking **Yes**
9. Verify the **Status** column shows ✅ **Granted for [Your Organization]**

### Step 2.4: Create App Service Plan

1. Go to **Azure Portal**: https://portal.azure.com
2. Search for **App Service plans** in the search bar
3. Click **+ Create**
4. Fill in:
   - **Subscription**: Select your Azure subscription
   - **Resource Group**: Create new or use existing (e.g., `gap-analysis-rg`)
   - **Name**: `gap-analysis-plan` (or your preferred name)
   - **Operating System**: **Linux**
   - **Region**: Choose closest to your users (e.g., `East US`, `West Europe`)
   - **Pricing Tier**: Click **Explore pricing plans** → Select **Basic B1** (recommended for testing) or **Standard S1** (for production)
5. Click **Review + create** → **Create**

### Step 2.5: Create App Service

1. Go to **Azure Portal**: https://portal.azure.com
2. Search for **App Services** in the search bar
3. Click **+ Create** → **Web App**
4. Fill in:
   - **Subscription**: Select your Azure subscription
   - **Resource Group**: Same as App Service Plan (e.g., `gap-analysis-rg`)
   - **Name**: `your-gap-analysis-bot` — This becomes your domain: `your-gap-analysis-bot.azurewebsites.net`
   - **Publish**: **Code**
   - **Runtime stack**: **Python 3.13**
   - **Operating System**: **Linux**
   - **Region**: Same as App Service Plan
   - **App Service Plan**: Select the plan you created in Step 2.4
5. Click **Review + create** → **Create**
6. Wait for deployment to complete (1-2 minutes)

### Step 2.6: Configure App Service Settings

1. Go to your newly created **App Service**
2. In the left sidebar, go to **Settings** → **Environment variables**
3. Click **+ Add** for each of the following variables:

   | Name | Value |
   |------|-------|
   | `MicrosoftAppId` | Your App ID from Step 2.1 |
   | `MicrosoftAppPassword` | Your Secret from Step 2.2 |
   | `MicrosoftAppType` | `SingleTenant` |
   | `MicrosoftAppTenantId` | Your Tenant ID from Step 2.1 |
   | `AZURE_OPENAI_ENDPOINT` | `https://your-resource.openai.azure.com` |
   | `AZURE_OPENAI_KEY` | Your Azure OpenAI API key |
   | `AZURE_OPENAI_DEPLOYMENT` | `gpt-4o-mini` |

4. Click **Apply** at the bottom
5. Click **Confirm** to restart the app

### Step 2.7: Configure Startup Command

1. In the App Service, go to **Settings** → **Configuration**
2. Click the **General settings** tab
3. In **Startup Command**, enter:
   ```
   gunicorn --bind=0.0.0.0 --worker-class aiohttp.worker.GunicornWebWorker app:APP
   ```
4. Click **Save**

### Step 2.8: Create Azure Bot

1. Go to **Azure Portal**: https://portal.azure.com
2. Search for **Azure Bot** in the search bar
3. Click **Create**
4. Fill in:
   - **Bot handle**: `gap-analysis-bot` (or your preferred name)
   - **Subscription**: Select your Azure subscription
   - **Resource group**: Same as before (e.g., `gap-analysis-rg`)
   - **Pricing tier**: **Standard** (or Free for testing)
   - **Type of App**: **Single Tenant**
   - **Creation type**: **Use existing app registration**
   - **App ID**: Paste your App ID from Step 2.1
   - **App tenant ID**: Paste your Tenant ID from Step 2.1
5. Click **Review + create** → **Create**
6. Wait for deployment to complete

### Step 2.9: Configure Messaging Endpoint

1. Go to your newly created **Azure Bot**
2. In the left sidebar, click **Configuration**
3. In **Messaging endpoint**, enter:
   ```
   https://your-gap-analysis-bot.azurewebsites.net/api/messages
   ```
   (Replace `your-gap-analysis-bot` with your actual App Service name from Step 2.5)
4. Click **Apply**

### Step 2.10: Enable Microsoft Teams Channel

1. In your Azure Bot, go to **Channels** (left sidebar)
2. Click **Microsoft Teams** (or **+ Add a featured channel** → **Microsoft Teams**)
3. Read and accept the Terms of Service
4. Click **Apply**
5. Verify the Teams channel shows as **Running**

---

## Part 3: Deploy to Azure

### Step 3.1: Create Deployment Package

**Windows (PowerShell):**
```powershell
Compress-Archive -Path "app.py", "requirements.txt", "src", "startup.sh" -DestinationPath "deploy.zip" -Force
```

**macOS/Linux:**
```bash
zip -r deploy.zip app.py requirements.txt src startup.sh
```

### Step 3.2: Deploy via Azure Portal

1. Go to your **App Service** in Azure Portal
2. In the left sidebar, go to **Deployment** → **Deployment Center**
3. Under **Settings**, select **Source**: **Local Git** or **FTPS** or use the method below:

**Alternative: Deploy via Kudu (Recommended)**

1. Go to: `https://your-gap-analysis-bot.scm.azurewebsites.net`
2. Click **Tools** → **Zip Push Deploy**
3. Drag and drop your `deploy.zip` file
4. Wait for deployment to complete (2-3 minutes)

**Alternative: Deploy via Azure CLI**

```bash
az webapp deploy --resource-group your-resource-group --name your-gap-analysis-bot --src-path deploy.zip --type zip
```

### Step 3.3: Verify Deployment

1. Go to your App Service → **Overview**
2. Click the **Default domain** link (e.g., `https://your-gap-analysis-bot.azurewebsites.net`)
3. You should see: `"Hello, Gap Analysis Bot is running!"`
4. Go back to Azure Bot → **Test in Web Chat**
5. Type `start` and verify the bot responds

---

## Part 4: Deploy to Teams

### Prerequisites for Teams Deployment

- ✅ Azure Bot is working (tested in Web Chat)
- ✅ Microsoft Teams channel is enabled
- ✅ App icons ready:
  - `color.png` — 192x192 pixels (full color)
  - `outline.png` — 32x32 pixels (transparent outline)

### Step 4.1: Update the Manifest

Edit `manifest/manifest.json` and replace ALL placeholder values:

| Placeholder | Replace With | Example |
|-------------|--------------|---------|
| `{{BOT_ID}}` | Your App ID from Step 2.1 | `d49e9c0f-8da0-4428-afc5-9b1ee183fc72` |
| `{{COMPANY_NAME}}` | Your company name | `Contoso` |
| `{{COMPANY_WEBSITE}}` | Your website URL (must start with https://) | `https://contoso.com` |
| `{{APP_DOMAIN}}` | Your App Service domain (without https://) | `your-gap-analysis-bot.azurewebsites.net` |

**Important Notes:**
- The `id` field (line 5) and `botId` field (line 28) MUST be identical
- Both must match your App Registration's Application ID
- All URLs must start with `https://`

### Step 4.2: Create the App Package

**Windows (PowerShell):**
```powershell
cd manifest
Compress-Archive -Path "manifest.json", "color.png", "outline.png" -DestinationPath "../appPackage.zip" -Force
cd ..
```

**macOS/Linux:**
```bash
cd manifest
zip -r ../appPackage.zip manifest.json color.png outline.png
cd ..
```

### Step 4.3: Upload for Personal Testing

1. Open **Microsoft Teams** (desktop or web app)
2. Click **Apps** in the left sidebar
3. Click **Manage your apps** at the bottom left
4. Click **Upload an app**
5. Select **Upload a custom app**
6. Browse and select your `appPackage.zip`
7. Click **Add** in the dialog that appears
8. The bot will open in a chat — type `start` to test!

> 📝 **Note**: If "Upload a custom app" is disabled, your Teams Administrator needs to enable it:
>
> 1. Go to **Teams Admin Center**: https://admin.teams.microsoft.com
> 2. Navigate to **Teams apps** → **Permission policies**
> 3. Click on **Global (Org-wide default)** (or create a custom policy)
> 4. Under **Custom apps**, select **Allow all apps**
> 5. Click **Save**
> 6. Navigate to **Teams apps** → **Setup policies**
> 7. Click on **Global (Org-wide default)**
> 8. Enable **Upload custom apps** toggle
> 9. Click **Save**
> 10. Wait 15-30 minutes for changes to propagate


### Step 4.4: Deploy to Entire Organization

> ⚠️ **Requires**: Teams Administrator or Global Administrator role

1. Go to **Teams Admin Center**: https://admin.teams.microsoft.com
2. Sign in with your admin account
3. Navigate to **Teams apps** → **Manage apps**
4. Click **⬆ Upload new app** (top right corner)
5. Upload your `appPackage.zip`
6. Wait for the upload to complete
7. Search for "Gap Analysis Agent" in the app list
8. Click on the app name to open details
9. Under **Status**, change **Publishing status** to **Published**
10. Navigate to **Teams apps** → **Setup policies**
11. Click on **Global (Org-wide default)**
12. Under **Installed apps**, click **+ Add apps**
13. Search for "Gap Analysis Agent"
14. Click **Add** → **Save**
15. (Optional) Under **Pinned apps**, click **+ Add apps** to pin it to the sidebar

> 📝 **Note**: Changes may take up to 24 hours to propagate to all users in the organization.

---

## Usage Guide

1. **Start**: Type `start`, `hello`, or `help` to begin
2. **Choose Input Method**: Select "Upload Files" or "Paste Text"
3. **Document A (Source)**: Upload or paste your source document
4. **Document B (Target)**: Upload or paste your target document(s)
5. **Set Objective**: Define what gaps you want to find
6. **Review Results**: View matched items, gaps, and recommendations

### Supported Commands

| Command | Description |
|---------|-------------|
| `start` | Begin a new gap analysis session |
| `help` | Show available commands |
| `about` | Learn about the bot |
| `status` | Check current session status |
| `reset` | Clear session and start fresh |

### Supported File Types

- **PDF** (.pdf)
- **Microsoft Word** (.docx)
- **Plain Text** (.txt)

---

## Project Structure

```
├── app.py                    # Entry point (aiohttp server)
├── requirements.txt          # Python dependencies
├── startup.sh                # Azure App Service startup script
├── .env.example              # Environment template
├── deploy.zip                # Pre-built deployment package
├── src/
│   ├── __init__.py
│   ├── agent.py              # M365 Application setup
│   ├── bot.py                # GapAnalysisBot handlers
│   ├── cards.py              # Adaptive Card definitions
│   ├── config.py             # Configuration loader
│   ├── file_handler.py       # PDF/DOCX/TXT parsing
│   ├── analyze.py            # Gap analysis logic
│   ├── azure_openai_client.py
│   └── logger.py
├── manifest/
│   ├── manifest.json         # Teams app manifest (template)
│   ├── color.png             # App icon (192x192)
│   └── outline.png           # Outline icon (32x32)
└── tests/                    # Unit tests
```

---

## Troubleshooting

### Bot doesn't respond in Teams

1. **Check Azure Bot**: Go to Azure Portal → Azure Bot → Test in Web Chat
2. **Verify messaging endpoint**: Must be `https://your-app.azurewebsites.net/api/messages`
3. **Check Teams channel**: Ensure Microsoft Teams channel is enabled and Running
4. **Restart App Service**: Azure Portal → App Service → Overview → Restart

### Authentication errors (401/403)

1. **Verify App Settings**: Ensure all `MicrosoftApp*` values are correctly set in App Service
2. **Check App Type**: Must be `SingleTenant`
3. **Verify Tenant ID**: Must match your Azure AD tenant
4. **Check App Registration**: Ensure the App ID matches in both App Registration and Azure Bot

### File upload fails

1. **Check API permissions**: Ensure `Sites.Read.All` is added with admin consent
2. **Verify permission status**: Must show "Granted for [Your Organization]"
3. **Restart App Service**: Changes may require a restart to take effect

### Cards not updating in Teams

- This is a known Teams limitation for some card types
- The bot handles this gracefully by sending new cards
- No action required

### Azure OpenAI errors

1. **Check endpoint URL**: Must include `https://` and end with `.openai.azure.com`
2. **Verify deployment name**: Must match exactly what's in Azure OpenAI Studio
3. **Check API key**: Ensure it's valid and not expired
4. **Check quota**: Ensure you have available tokens in your Azure OpenAI resource

### View App Service Logs

**Via Azure Portal:**
1. Go to App Service → **Monitoring** → **Log stream**

**Via Azure CLI:**
```bash
az webapp log tail --name your-app-name --resource-group your-resource-group
```

---

## M365 Agents SDK Confirmation

This bot is built with the **M365 Agents SDK (teams-ai)**:

```python
# In src/agent.py
from teams import Application, ApplicationOptions, TeamsAdapter
app = Application[AppState](app_options)
```

```txt
# In requirements.txt
teams-ai>=1.6.0
```

---

## License

MIT
