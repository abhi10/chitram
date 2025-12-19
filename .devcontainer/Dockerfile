FROM python:3.12-slim-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv (fast Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Create non-root user
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && mkdir -p /home/$USERNAME/.local/bin \
    && chown -R $USERNAME:$USERNAME /home/$USERNAME

# Install uv for non-root user
USER $USERNAME
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/home/$USERNAME/.local/bin:$PATH"

WORKDIR /workspaces/image-hosting-app
