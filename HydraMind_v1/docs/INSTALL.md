# Installation Guide

This guide provides comprehensive installation instructions for HydraMind v1 across different platforms and deployment scenarios.

---

## 📋 System Requirements

### Minimum Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Linux/macOS/Windows | Linux (Ubuntu 20.04+) |
| **CPU** | 2 cores | 4+ cores |
| **RAM** | 4 GB | 8+ GB |
| **Disk** | 2 GB free | 10+ GB free |
| **Python** | 3.10+ | 3.11+ |

### Supported Platforms

- **Linux** - Ubuntu 20.04+, CentOS 8+, Debian 11+
- **macOS** - macOS 12.0+ (Monterey and later)
- **Windows** - Windows 10/11 with WSL2
- **Docker** - Official Docker images available
- **Raspberry Pi** - Raspberry Pi 4+ with 4GB+ RAM

---

## 📦 Core Dependencies

- **Python 3.10+** (Required)
- **psutil** - System monitoring
- **numpy** - Numerical operations
- **SQLAlchemy** - Database ORM
- **pandas** - Data processing
- **PyYAML** - Configuration

**Optional Dependencies:**
- **fastapi + uvicorn** - FastAPI Control Plane API
- **scipy, scikit-learn** - Advanced analytics

---

## 🚀 Quick Installation

### Option 1: PyPI (Recommended)

```bash
# Install from PyPI
pip install hydramind

# Verify installation
python -c "import hydramind; print('HydraMind installed successfully')"
```

### Option 2: From Source

```bash
# Clone the repository
git clone https://github.com/hydramind/hydramind-v1.git
cd hydramind-v1

# Install in development mode
pip install -e .

# Or install for production
pip install .
```

### Option 3: Docker

```bash
# Pull the official image
docker pull hydramind/hydramind:v1.0.0

# Run with default configuration
docker run -p 8765:8765 hydramind/hydramind:v1.0.0

# Or run with custom configuration
docker run -v $(pwd)/config.yaml:/app/hydramind.yaml hydramind/hydramind:v1.0.0
```

---

## 📦 Detailed Installation

### Step 1: Python Environment

#### Using venv (Recommended)

```bash
# Create virtual environment
python -m venv hydramind-env

# Activate on Linux/macOS
source hydramind-env/bin/activate

# Activate on Windows
hydramind-env\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

#### Using conda

```bash
# Create conda environment
conda create -n hydramind python=3.11
conda activate hydramind

# Install in conda environment
pip install hydramind
```

### Step 2: Install Dependencies

#### Core Dependencies

```bash
# Install required packages
pip install psutil numpy SQLAlchemy pandas PyYAML

# Optional: Install development dependencies
pip install black flake8 mypy pytest pytest-cov

# Optional: Install FastAPI control plane
pip install fastapi uvicorn

# Optional: Install advanced analytics
pip install scipy scikit-learn
```

#### Verify Installation

```bash
# Test basic import
python -c "import hydramind; print('✓ HydraMind core imported')"

# Test module imports
python -c "from hydramind.modules import get_available_modules; print(f'✓ {len(get_available_modules())} modules available')"

# Test brain creation (without starting)
python -c "
from hydramind.brain import HydraBrain
brain = HydraBrain()
print('✓ HydraMind brain initialized')
brain._initialize_core_components()
print('✓ All core components initialized')
"
```

### Step 3: Configuration

#### Copy Default Configuration

```bash
# Copy the default configuration
cp hydramind.yaml myproject.yaml

# Edit for your needs
nano myproject.yaml  # or use your preferred editor
```

#### Basic Configuration Example

```yaml
# myproject.yaml
server:
  enabled: true
  host: 0.0.0.0
  port: 8765

features:
  seed: true
  replay: true
  anomaly: true
  optimizer: true
  meta_planner: true

# Your custom modules
custom:
  my_module: true
  data_source: /dev/ttyUSB0
```

### Step 4: First Run

```bash
# Run with default configuration
python -m hydramind

# Or run with custom configuration
python -m hydramind --config myproject.yaml

