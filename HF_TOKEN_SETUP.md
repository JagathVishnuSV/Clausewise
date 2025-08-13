# Hugging Face API Token Setup Guide

## Issue Summary
You're experiencing 403 Forbidden errors when trying to access the IBM Granite model via Hugging Face API. This typically indicates authentication or permission issues.

## Quick Fix Steps

### 1. Get Your Hugging Face Token
1. Go to https://huggingface.co/settings/tokens
2. Create a new token with `read` permissions
3. Copy the token (starts with `hf_...`)

### 2. Set Environment Variable

**Windows (Command Prompt):**
```cmd
set HF_API_TOKEN=your_token_here
```

**Windows (PowerShell):**
```powershell
$env:HF_API_TOKEN="your_token_here"
```

**Linux/Mac:**
```bash
export HF_API_TOKEN=your_token_here
```

### 3. Verify Token Permissions
The IBM Granite model (`ibm-granite/granite-3.2-2b-instruct`) may require special access. Check if your token has access to this specific model.

### 4. Test the Setup
Run the validation script:
```bash
python -c "from utils.hf_auth_utils import validate_hf_token; print('Token valid:', validate_hf_token())"
```

## Alternative Solutions

If the IBM Granite model is not accessible:

1. **Use a different model**: The code now includes fallback classification
2. **Request model access**: Visit the model page on Hugging Face and request access
3. **Use local models**: Consider downloading the model locally

## Troubleshooting

### Check Current Token
```bash
echo %HF_API_TOKEN%  # Windows
echo $HF_API_TOKEN   # Linux/Mac
```

### Test Model Access
```python
from utils.hf_auth_utils import check_model_accessibility
print("Model accessible:", check_model_accessibility("ibm-granite/granite-3.2-2b-instruct"))
```

### Common Issues
- **Token not set**: Ensure HF_API_TOKEN environment variable is properly configured
- **Token expired**: Generate a new token from Hugging Face
- **Model access**: Some models require explicit approval from the model owner
- **Rate limits**: Check if you've hit API rate limits

## Environment Configuration

Add to your `.env` file (if using one):
```
HF_API_TOKEN=your_actual_token_here
```

Or create a startup script that sets the environment variable before running the application.
