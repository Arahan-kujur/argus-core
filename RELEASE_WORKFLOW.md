# Release Workflow

This repository uses GitHub Actions to automatically create releases when version tags are pushed.

## How It Works

The workflow (`.github/workflows/release.yml`) triggers automatically when you push a tag matching the pattern `v*` (e.g., `v0.1.0`, `v1.2.3`).

## How to Trigger a Release

1. **Create and push a version tag:**
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

2. **The workflow will automatically:**
   - Check out the repository
   - Set up Python 3.10
   - Install build tools
   - Run a sanity check (imports argus)
   - Build the package (creates wheel and source distribution)
   - Create a GitHub Release with the tag name
   - Attach build artifacts to the release

## What Gets Attached

The following files are automatically attached to the GitHub Release:

- `dist/*.whl` - Python wheel distribution
- `dist/*.tar.gz` - Source distribution (sdist)

These are the standard Python package distribution formats that can be installed via `pip`.

## How to Verify It Worked

1. **Check GitHub Actions:**
   - Go to the "Actions" tab in your GitHub repository
   - Look for a workflow run with your tag name
   - Verify it completed successfully (green checkmark)

2. **Check Releases:**
   - Go to the "Releases" section in your GitHub repository
   - You should see a new release with your tag name
   - The release should have both `.whl` and `.tar.gz` files attached

3. **Test Installation:**
   ```bash
   # Install from the wheel
   pip install https://github.com/yourusername/argus-core/releases/download/v0.1.0/argus_core-0.1.0-py3-none-any.whl
   
   # Or from source
   pip install https://github.com/yourusername/argus-core/releases/download/v0.1.0/argus-core-0.1.0.tar.gz
   ```

## Workflow Details

The workflow performs these steps:

1. **Checkout** - Gets the repository code
2. **Setup Python** - Installs Python 3.10
3. **Install build tools** - Installs `build`, `setuptools`, `wheel`
4. **Sanity check** - Verifies `import argus` works
5. **Build package** - Creates distribution files using `python -m build`
6. **Create release** - Uses GitHub CLI to create release and attach artifacts

## Requirements

- The repository must have a `pyproject.toml` file (already included)
- Tags must follow the `v*` pattern (e.g., `v0.1.0`, not `0.1.0`)
- The workflow uses the built-in `GITHUB_TOKEN` (no additional secrets needed)

## Notes

- This workflow does NOT publish to PyPI
- This workflow does NOT run tests (add separately if needed)
- The workflow is minimal and focused on creating releases with build artifacts
- Build artifacts are suitable for manual installation or future PyPI publishing