# Run in background for production
nohup python -m hydramind --config production.yaml > hydramind.log 2>&1 &
```

---

## 🐳 Docker Installation

### Using Docker Compose (Recommended)

```yaml
# docker-compose.yml
version: '3.8'
services:
  hydramind:
    image: hydramind/hydramind:v1.0.0
    ports:
      - "8765:8765"
    volumes:
      - ./config.yaml:/app/hydramind.yaml
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - HYDRAMIND_LOGGING_LEVEL=INFO
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8765/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

```bash
# Start with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f hydramind

# Check health
curl http://localhost:8765/health
```

### Manual Docker Commands

```bash
# Build from source
docker build -t hydramind/hydramind:v1.0.0 .

# Run with volume mounts
docker run -d \
  --name hydramind \
  -p 8765:8765 \
  -v $(pwd)/config.yaml:/app/hydramind.yaml \
  -v $(pwd)/data:/app/data \
  hydramind/hydramind:v1.0.0

# Execute commands in container
docker exec -it hydramind python -c "import hydramind; print('Running in Docker')"
```

---

## 🔧 Platform-Specific Installation

### Linux (Ubuntu/Debian)

#### System Dependencies

```bash
# Update package index
sudo apt update

# Install system dependencies
sudo apt install -y python3-dev python3-venv build-essential

# Optional: Install for better performance
sudo apt install -y python3-numpy python3-scipy
```

#### Python Installation

```bash
# Install Python 3.11 (if not already installed)
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Create virtual environment
python3.11 -m venv hydramind-env
source hydramind-env/bin/activate

# Install HydraMind
pip install hydramind
```

### macOS

#### Using Homebrew

```bash
# Install Python (if needed)
brew install python@3.11

# Create virtual environment
python3.11 -m venv hydramind-env
source hydramind-env/bin/activate

# Install HydraMind
pip install hydramind
```

#### Using pyenv

```bash
# Install Python 3.11
pyenv install 3.11.0
pyenv local 3.11.0

# Create virtual environment
python -m venv hydramind-env
source hydramind-env/bin/activate

# Install HydraMind
pip install hydramind
```

### Windows

#### Using WSL2 (Recommended)

```bash
# Install WSL2 and Ubuntu
wsl --install Ubuntu

# In WSL Ubuntu terminal:
sudo apt update
sudo apt install python3.11 python3.11-venv

# Create virtual environment
python3.11 -m venv hydramind-env
source hydramind-env/bin/activate

# Install HydraMind
pip install hydramind
```

#### Native Windows

```powershell
# Install Python 3.11
winget install Python.Python.3.11

# Create virtual environment
python -m venv hydramind-env
hydramind-env\Scripts\activate

# Install HydraMind
pip install hydramind
```

### Raspberry Pi

#### Raspberry Pi 4+ (4GB+ RAM recommended)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install -y python3.11 python3.11-venv python3-dev

# Create virtual environment
python3.11 -m venv hydramind-env
source hydramind-env/bin/activate

# Install HydraMind (may need to build from source for ARM)
pip install hydramind

# Or build from source for better ARM support
git clone https://github.com/hydramind/hydramind-v1.git
cd hydramind-v1
pip install -e .
```

---

## 📦 Advanced Installation Options

### Development Installation

```bash
# Clone repository
git clone https://github.com/hydramind/hydramind-v1.git
cd hydramind-v1

# Install in development mode with all dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
python -m pytest tests/

# Run linting
python -m flake8 hydramind/
python -m mypy hydramind/
```

### Production Installation

#### Using pip

```bash
# Install production dependencies only
pip install hydramind

# For Docker production deployment
docker build -f Dockerfile.prod -t hydramind-prod .
```

#### Using Ansible

```yaml
# ansible/playbook.yml
- name: Install HydraMind
  pip:
    name: hydramind
    virtualenv: /opt/hydramind
    state: present

- name: Configure HydraMind
  template:
    src: hydramind.j2
    dest: /opt/hydramind/hydramind.yaml

