# Changelog

## [0.3.0] - 2025-01-14

### Added
- New `wait()` method for waiting for command completion with optional timeout
  - `wait()` - Wait indefinitely until command completes
  - `wait(seconds)` - Wait up to specified seconds for command completion
  - Returns `True` if command completed, `False` if timeout occurred
- Enhanced examples demonstrating the new `wait()` method
- Improved documentation with comprehensive API coverage

### Changed
- Updated README with `wait()` method documentation and examples
- Improved feature descriptions to highlight flexible waiting capabilities

## [0.2.0] - Previous Release

### Features
- Non-blocking command execution
- Persistent shell sessions
- Real-time output streaming
- Interactive program support
- Process control with `stop()` method
- Blocking mode support with `setblocking()`