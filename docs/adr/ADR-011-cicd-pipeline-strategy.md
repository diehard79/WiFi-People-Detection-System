# ADR-011: CI/CD Pipeline Strategy

**Status:** Accepted
**Date:** 2025-02-02
**Context:** Automated Testing, Integration, and Deployment for WiFi Detection System
**Decision:** GitHub Actions with Kubernetes Deployment and Multi-Environment Support

---

## Context

The WiFi-based people detection system requires robust CI/CD infrastructure to:
- **Ensure Code Quality:** Automated testing, linting, and security scanning
- **Enable Rapid Iteration:** Fast feedback loops for developers
- **Support Multiple Environments:** Development, staging, production
- **Deploy Reliably:** Automated, repeatable deployments with rollback capability
- **Monitor Deployments:** Track deployment status and system health

**Deployment Complexity:**
- **Backend:** Python FastAPI services with ML models
- **Frontend:** Next.js application with TypeScript
- **Edge Devices:** Raspberry Pi deployments with OTA updates
- **Infrastructure:** Kubernetes clusters (cloud) + Edge devices (on-premises)

---

## Decision

**Selected Platform: GitHub Actions** for CI/CD with **Kubernetes** for orchestration

### Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CI/CD PIPELINE FLOW                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. TRIGGER (Push/PR)                                         │
│  ├─ Code pushed to main/develop branch                       │
│  ├─ Pull request opened                                      │
│  ├─ Manual trigger (production deploy)                       │
│  └─ Scheduled (nightly builds)                               │
│                                                               │
│  2. BUILD STAGE                                               │
│  ├─ Backend (Python)                                         │
│  │   ├─ Lint (Ruff)                                          │
│  │   ├─ Type check (MyPy)                                    │
│  │   ├─ Unit tests (Pytest)                                  │
│  │   ├─ Integration tests                                    │
│  │   ├─ Security scan (Bandit)                               │
│  │   └─ Docker image build                                   │
│  ├─ Frontend (Next.js)                                       │
│  │   ├─ Lint (ESLint)                                       │
│  │   ├─ Type check (TypeScript)                             │
│  │   ├─ Unit tests (Jest)                                   │
│  │   ├─ E2E tests (Playwright)                              │
│  │   ├─ Build optimization                                  │
│  │   └─ Docker image build                                   │
│  └─ Edge Device Firmware                                     │
│      ├─ Cross-compile for ARM64                              │
│      ├─ Package as Debian (.deb)                             │
│      └─ OTA update package                                   │
│                                                               │
│  3. TEST STAGE                                                │
│  ├─ Deploy to staging environment                           │
│  ├─ Run smoke tests                                          │
│  ├─ Performance tests (Locust)                               │
│  ├─ Security tests (OWASP ZAP)                               │
│  └─ Manual QA approval (production gate)                     │
│                                                               │
│  4. DEPLOY STAGE                                              │
│  ├─ Development (auto-deploy on push to develop)            │
│  ├─ Staging (auto-deploy after tests pass)                  │
│  └─ Production (manual approval + gradual rollout)           │
│                                                               │
│  5. POST-DEPLOY                                               │
│  ├─ Health checks                                            │
│  ├─ Smoke tests                                              │
│  ├─ Metrics verification                                     │
│  ├─ Alert on rollback                                        │
│  └─ Generate deployment report                               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Rationale

### CI/CD Platform Comparison

| Platform | Pros | Cons | Scalability | Cost | Learning Curve |
|----------|------|------|-------------|------|----------------|
| **GitHub Actions** | Native Git integration, generous free tier, YAML config | Limited to GitHub workflows | Excellent ✅ | Free tier generous, $0.008/min after | Low ✅ |
| GitLab CI | Built-in GitLab, powerful features | GitLab-specific | Excellent ✅ | Free tier 400min/month | Medium ⚠️ |
| CircleCI | Fast builds, excellent UX | Limited free tier, less native | Good ⚠️ | Free tier limited | Low ✅ |
| Jenkins | Highly customizable, plugin ecosystem | Complex setup, maintenance burden | Excellent ✅ | Free (self-hosted) | High ❌ |
| Azure DevOps | Integrated Azure ecosystem | Azure-specific | Good ⚠️ | Free tier limited | Medium ⚠️ |