- name: Start HydraMind service
  systemd:
    name: hydramind
    state: started
    enabled: yes
```

### Custom Installation Paths

```bash
# Install to custom location
pip install --prefix=/opt/hydramind hydramind

# Add to PATH
export PATH=/opt/hydramind/bin:$PATH

# Configure library path
export LD_LIBRARY_PATH=/opt/hydramind/lib:$LD_LIBRARY_PATH
```

---

## 🔧 Post-Installation Setup

### Step 1: Verify Installation

```bash
# Basic functionality test
python -c "
import hydramind
from hydramind.brain import HydraBrain
brain = HydraBrain()
print('✓ HydraMind installation verified')
"

# Module availability test
python -c "
from hydramind.modules import get_available_modules
modules = get_available_modules()
print(f'✓ {len(modules)} modules available')
"
```

### Step 2: Configure Environment

#### Environment Variables

```bash
# Set environment variables
export HYDRAMIND_LOGGING_LEVEL=INFO
export HYDRAMIND_CONFIG_PATH=/path/to/config.yaml
export HYDRAMIND_DATA_DIR=/path/to/data

# Or create .env file
cat > .env << EOF
HYDRAMIND_LOGGING_LEVEL=INFO
HYDRAMIND_CONFIG_PATH=./config.yaml
HYDRAMIND_DATA_DIR=./data
EOF
```

#### Configuration File

```bash
# Copy and customize configuration
cp hydramind.yaml myconfig.yaml

# Edit configuration
nano myconfig.yaml

# Test configuration
python -m hydramind --config myconfig.yaml --dry-run
```

### Step 3: First Run

```bash
# Start HydraMind
python -m hydramind --config myconfig.yaml

# Check control plane (if enabled)
curl http://localhost:8765/health

# Check logs
tail -f logs/hydramind.log
```

---

## 🛠️ Troubleshooting

### Common Installation Issues

#### Import Errors

```bash
# Problem: Module not found errors
# Solution: Check Python path and virtual environment

# Verify Python environment
which python
python --version

# Check if HydraMind is installed
python -c "import hydramind"

# Check module availability
python -c "from hydramind.modules import get_available_modules"
```

#### Permission Issues

```bash
# Problem: Permission denied for shared memory or files
# Solution: Check permissions and run with appropriate user

# Check shared memory permissions
ls -la /dev/shm/

# Run as appropriate user
sudo -u hydramind python -m hydramind

# Or fix permissions
sudo chmod 666 /dev/shm/hydra_ring
```

#### Dependency Issues

```bash
# Problem: Missing dependencies or version conflicts
# Solution: Update pip and reinstall

# Update pip
pip install --upgrade pip

# Clear pip cache
pip cache purge

# Reinstall with no cache
pip install --no-cache-dir hydramind

# Check for conflicts
pip check
```

### Performance Issues

#### High Memory Usage

```bash
# Problem: Excessive memory consumption
# Solution: Tune configuration

# Reduce ring buffer size
# In hydramind.yaml:
ring_capacity: 8192  # Default: 16384
ring_item_bytes: 1024  # Default: 2048

# Monitor memory usage
python -c "
import psutil
process = psutil.Process()
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB')
"
```

#### Slow Startup

```bash
# Problem: Slow initialization
# Solution: Optimize configuration and dependencies

# Disable unused features
# In hydramind.yaml:
features:
  seed: false
  replay: false
  anomaly: false

# Use production settings
export HYDRAMIND_LOGGING_LEVEL=WARNING
```

### Network Issues

#### Port Conflicts

```bash
# Problem: Port already in use
# Solution: Change default port

# In hydramind.yaml:
server:
  port: 8766  # Change from default 8765

# Or use environment variable
export HYDRAMIND_SERVER_PORT=8766
```

#### Firewall Issues

```bash
# Problem: Cannot access control plane
# Solution: Check firewall and network configuration

# Check if port is open
netstat -tlnp | grep 8765

# Open firewall port (Linux)
sudo ufw allow 8765

