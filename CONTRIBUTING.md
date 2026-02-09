# Contributing to Windows System Cleaner

First off, thank you for considering contributing! It's people like you that make the open-source community such an amazing place.

## 🛠 How to Contribute

### 1. Reporting Bugs
- Use the **Bug Report** template when opening an issue.
- Provide as much detail as possible, including logs and system info.

### 2. Suggesting Enhancements
- Open an issue with the tag `enhancement`.
- Describe the feature and why it would be useful.

### 3. Pull Requests
1. **Fork** the repository.
2. Create a new **branch** (`git checkout -b feature/cool-new-feature`).
3. Follow the **Code Style** (see below).
4. **Test** your changes locally.
5. **Commit** your changes with clear, descriptive messages.
6. **Push** to your branch and open a **Pull Request**.

## 🎨 Code Style & Standards
- **UI:** We use `CustomTkinter`. All new UI elements should follow the "Deep Space" theme (see `self.colors` in `App.__init__`).
- **Engine:** Business logic belongs in `cleaner_engine.py`. Keep it separate from the UI.
- **Performance:** Use `os.scandir` for disk operations. Avoid `os.walk` or `Path.iterdir` for recursive scans.
- **Error Handling:** Avoid `except: pass`. Use `logger.debug` for expected issues (like permission denied) and `logger.error` for actual failures.

## 🧪 Testing Requirements
Before submitting a PR, ensure:
1. The app launches without `TclError`.
2. The scan finishes within a reasonable time (use small project folders for testing).
3. Whitelisted system files are not being detected or deleted.

---
*By contributing, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).*
