# Contributing to Authority Boundary Ledger

Thank you for your interest in contributing! This is a reference implementation of a governance primitive, and we welcome improvements.

## What We're Looking For

### High-Priority Contributions

- **Additional boundary types** (NO_INTERNET_ACCESS, NO_FILE_SYSTEM, etc.)
- **Persistence layers** (SQLite, PostgreSQL, Redis implementations)
- **Language bindings** (TypeScript, Go, Rust)
- **Integration examples** (LangChain, LlamaIndex, other frameworks)
- **Better verification strategies** (AST parsing, regex-based checks)
- **Performance optimizations**

### Medium-Priority Contributions

- **Documentation improvements** (tutorials, guides, architecture docs)
- **Additional demos** (more use cases, video tutorials)
- **Test coverage** (unit tests, integration tests)
- **Error handling improvements**

### Out of Scope

- **Production deployment infrastructure** - This is a reference implementation, not production-ready code
- **Complete safety system** - This is a governance primitive, not a comprehensive safety solution
- **Complex ML-based verification** - Keep it simple and deterministic

## How to Contribute

### 1. Fork and Clone

```bash
git clone https://github.com/rosetta-labs-erb/authority-boundary-ledger.git
cd authority-boundary-ledger
```

### 2. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 3. Make Your Changes

- Follow existing code style (simple, readable Python)
- Keep the architecture clean (separate concerns)
- Add docstrings to new functions
- Test your changes locally

### 4. Submit a Pull Request

- Describe what your PR does and why
- Reference any related issues
- Include examples of how to use new features
- Update documentation if needed

## Code Style

This project prioritizes **readability over cleverness**:

- Clear variable names over abbreviations
- Explicit logic over implicit magic
- Simple Python over advanced features
- Comments explaining *why*, not *what*

## Testing

Currently, testing is manual via demos. If you add functionality:

1. Create a demo showing it works
2. Document expected behavior
3. Show failure modes

Automated testing contributions welcome!

## Architecture Principles

1. **Governance, not safety** - This provides control primitives, not content filtering
2. **Explicit state** - Boundaries are first-class objects with defined lifecycle
3. **Defense-in-depth** - Multiple layers (prompt + verification)
4. **Auditability first** - Every action is logged with context

## Questions?

- Open an issue for discussion
- Tag maintainers for guidance
- Check existing issues/PRs for similar work

## License

By contributing, you agree to license your contributions under the MIT License.

---

Thanks for helping make AI systems more governable!
