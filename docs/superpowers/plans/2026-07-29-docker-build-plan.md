# Docker Multi-Stage Build Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the existing single-stage Dockerfile with a multi-stage build that produces a smaller `games:latest` image.

**Architecture:** Two-stage Dockerfile – a builder stage that installs Python dependencies, and a runtime stage that copies only the installed packages and source code. Build with `docker build -t games:latest .`.

**Tech Stack:** Docker, Python 3.11-slim, FastAPI/Uvicorn.

## Global Constraints
- Tag must be `games:latest`.
- Use the existing `python:3.11-slim` base image for both stages.
- Keep the same runtime command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- No additional OS packages unless required by dependencies.

---

### Task 1: Update Dockerfile to multi-stage

**Files:**
- Modify: `Dockerfile`

**Interfaces:**
- Produces: Updated Dockerfile that builds a multi-stage image.

- [ ] **Step 1: Backup current Dockerfile**
```bash
cp Dockerfile Dockerfile.backup
```

- [ ] **Step 2: Write new multi-stage Dockerfile**
```dockerfile
# ---------- Builder stage ----------
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build-time dependencies
COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# ---------- Runtime stage ----------
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed packages and source from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /app /app

EXPOSE 8000

# Run the FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 3: Verify Dockerfile syntax**
```bash
docker build --no-cache -t games:test-syntax .
```
Expected: Build succeeds without errors.

- [ ] **Step 4: Test that the image runs**
```bash
docker run --rm -d --name test-games -p 8000:8000 games:test-syntax
sleep 5
curl -f http://localhost:8000/health || curl -f http://localhost:8000/
docker stop test-games
```
Expected: Container starts and responds to HTTP requests.

- [ ] **Step 5: Tag as latest and clean up**
```bash
docker tag games:test-syntax games:latest
docker rmi games:test-syntax
docker rmi $(docker images -f "dangling=true" -q) 2>/dev/null || true
```

- [ ] **Step 6: Commit**
```bash
git add Dockerfile
git commit -m "feat: multi-stage Docker build for games image"
```

---

### Task 2: Verify image size reduction

**Files:**
- None (verification only)

**Interfaces:**
- Consumes: The `games:latest` image from Task 1.

- [ ] **Step 1: Check image size**
```bash
docker images games:latest --format "{{.Size}}"
```
Expected: Size significantly smaller than the original single-stage image (should be ~30% reduction).

- [ ] **Step 2: Compare with backup (optional)**
```bash
docker build -t games:single-stage -f Dockerfile.backup .
docker images games:single-stage games:latest --format "{{.Repository}}:{{.Tag}} {{.Size}}"
```

- [ ] **Step 3: Document size comparison** (optional, for reference)

---

### Task 3: Update documentation

**Files:**
- Modify: `README.md` (if it contains Docker build instructions)

**Interfaces:**
- Produces: Updated README with new build command.

- [ ] **Step 1: Check README for Docker instructions**
```bash
grep -n -i docker README.md
```

- [ ] **Step 2: Update build command if present**
```bash
# If README has docker build instructions, update to:
# docker build -t games:latest .
```

- [ ] **Step 3: Commit**
```bash
git add README.md
git commit -m "docs: update Docker build instructions"
```

---

**Plan complete and saved to `docs/superpowers/plans/2026-07-29-docker-build-plan.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**