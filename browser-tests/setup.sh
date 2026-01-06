#!/bin/bash

# Browser Tests Setup Script
# Automates the installation and verification process

set -e  # Exit on error

echo "🚀 Setting up Browser Test Suite for Image Hosting App"
echo "======================================================"
echo ""

# Check if Bun is installed
echo "1️⃣  Checking Bun installation..."
if command -v bun &> /dev/null; then
    BUN_VERSION=$(bun --version)
    echo "   ✅ Bun is installed (version $BUN_VERSION)"
else
    echo "   ❌ Bun is not installed"
    echo ""
    echo "   Installing Bun..."
    curl -fsSL https://bun.sh/install | bash

    # Source shell config to get bun in PATH
    if [ -f "$HOME/.bashrc" ]; then
        source "$HOME/.bashrc"
    elif [ -f "$HOME/.zshrc" ]; then
        source "$HOME/.zshrc"
    fi

    echo "   ✅ Bun installed successfully"
fi

echo ""

# Install npm dependencies
echo "2️⃣  Installing dependencies..."
bun install
echo "   ✅ Dependencies installed"
echo ""

# Install Playwright browsers
echo "3️⃣  Installing Playwright browsers..."
bunx playwright install chromium
echo "   ✅ Playwright chromium installed"
echo ""

# Create directories
echo "4️⃣  Creating directories..."
mkdir -p screenshots
mkdir -p screenshots/comprehensive
mkdir -p screenshots/visual-regression
echo "   ✅ Directories created"
echo ""

# Verify TypeScript can import browser module
echo "5️⃣  Verifying TypeScript setup..."
if bun run -e "import { PlaywrightBrowser } from './src/browser'; console.log('TypeScript import successful')" &> /dev/null; then
    echo "   ✅ TypeScript setup verified"
else
    echo "   ❌ TypeScript import failed"
    exit 1
fi

echo ""
echo "======================================================"
echo "✅ Browser Test Suite setup complete!"
echo "======================================================"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Start your Image Hosting App backend:"
echo "   cd ../backend"
echo "   uv run uvicorn app.main:app --reload"
echo ""
echo "2. Run verification (in another terminal):"
echo "   cd browser-tests"
echo "   bun run tools/gallery-test.ts verify-home"
echo ""
echo "3. Run smoke tests:"
echo "   bun run examples/smoke-test.ts"
echo ""
echo "4. See README.md for more usage examples"
echo ""
echo "📚 Documentation:"
echo "   - README.md - Complete usage guide"
echo "   - VERIFY.md - Full verification checklist"
echo ""