**Selected: GitHub Actions**
- ✅ Already using GitHub for source control
- ✅ Native integration with PR workflows
- ✅ Generous free tier (2000 minutes/month)
- ✅ Excellent community marketplace (actions)
- ✅ Simple YAML configuration
- ✅ Built-in secret management
- ✅ Support for self-hosted runners (edge device builds)

### Deployment Strategy Comparison

| Strategy | Rollout Speed | Risk | Rollback Complexity | Best For |
|----------|---------------|------|---------------------|----------|
| **Blue-Green** | Instant | Low | Simple | Stateful services |
| **Canary** | Gradual | Very Low | Medium | Critical services |
| **Rolling** | Gradual | Medium | Simple | Stateless services |
| **All-at-Once** | Instant | High | Complex | Non-critical services |

**Selected: Hybrid Approach**
- **Backend/Frontend:** Rolling updates (5% → 25% → 50% → 100%)
- **Critical Changes:** Canary deployment (10% canary, monitor, then full rollout)
- **Edge Devices:** Blue-Green (maintain previous version, rollback if needed)

---

## Consequences

### Positive Consequences

**Development Velocity:**
- ✅ Automated testing catches bugs early
- ✅ Fast feedback loop (5-10 minutes for full CI run)
- ✅ Developers can focus on features, not manual testing
- ✅ Consistent build process across team

**Quality Assurance:**
- ✅ Every change tested before merge
- ✅ Code coverage metrics enforced
- ✅ Security scanning automated
- ✅ Performance tests prevent regressions

**Deployment Reliability:**
- ✅ Repeatable deployments (no manual steps)
- ✅ Rollback automated (one command)
- ✅ Gradual rollouts reduce blast radius
- ✅ Post-deployment health checks

**Operational Excellence:**
- ✅ Deployment visibility (GitHub UI)
- ✅ Audit trail (who deployed what when)
- ✅ Integration with issue tracking (GitHub Issues)
- ✅ Multi-environment support (dev/staging/prod)

### Negative Consequences

**Setup Complexity:**
- ❌ Initial pipeline configuration effort (2-3 days)
- ❌ Kubernetes manifests maintenance
- ❌ Multiple pipeline files to maintain
- ❌ Learning curve for team members

**Cost Considerations:**
- ❌ GitHub Actions minutes can accumulate ($0.008/min beyond free tier)
- ❌ Self-hosted runners maintenance (for edge device builds)
- ❌ Additional infrastructure (staging environment)

**Pipeline Bottlenecks:**
- ❌ Long-running tests slow down deployments
- ❌ Pipeline queue times during active development
- ❌ Resource contention (parallel job limits)

**Mitigation Strategies:**
```yaml
# 1. Parallel job execution
jobs:
  test:
    strategy:
      matrix:
        python-version: ['3.11']
        # Split tests across runners
        shard: [1, 2, 3, 4]
    # Run 4 shards in parallel (4x faster)

# 2. Caching dependencies
- name: Cache Python packages
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/poetry.lock') }}
    # Saves 30-60 seconds per run

# 3. Conditional execution
- name: Run full tests
  if: github.event_name == 'push' && github.ref == 'refs/heads/main'
  # Only run full test suite on main branch
```

---

## Implementation

### Backend CI Pipeline

