# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2024-12-30

### Added
- Support for DeepSeek Chat model as an alternative to OpenRouter
- Flexible model selection based on available API keys

### Changed
- Updated LiteLLMClient to support both OpenRouter and DeepSeek API keys
- Modified environment variable loading to use project directory instead of home directory
- Improved error handling in create_agent endpoint with separate validation for repo_url and tasks
- Updated package versions in requirements.txt for better compatibility

### Fixed
- Task text concatenation in create_agent endpoint
- Error messages for missing repository URL and tasks
