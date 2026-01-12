# Chitram Blog - Developer Learnings

Technical blog posts documenting the journey of building Chitram, an image hosting application with distributed systems principles.

## Purpose

This blog serves as:
- **Learning Documentation** - Capture lessons learned during development
- **Knowledge Sharing** - Help other developers avoid common pitfalls
- **Portfolio Showcase** - Demonstrate problem-solving and architectural thinking
- **Reference Material** - Quick lookups for specific technical decisions

## Target Audience

- Backend developers learning distributed systems
- Engineers implementing async background jobs
- Developers debugging production deployments
- Anyone building FastAPI applications

## Blog Structure

```
blog/
├── README.md           # This file
├── TEMPLATE.md         # Blog post template
├── 2026/              # Posts by year
│   ├── 01-phase6-deployment-debugging.md
│   └── 02-storage-factory-pattern.md
└── drafts/            # Work in progress
    └── ...
```

## Published Posts

### 2026

1. **[Debugging Cascading Infrastructure Failures: A Phase 6 Deployment Story](2026/01-phase6-deployment-debugging.md)**
   - *January 12, 2026*
   - Tags: #deployment #debugging #celery #redis #infrastructure
   - 5 cascading bugs from Celery deployment, systematic debugging approach

2. **[The Storage Factory Pattern: How Code Duplication Caused a Production Bug](2026/02-storage-factory-pattern.md)**
   - *January 12, 2026*
   - Tags: #design-patterns #dry-principle #refactoring #production-bugs
   - Storage backend mismatch between app and worker, factory pattern fix

## Writing Guidelines

### Post Format

- **Title:** Clear, descriptive, SEO-friendly
- **Date:** Publication date
- **Tags:** 3-5 relevant tags
- **Reading Time:** Estimate (5-10 min typical)
- **Target Audience:** Who should read this
- **Prerequisites:** What readers should know

### Content Structure

1. **Hook** - Start with the problem or interesting finding
2. **Context** - Briefly explain the project/architecture
3. **Problem** - Deep dive into the issue
4. **Solution** - How it was solved
5. **Lessons Learned** - Key takeaways
6. **Code Examples** - Working snippets with explanations
7. **Conclusion** - Summary and next steps

### Writing Style

- ✅ **DO:** Use first-person narrative ("I found...", "We debugged...")
- ✅ **DO:** Include actual error messages and logs
- ✅ **DO:** Show code before/after comparisons
- ✅ **DO:** Link to related docs, PRs, and commits
- ✅ **DO:** Include diagrams for complex architecture
- ❌ **DON'T:** Include sensitive information (keys, passwords, IPs)
- ❌ **DON'T:** Use jargon without explanation
- ❌ **DON'T:** Make it sound like a changelog (be narrative)

### Publishing Process

1. **Draft** - Start in `drafts/` folder
2. **Review** - Self-review for clarity and accuracy
3. **Sanitize** - Remove any sensitive information
4. **Publish** - Move to `YYYY/` folder with sequential number
5. **Update Index** - Add to this README
6. **Share** - Post on dev.to, Medium, Twitter, etc.

## Topics for Future Posts

### Planned

- [ ] Authentication Provider Pattern: Supabase Integration
- [ ] Test Dependency Container Pattern (ADR-0014)
- [ ] From 11 to 355 Tests: Growing Test Suite Sustainably
- [ ] Web UI with HTMX: Modern Without the JavaScript Fatigue
- [ ] Pluggable AI Providers: OpenAI + Fallback Chain

### Ideas

- [ ] GitHub Codespaces vs Local Docker: 8GB RAM Constraint
- [ ] MinIO vs S3: S3-Compatible Object Storage
- [ ] Pre-commit Hooks: Catching Issues Before CI
- [ ] CD Pipeline: Zero-Downtime Deployments with Docker Compose
- [ ] Cost Optimization: OpenAI gpt-4o-mini at $0.0001658/image

## Promotion Channels

### Primary
- **dev.to** - Developer community
- **Medium** - Tech writing platform
- **Personal blog** - Canonical source

### Secondary
- **Twitter/X** - Quick threads with highlights
- **LinkedIn** - Professional network
- **Reddit** - r/programming, r/Python, r/FastAPI
- **Hacker News** - If particularly insightful

## Analytics & Feedback

Track engagement to improve future posts:
- Views and read time
- Comments and questions
- Social media shares
- GitHub stars/forks (if applicable)

## License

All blog posts are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) - feel free to share with attribution.

---

**Author:** [@abhi10](https://github.com/abhi10)
**Project:** [Chitram](https://github.com/abhi10/chitram)
**Contact:** Open GitHub issues for questions or corrections