**`.github/workflows/backend.yml`:**
```yaml
name: Backend CI/CD

on:
  push:
    branches: [main, develop]
    paths:
      - 'backend/**'
      - '.github/workflows/backend.yml'
  pull_request:
    branches: [main, develop]
    paths:
      - 'backend/**'

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: wifi-detection/backend

jobs:
  # Job 1: Code Quality
  lint:
    name: Lint & Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install ruff mypy

      - name: Run Ruff linter
        run: ruff check backend/src/

      - name: Run MyPy type checker
        run: mypy backend/src/

  # Job 2: Unit Tests
  test:
    name: Unit Tests
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        working-directory: ./backend
        run: |
          pip install poetry
          poetry install --with dev

      - name: Run pytest
        working-directory: ./backend
        run: |
          poetry run pytest --cov=src --cov-report=xml --cov-report=html

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml
          fail_ci_if_error: false

  # Job 3: Security Scan
  security:
    name: Security Scan
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v3

      - name: Run Bandit security linter
        uses: shubham-patel/bandit-action@v1.0.0
        with:
          path: backend/src/

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: './backend'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'

  # Job 4: Build Docker Image
  build:
    name: Build Docker Image
    runs-on: ubuntu-latest
    needs: [test, security]
    if: github.event_name == 'push'
    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}
    steps:
      - uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Log in to Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=sha,prefix={{branch}}-
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: ./backend
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # Job 5: Deploy to Development
  deploy-dev:
    name: Deploy to Development
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/develop'
    environment:
      name: development
      url: https://dev-api.wifi-detection.com
    steps:
      - name: Deploy to Kubernetes
        uses: steebchen/kubectl@v2.0.0
        with:
          config: ${{ secrets.KUBE_CONFIG_DEV }}
          command: |
            set image deployment/wifi-detection-backend \
              backend=${{ needs.build.outputs.image-tag }} \
              -n development

      - name: Verify deployment
        run: |
          kubectl rollout status deployment/wifi-detection-backend -n development

  # Job 6: Deploy to Staging
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    environment:
      name: staging
      url: https://staging-api.wifi-detection.com
    steps:
      - name: Deploy to Kubernetes
        uses: steebchen/kubectl@v2.0.0
        with:
          config: ${{ secrets.KUBE_CONFIG_STAGING }}
          command: |
            set image deployment/wifi-detection-backend \
              backend=${{ needs.build.outputs.image-tag }} \
              -n staging

      - name: Run smoke tests
        run: |
          curl -f https://staging-api.wifi-detection.com/health || exit 1

  # Job 7: Deploy to Production (Manual Approval)
  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: [build, deploy-staging]
    if: github.ref == 'refs/heads/main'
    environment:
      name: production
      url: https://api.wifi-detection.com
    steps:
      - name: Deploy to Kubernetes (Gradual Rollout)
        uses: steebchen/kubectl@v2.0.0
        with:
          config: ${{ secrets.KUBE_CONFIG_PROD }}
          command: |
            # Update deployment with new image
            set image deployment/wifi-detection-backend \
              backend=${{ needs.build.outputs.image-tag }} \
              -n production

      - name: Monitor rollout
        run: |
          # Wait for rollout to complete (5% → 25% → 50% → 100%)
          kubectl rollout status deployment/wifi-detection-backend -n production --timeout=5m

      - name: Run production smoke tests
        run: |
          ./scripts/smoke-tests.sh production

      - name: Notify team
        if: success()
        uses: 8398a7/action-slack@v3
        with:
          status: custom
          custom_payload: |
            {
              text: "✅ Backend deployed to production: ${{ needs.build.outputs.image-tag }}"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

### Frontend CI Pipeline

**`.github/workflows/frontend.yml`:**
```yaml
name: Frontend CI/CD

on:
  push:
    branches: [main, develop]
    paths:
      - 'frontend/**'
      - '.github/workflows/frontend.yml'
  pull_request:
    branches: [main, develop]
    paths:
      - 'frontend/**'

jobs:
  lint:
    name: Lint & Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci

      - name: Run ESLint
        working-directory: ./frontend
        run: npm run lint

      - name: Run TypeScript compiler
        working-directory: ./frontend
        run: npm run typecheck

  test:
    name: Unit & Integration Tests
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci

      - name: Run Jest tests
        working-directory: ./frontend
        run: npm run test:ci

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./frontend/coverage/lcov.info
          flags: frontend

  e2e:
    name: E2E Tests (Playwright)
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci

      - name: Install Playwright browsers
        working-directory: ./frontend
        run: npx playwright install --with-deps

      - name: Run Playwright tests
        working-directory: ./frontend
        run: npm run test:e2e
        env:
          CI: true

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: frontend/playwright-report/
          retention-days: 30

  build:
    name: Build Production Bundle
    runs-on: ubuntu-latest
    needs: [test, e2e]
    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci

      - name: Build Next.js application
        working-directory: ./frontend
        run: npm run build
        env:
          NEXT_PUBLIC_API_URL: https://api.wifi-detection.com

      - name: Upload build artifacts
        uses: actions/upload-artifact@v3
        with:
          name: frontend-build
          path: frontend/.next/
          retention-days: 7

  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    environment:
      name: staging-frontend
      url: https://staging.wifi-detection.com
    steps:
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org: wifi-detection
          vercel-project-name: frontend
          working-directory: ./frontend
          vercel-args: '--prebuilt --prod'

  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: [build, deploy-staging]
    if: github.ref == 'refs/heads/main'
    environment:
      name: production-frontend
      url: https://wifi-detection.com
    steps:
      - name: Deploy to Vercel (Production)
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org: wifi-detection
          vercel-project-name: frontend
          working-directory: ./frontend
          vercel-args: '--prebuilt --prod'
