# Repository Setup Guide

This guide will walk you through setting up this repository with AI-powered code review workflows, Firebase integration, and Docker### 4. Branch Protection (Optional but Recommended)

1. Go to Settings → Branches
2. Add rule for main branch
3. Enable "Require status checks to pass before merging"
4. Select the AI code review workflow

## Testing the Setup

### 1. Test Docker Image Monitoringnt updates.

## Prerequisites

Before starting, ensure you have:
- A GitHub repository with admin access
- A Google Cloud Platform account (for Firebase)
- Anthropic API account (for Claude)
- OpenAI API account (for GPT models)
- Docker installed locally (optional, for testing)

## Docker Setup

This repository uses Docker images from `kaloyangavrilov/github-workflows` to automatically update AI agent workflows.

### 1. Enable Docker Image Monitoring

The repository is configured to monitor Docker image updates automatically. When you create a pull request with the checkbox "Load the latest agent updates" marked, the system will:

1. Check for updates to `kaloyangavrilov/github-workflows:latest`
2. Extract updated workflow files if found
3. Commit changes to your repository
4. Run the AI code review on your changes

### 2. Manual Docker Testing (Optional)

To test Docker integration locally:

```bash
# Pull the latest agent image
docker pull kaloyangavrilov/github-workflows:latest

# Method 1: .github doesnt exist (Recommended)
docker create --name temp-container kaloyangavrilov/github-workflows:latest
docker cp temp-container:/app/.github ./.github
docker rm temp-container


# Method 2: Extract to temporary directory first (Recommended)
docker create --name temp-container kaloyangavrilov/github-workflows:latest
docker cp temp-container:/app/.github ./temp-github
docker rm temp-container

# Compare with your current .github directory
diff -r .github temp-github

# To merge changes, copy only the files you want:
mkdir -p .github/workflows
cp temp-github/workflows/*.yml .github/workflows/
mkdir -p .github/workflows/scripts
cp temp-github/workflows/scripts/* .github/workflows/scripts/ 2>/dev/null || true
rm -rf temp-github

# For selective copying (recommended):
cp temp-github/workflows/*.yml .github/workflows/
cp -r temp-github/workflows/scripts .github/workflows/ 2>/dev/null || true
cp -r temp-github/workflows/actions .github/workflows/ 2>/dev/null || true


# Method 3: Backup existing .github first
mv .github .github-backup
docker create --name temp-container kaloyangavrilov/github-workflows:latest
docker cp temp-container:/app/.github ./.github
docker rm temp-container
# Then manually merge files from .github-backup if needed
```

## Firebase Configuration

Firebase is used to track architecture changes and manage Docker image versions.

### 1. Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or use existing one
3. Enable Firestore Database
4. Set Firestore rules to allow read/write access:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if true;
    }
  }
}
```

### 2. Create Service Account

1. Go to Project Settings → Service Accounts
2. Click "Generate new private key"
3. Download the JSON file
4. Copy the entire JSON content (you'll need this for GitHub secrets)

### 3. Initialize Firebase Collections

The system expects these Firestore collections (where `PROJECT_NAME` is the value from the `.github/workflows/scripts/config.py` file, default is "test"):

- `PROJECT_NAME/architecture_summaries/summaries/{repo}` - Architecture summaries
- `PROJECT_NAME/architecture_changes/changes` - Change tracking
- `PROJECT_NAME/docker_images/digests` - Docker image version tracking
- `PROJECT_NAME/macros/settings/macros` - Configuration macros

## GitHub Secrets Setup

Add these secrets to your repository (Settings → Secrets and variables → Actions):

### Required Secrets

#### `FIREBASE_SERVICE_ACCOUNT_JSON`
- **How to get**: Follow the steps in the Firebase Configuration section
- **1. Go to Firebase Console → Project Settings → Service Accounts**
- **2. Click "Generate new private key"**
- **3. Download the JSON file**
- **4. Copy the entire JSON content**
- **Value**: Complete JSON content from Firebase service account file
- **Example**:
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "service-account@your-project.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/service-account%40your-project.iam.gserviceaccount.com"
}
```