# Open firewall port (macOS)
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /Applications/HydraMind.app/Contents/MacOS/HydraMind
```

---

## 🔄 Upgrading HydraMind

### From Previous Versions

```bash
# Backup current configuration
cp hydramind.yaml hydramind.yaml.backup

# Update HydraMind
pip install --upgrade hydramind

# Or update from source
cd hydramind-v1
git pull origin main
pip install -e .

# Test upgrade
python -c "import hydramind; print('✓ Upgrade successful')"
```

### Version Compatibility

| From Version | To Version | Migration Required |
|--------------|------------|-------------------|
| **< 1.0.0** | **1.0.0** | ✅ Full reinstall recommended |
| **1.0.0** | **1.0.x** | ✅ Configuration review needed |
| **1.0.x** | **1.1.0** | ⚠️ Check changelog for breaking changes |

### Backup and Recovery

#### Pre-Upgrade Backup

```bash
# Backup configuration and data
cp hydramind.yaml hydramind.yaml.backup
cp -r data/ data.backup.$(date +%Y%m%d_%H%M%S)
cp -r logs/ logs.backup.$(date +%Y%m%d_%H%M%S)

# Backup database
cp brain_events.sqlite brain_events.sqlite.backup
```

#### Post-Upgrade Validation

```bash
# Test basic functionality
python -c "
import hydramind
from hydramind.brain import HydraBrain
brain = HydraBrain()
print('✓ Post-upgrade validation passed')
"

# Test configuration loading
python -m hydramind --config hydramind.yaml --dry-run

# Check module availability
python -c "from hydramind.modules import get_available_modules; print(f'✓ {len(get_available_modules())} modules loaded')"
```

---

## 🧪 Testing Installation

### Automated Tests

```bash
# Run full test suite
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
python -m pytest tests/performance/ -v

# Run with coverage
python -m pytest --cov=hydramind tests/
```

### Manual Verification

#### Basic Functionality

```bash
# Test 1: Import test
python -c "import hydramind; print('✓ Import successful')"

# Test 2: Brain creation
python -c "
from hydramind.brain import HydraBrain
brain = HydraBrain()
print('✓ Brain creation successful')
"

# Test 3: Module loading
python -c "
from hydramind.modules import get_available_modules
modules = get_available_modules()
print(f'✓ {len(modules)} modules loaded: {modules[:3]}...')
"

# Test 4: Configuration loading
python -c "
from hydramind.core.config import load_config
config = load_config('hydramind.yaml')
print(f'✓ Configuration loaded: {len(config.__dict__)} settings')
"
```

#### Performance Verification

```bash
# Test 5: Performance benchmarks
python -c "
import time
from hydramind.brain import HydraBrain

start = time.time()
brain = HydraBrain()
init_time = time.time() - start
print(f'✓ Initialization time: {init_time:.2f}s')

# Test event processing speed
start = time.time()
# Send test events...
process_time = time.time() - start
print(f'✓ Processing time: {process_time:.3f}s')
"
```

---

## 📚 Additional Resources

### Documentation Links
- **[README.md](README.md)** - Project overview and quick start
- **[GETTING_STARTED.md](GETTING_STARTED.md)** - 10-minute tutorial
- **[CONFIGURATION.md](CONFIGURATION.md)** - Detailed configuration options
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions

### Community Support
- **[GitHub Issues](https://github.com/hydramind/hydramind-v1/issues)** - Bug reports and feature requests
- **[GitHub Discussions](https://github.com/hydramind/hydramind-v1/discussions)** - Questions and community discussion
- **[Discord Community](https://discord.gg/hydramind)** - Real-time chat and support

### Professional Support
- **Enterprise Support** - Dedicated support for commercial customers
- **Consulting Services** - Custom development and deployment assistance
- **Training Programs** - Hands-on workshops and certification

---

## 🔄 Version Information

**Current Version:** 1.0.0
**Release Date:** 2024-01-01
**Python Compatibility:** 3.10+

**Installation completed successfully!** 🎉

Ready to build intelligent systems with HydraMind!