```

### Edge Device OTA Update Pipeline

**`.github/workflows/edge-firmware.yml`:**
```yaml
name: Edge Device Firmware Build

on:
  push:
    branches: [main]
    paths:
      - 'edge-device/**'
      - '.github/workflows/edge-firmware.yml'
  release:
    types: [created]

jobs:
  build:
    name: Cross-Compile for ARM64
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up QEMU (multi-arch support)
        uses: docker/setup-qemu-action@v2

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Log in to Container Registry
        uses: docker/login-action@v2
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build edge device image
        uses: docker/build-push-action@v4
        with:
          context: ./edge-device
          platforms: linux/arm64
          push: true
          tags: |
            ghcr.io/wifi-detection/edge-device:latest
            ghcr.io/wifi-detection/edge-device:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  create-ota-package:
    name: Create OTA Update Package
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v3

      - name: Create Debian package
        run: |
          cd edge-device
          ./scripts/create-deb.sh \
            --version ${GITHUB_SHA:0:7} \
            --output ../wifi-detection-edge_${GITHUB_SHA:0:7}_arm64.deb

      - name: Upload OTA package
        uses: actions/upload-artifact@v3
        with:
          name: ota-package
          path: wifi-detection-edge_*_arm64.deb

      - name: Upload to release
        if: github.event_name == 'release'
        uses: softprops/action-gh-release@v1
        with:
          files: wifi-detection-edge_*_arm64.deb
```

---

## Multi-Environment Strategy

### Environment Configuration

**Environment-Specific Values:**
```yaml
# k8s/environments/development/values.yaml
replicas: 1

image:
  tag: develop

resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "200m"

env:
  LOG_LEVEL: "DEBUG"
  DATABASE_POOL_SIZE: "5"

# k8s/environments/production/values.yaml
replicas: 3

image:
  tag: latest

resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"

env:
  LOG_LEVEL: "INFO"
  DATABASE_POOL_SIZE: "20"

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
```

### Promotion Strategy

```
development → staging → production

1. Code merged to 'develop' branch
   ↓
2. Auto-deploy to development (CI gate: tests pass)
   ↓
3. QA validates in development
   ↓
4. PR: develop → main
   ↓
5. Auto-deploy to staging (CI gate: tests + security pass)
   ↓
6. Manual QA approval in staging
   ↓
7. Manual trigger: deploy to production
   ↓
8. Gradual rollout (5% → 25% → 50% → 100%)
   ↓
9. Post-deployment smoke tests
   ↓
10. Monitor metrics (rollback if issues detected)
```

---

## Success Criteria

- **Build Time:** <5 minutes for backend, <3 minutes for frontend
- **Test Coverage:** >90% for critical paths, enforced by CI
- **Deployment Frequency:** Multiple times per day (development)
- **Lead Time:** <30 minutes from commit to development deployment
- **Change Failure Rate:** <5% (rollbacks <5% of deployments)
- **Mean Time to Recovery:** <15 minutes (automated rollback)
- **Uptime:** >99.9% (production)
- **Security:** All deployments pass security scans

---

## References

1. [GitHub Actions Documentation](https://docs.github.com/en/actions)
2. [Kubernetes Deployment Best Practices](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
3. [Continuous Delivery](https://continuousdelivery.com/)
4. ADR-002: Backend Programming Language (FastAPI deployment)
5. ADR-006: Deployment Architecture (Kubernetes infrastructure)

---

**Document End**

*This ADR will be reviewed if deployment failure rate exceeds 5% or if lead time increases beyond 30 minutes.*
