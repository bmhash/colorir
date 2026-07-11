# Multi-stage build for minimal image size
# Stage 1: Build wheel + install all deps
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build backend
RUN pip install --no-cache-dir hatchling

# Copy project files needed for wheel build
COPY pyproject.toml ./
COPY coloured_drawings/ coloured_drawings/

# Build wheel
RUN python -m hatchling build -t wheel

# Install everything (wheel + deps) into a clean prefix
RUN pip install --no-cache-dir --prefix=/install dist/*.whl

# Stage 2: Minimal runtime image
FROM python:3.12-slim

# System deps for OpenCV-headless + fonts for PDF title rendering
# Note: opencv-python-headless doesn't need libGL, only libglib2.0
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user (uid 1000 matches most host users for volume mounts)
RUN groupadd -g 1000 colorir && useradd -u 1000 -g 1000 -d /app colorir

# Copy installed Python packages (includes our package + all deps)
COPY --from=builder /install /usr/local

# Output directory (mount point for users)
WORKDIR /app
RUN mkdir -p /app/output && chown -R colorir:colorir /app
VOLUME ["/app/output"]

# Switch to non-root user
USER colorir

# Default env
ENV COLORIR_OUTPUT_DIR=/app/output

ENTRYPOINT ["colorir"]
CMD ["--help"]
