# 📚 Documentation Index - Aletheia Deep Research

Welcome to the Aletheia Deep Research documentation center. This directory contains all project documentation, guides, and reference materials.

## 📁 Directory Structure

### 📖 Guides (`/guides/`)
Comprehensive guides for using and understanding Aletheia:

- **[CI/CD_GUIDE.md](./guides/CI_CD_GUIDE.md)** - Complete CI/CD pipeline documentation
  - GitHub Actions workflows
  - Multi-environment deployment
  - Security and compliance features
  - Troubleshooting guide

### 🗺️ Roadmaps (`/roadmaps/`)
Project planning and future development roadmaps:

- **[TESTING_ROADMAP.md](./roadmaps/TESTING_ROADMAP.md)** - Testing coverage improvement plan
  - Coverage gap analysis
  - Implementation phases
  - Test strategy recommendations

- **[STATUS_REPORT.md](./roadmaps/STATUS_REPORT.md)** - Historical project status reports
  - Development milestones
  - Achievement tracking
  - Performance metrics

- **[performance_report.md](./roadmaps/performance_report.md)** - Performance benchmarking results
  - API response times
  - Load testing results
  - Optimization recommendations

### 🔌 API Documentation (`/api/`)
Documentación completa de la API REST:

- **[API README.md](./api/README.md)** - Documentación completa de la API v0.7.0
  - Endpoints y modelos de datos
  - Ejemplos de uso y configuración
  - Métricas de rendimiento y seguridad
  
- **[openapi.json](./api/openapi.json)** - Especificación OpenAPI en formato JSON
- **[openapi.yaml](./api/openapi.yaml)** - Especificación OpenAPI en formato YAML

### 🏗️ Architecture (`/architecture/`)
Technical architecture documentation and design decisions:

*Note: Architecture documentation to be added as system evolves*

### 🧪 Testing (`/testing/`)
Testing artifacts, reports, and coverage data:

- **coverage.xml** - Latest test coverage report
- **htmlcov/** - HTML coverage report (viewable in browser)
- **performance_results.json** - Latest performance test results

### 📝 Project Files (`/`)
General project documentation and notes:

- **Description.txt** - Project description and overview
- **daily.txt** - Development notes and daily logs
- **debugging.txt** - Debugging sessions and issue resolution

## 🚀 Quick Start Guide

### For Developers
1. Start with the main [README.md](../README.md) for project overview
2. Review [API Documentation](./api/README.md) for endpoints and integration
3. Check [CI/CD_GUIDE.md](./guides/CI_CD_GUIDE.md) for deployment processes
4. Review [TESTING_ROADMAP.md](./roadmaps/TESTING_ROADMAP.md) for testing strategy

### For DevOps Engineers
1. Focus on [CI/CD_GUIDE.md](./guides/CI_CD_GUIDE.md) for pipeline setup
2. Review Kubernetes configurations in `/infra/k8s/`
3. Check deployment scripts in `/scripts/deployment/`

### For QA Engineers
1. Review [TESTING_ROADMAP.md](./roadmaps/TESTING_ROADMAP.md) for testing strategy
2. Check `/testing/` directory for coverage reports
3. Review benchmark tools in `/tools/benchmarks/`

### For Project Managers
1. Check [STATUS_REPORT.md](./roadmaps/STATUS_REPORT.md) for progress tracking
2. Review main [README.md](../README.md) for feature completeness
3. Check `plan.yaml` in project root for detailed roadmap

## 📊 Documentation Standards

All documentation in this project follows these standards:

- **Markdown Format**: All docs use GitHub-flavored Markdown
- **Mermaid Diagrams**: Complex flows use Mermaid for visualization
- **Code Examples**: Practical examples with syntax highlighting
- **Table of Contents**: Long documents include navigation
- **Status Badges**: Clear indication of implementation status

## 🔄 Maintenance

This documentation is maintained alongside the codebase and updated with each release:

- **v0.7.0**: Added comprehensive CI/CD documentation
- **v0.6.1**: Added testing roadmap and coverage analysis
- **v0.6.0**: Initial documentation structure

## 🤝 Contributing

When adding new documentation:

1. Place files in the appropriate subdirectory
2. Update this index file
3. Follow existing formatting standards
4. Include practical examples where relevant
5. Add cross-references to related documentation

---

**📍 Current Version**: v0.7.0 ENTERPRISE-READY CI/CD COMPLETE  
**📅 Last Updated**: September 12, 2025  
**👥 Maintained by**: Aletheia Development Team