#### `ANTHROPIC_API_KEY`
- **How to get**: Sign up at [Anthropic Console](https://console.anthropic.com/)
- **Value**: Your Anthropic API key (starts with `sk-ant-`)
- **Used for**: Claude Sonnet 4 model for complex code reviews

#### `OPENAI_API_KEY`
- **How to get**: Sign up at [OpenAI Platform](https://platform.openai.com/)
- **Value**: Your OpenAI API key (starts with `sk-`)
- **Used for**: GPT-4.1-nano model for lightweight code reviews

#### `PAT_TOKEN`
- **How to get**: GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
- **Required permissions**: `repo`, `pull_requests`, `contents`
- **Value**: Your GitHub personal access token
- **Used for**: Posting PR comments and accessing repository

### Setting Up Secrets

1. Go to your repository on GitHub
2. Click Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add each secret with the exact name and value

## Repository Configuration

### 1. Verify Workflow Files

Ensure these key files are present in `.github/workflows/`:
- `ai-review.yml` - Main AI code review workflow
- `workflow-manager.yml` - Orchestrates workflow processes
- `agent-update.yml` - Handles Docker image updates

### 2. Configure Pull Request Template

The `.github/pull_request_template.md` provides checkboxes for:
- Loading latest agent updates
- Marking important changes
- Requesting Claude Sonnet 4 explicitly
- Custom review thresholds

### 3. Firebase Macros Configuration

The system now supports configuration macros stored in Firebase:
- Global default settings can be stored in Firebase
- PR-specific macros can override Firebase defaults
- Macros control thresholds, model selection, and other behaviors
- Configuration is resolved at runtime with PR-specific settings taking precedence

### 4. Branch Protection (Optional but Recommended)

1. Go to Settings → Branches
2. Add rule for main branch
3. Enable "Require status checks to pass before merging"
4. Select the code review workflow

## Testing the Setup

### 1. Test Docker Image Monitoring

1. Create a new branch
2. Make a small change
3. Create PR with "Load the latest agent updates" checked
4. Verify the workflow runs and updates are applied

### 2. Test AI Code Review

1. Create a branch with some code changes
2. Create PR (leave agent updates unchecked)
3. Check different scenarios:
   - Small changes (should use GPT-4.1-nano)
   - Large changes or "important changes" marked (should use Claude)
   - Architecture changes (should track in Firebase)

### 3. Verify Firebase Integration

Check Firestore console to see:
- Architecture summaries being created
- Docker digest tracking

## Cost Tracking

The system now includes AI cost tracking features:
- Tracks API usage for both Anthropic and OpenAI models
- Provides cost summaries at the end of each workflow run
- Uploads cost data as artifacts for later analysis
- Helps optimize model selection based on usage patterns

## Troubleshooting

### Common Issues

#### 1. Firebase Connection Failed
```
Error: Invalid JSON in Firebase service account credentials
```
**Solution**: Ensure the entire JSON is copied correctly, including all brackets and quotes.

#### 2. API Key Invalid
```
Error: Invalid API key
```
**Solution**: 
- Verify API keys are correct
- Check API key permissions and billing
- Ensure no extra spaces in secret values

#### 3. Docker Image Not Found
```
Error: Docker repository 'kaloyangavrilov/github-workflows' API check failed
```
**Solution**: This is usually temporary. The workflow uses the nick-invision/retry action to automatically retry operations with exponential backoff.

#### 4. Permission Denied
```
Error: Resource not accessible by integration
```
**Solution**: 
- Verify PAT_TOKEN has correct permissions
- Check if repository is private and token has `repo` scope

### Debug Mode

To enable detailed logging, add this to any workflow step:
```yaml
- name: Debug Firebase
  run: python3 .github/workflows/debug_firebase.py
```

### Cost Analysis

To analyze AI costs:
```bash
# View cost summary from workflow artifacts
# Download the ai-response-output artifact from the workflow run
cat /tmp/ai_cost_summary.txt
```

### Manual Verification Commands

Test Firebase connection:
```bash
python3 .github/workflows/debug_firebase.py
```

## Configuration Customization

### Adjusting Thresholds

You can customize behavior through multiple methods:

1. **Firebase Macros**: Set global configuration defaults in Firebase
2. **PR Template**: Override defaults with PR-specific macros in backticks
3. **Workflow Configuration**: Update thresholds directly in workflow files
4. **Workflow Environment**: Set environment variables in workflow files


## Project Name Configuration

The system uses a global project name that determines the Firebase collection paths. By default, this is set to "test". To change it:

1. Open the file `.github/workflows/scripts/config.py`
2. Update the `PROJECT_NAME` variable to match your desired project name:
   ```python
   PROJECT_NAME = "your-project-name"
   ```
3. This change will affect all Firebase collections:
   - Collections will be created as `your-project-name/architecture_summaries/summaries/{repo}`
   - Changes will be tracked in `your-project-name/architecture_changes/changes`
   - Docker image versions will be stored in `your-project-name/docker_images/digests`
   - Macros will be stored in `your-project-name/macros/settings/macros`

Update the project name before initializing your Firebase collections to ensure all data is stored in the correct location.

### Model Selection Logic

The system chooses AI models based on:
- Explicit checkbox selection
- "Important changes" labels/markers
- Diff size vs. LINE_THRESHOLD
- PR description checkboxes
- Macro configurations (both global and PR-specific)

### Architecture Summary Triggers

Architecture summaries are generated when:
- Important changes are detected
- Change count exceeds CHANGES_THRESHOLD
- Manual trigger via workflow

## Support

For issues:
1. Check workflow logs in Actions tab
2. Review Firebase console for data
3. Check API usage in respective consoles
4. Verify all secrets are correctly set

For updates to the agent system, they will be automatically pulled from the Docker image when you check the update box in PR templates.
