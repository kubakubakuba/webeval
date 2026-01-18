#!/bin/bash
#
# Initialize .docker directories with templates and tasks
# Run this script before starting Docker containers
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "Initializing .docker directories..."

# Create .docker directories
mkdir -p "$PROJECT_ROOT/.docker/S_templates"
mkdir -p "$PROJECT_ROOT/.docker/tasks"

# Copy templates
if [ -d "$PROJECT_ROOT/web/S_templates" ]; then
    echo "Copying template files..."
    cp -r "$PROJECT_ROOT/web/S_templates/"* "$PROJECT_ROOT/.docker/S_templates/" 2>/dev/null || true
    echo "Template files copied to .docker/S_templates/"
else
    echo "Warning: web/S_templates directory not found"
fi

# Copy tasks
if [ -d "$PROJECT_ROOT/web/tasks" ]; then
    echo "Copying task files..."
    cp -r "$PROJECT_ROOT/web/tasks/"* "$PROJECT_ROOT/.docker/tasks/" 2>/dev/null || true
    echo "Task files copied to .docker/tasks/"
else
    echo "Warning: web/tasks directory not found"
fi

echo ""
echo "Initialization complete!"
echo ""
echo "Directory structure:"
echo "  .docker/"
echo "    ├── S_templates/ ($(ls -1 "$PROJECT_ROOT/.docker/S_templates" 2>/dev/null | wc -l) files)"
echo "    └── tasks/       ($(ls -1 "$PROJECT_ROOT/.docker/tasks" 2>/dev/null | wc -l) files)"
echo ""
echo "Next steps:"
echo "  1. Review and configure scripts/docker/variables.env"
echo "  2. Run: cd scripts/docker && docker-compose up -d"
